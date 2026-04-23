from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

from .browser import launch
from .fetcher import CloudflareChallengeError, dismiss_cookie_banner, fetch_event_pdf
from .merger import merge
from .paths import OUTPUT_ROOT, ensure_dirs
from .url import parse

SETUP_LANDING = "https://bwfworldtour.bwfbadminton.com/calendar/"
APP_TITLE = "BWF ドロー表 ダウンローダ"


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("720x520")

        self.log_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self.worker: threading.Thread | None = None

        ensure_dirs()
        self._build_ui()
        self.root.after(100, self._drain_log)

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 6}

        intro = ttk.Label(
            self.root,
            text=(
                "BWF World Tour 大会ページの URL を貼り付けて「ダウンロード」を押してください。\n"
                "5 種目（MS / WS / MD / WD / XD）のドロー表 PDF を取得して 1 ファイルに結合します。"
            ),
            justify="left",
            wraplength=680,
        )
        intro.pack(anchor="w", **pad)

        url_frame = ttk.Frame(self.root)
        url_frame.pack(fill="x", **pad)
        ttk.Label(url_frame, text="大会 URL:").pack(side="left")
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", **pad)
        self.download_btn = ttk.Button(
            btn_frame, text="ダウンロード開始", command=self.on_download
        )
        self.download_btn.pack(side="left")
        self.setup_btn = ttk.Button(
            btn_frame, text="初回セットアップ（最初に一度）", command=self.on_setup
        )
        self.setup_btn.pack(side="left", padx=(8, 0))
        self.open_btn = ttk.Button(
            btn_frame, text="出力フォルダを開く", command=self.on_open_output
        )
        self.open_btn.pack(side="right")

        ttk.Label(self.root, text="ログ:").pack(anchor="w", **pad)
        self.log = scrolledtext.ScrolledText(self.root, height=18, state="disabled")
        self.log.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._log_line(f"出力先: {OUTPUT_ROOT}")
        self._log_line("初回のみ「初回セットアップ」を実行してください。")

    # --- worker plumbing -------------------------------------------------

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.download_btn.configure(state=state)
        self.setup_btn.configure(state=state)
        self.url_entry.configure(state=state)

    def _log_line(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _drain_log(self) -> None:
        try:
            while True:
                kind, payload = self.log_queue.get_nowait()
                if kind == "log":
                    self._log_line(str(payload))
                elif kind == "done":
                    self._set_busy(False)
                    if isinstance(payload, dict) and payload.get("ok"):
                        path = payload.get("path")
                        if path:
                            messagebox.showinfo(
                                APP_TITLE,
                                f"完了しました。\n\n{path}",
                            )
                elif kind == "error":
                    self._set_busy(False)
                    messagebox.showerror(APP_TITLE, str(payload))
        except queue.Empty:
            pass
        self.root.after(100, self._drain_log)

    def _post_log(self, text: str) -> None:
        self.log_queue.put(("log", text))

    def _post_done(self, payload: dict | None = None) -> None:
        self.log_queue.put(("done", payload or {"ok": True}))

    def _post_error(self, msg: str) -> None:
        self.log_queue.put(("error", msg))

    def _start_worker(self, target) -> None:
        if self.worker and self.worker.is_alive():
            return
        self._set_busy(True)
        self.worker = threading.Thread(target=target, daemon=True)
        self.worker.start()

    # --- button handlers -------------------------------------------------

    def on_setup(self) -> None:
        self._post_log("--- 初回セットアップ開始 ---")
        self._post_log("Chrome 窓が開きます。BWF サイトを軽く操作してから窓を閉じてください。")
        self._start_worker(self._run_setup)

    def on_download(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning(APP_TITLE, "大会の URL を貼り付けてください。")
            return
        self._post_log(f"--- ダウンロード開始: {url} ---")
        self._start_worker(lambda: self._run_download(url))

    def on_open_output(self) -> None:
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        _open_in_filemanager(OUTPUT_ROOT)

    # --- worker bodies ---------------------------------------------------

    def _run_setup(self) -> None:
        try:
            with launch(headless=False) as (_, context):
                page = context.new_page()
                page.goto(SETUP_LANDING, wait_until="domcontentloaded", timeout=60000)
                if dismiss_cookie_banner(page):
                    self._post_log("Cookie 同意バナーを自動で閉じました。")
                self._post_log("窓を閉じると完了します…")
                try:
                    page.wait_for_event("close", timeout=0)
                except Exception:
                    pass
            self._post_log("セットアップ完了。Cookie を保存しました。")
            self._post_done({"ok": True})
        except Exception as e:
            self._post_log("エラー: " + repr(e))
            self._post_log(traceback.format_exc())
            self._post_error(f"セットアップに失敗しました:\n{e}")

    def _run_download(self, url: str) -> None:
        try:
            parsed = parse(url)
        except ValueError as e:
            self._post_error(str(e))
            return

        out_dir = OUTPUT_ROOT / parsed.slug
        self._post_log(f"大会: {parsed.slug} (id={parsed.tournament_id})")
        self._post_log(f"出力先: {out_dir}")

        try:
            pdfs: list[Path] = []
            with launch(headless=False) as (_, context):
                for ev, ev_url in parsed.event_urls:
                    self._post_log(f"  [{ev.upper()}] 取得中…")
                    pdf = fetch_event_pdf(context, ev, ev_url, out_dir)
                    self._post_log(f"      保存 {pdf.name} ({pdf.stat().st_size:,} bytes)")
                    pdfs.append(pdf)

            combined = OUTPUT_ROOT / f"{parsed.slug}_combined.pdf"
            merge(pdfs, combined)
            self._post_log(f"結合完了: {combined}")
            self._post_done({"ok": True, "path": str(combined)})
        except CloudflareChallengeError as e:
            self._post_log("Cloudflare チャレンジを検出しました。")
            self._post_error(
                "Cloudflare に止められました。\n「初回セットアップ」をもう一度実行してください。"
            )
        except Exception as e:
            self._post_log("エラー: " + repr(e))
            self._post_log(traceback.format_exc())
            self._post_error(f"ダウンロードに失敗しました:\n{e}")


def _open_in_filemanager(path: Path) -> None:
    import subprocess

    if sys.platform == "win32":
        subprocess.Popen(["explorer", str(path)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
