from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import (
    BrowserContext,
    Download,
    Page,
    Response,
    TimeoutError as PlaywrightTimeoutError,
)


class CloudflareChallengeError(RuntimeError):
    """Raised when a Cloudflare interactive challenge is shown."""


# Hooks window.print so we can detect a print invocation and call CDP printToPDF instead.
_PRINT_HOOK = """
window.__bwfPrintRequested = false;
const _origPrint = window.print;
window.print = function () { window.__bwfPrintRequested = true; };
"""

# Heuristic selectors for the print/download icon next to the tournament title.
# The page is an SPA so we try multiple shapes — first match wins.
_PRINT_SELECTORS = [
    "button[aria-label*='print' i]",
    "button[aria-label*='download' i]",
    "button[title*='print' i]",
    "button[title*='download' i]",
    "a[aria-label*='print' i]",
    "a[aria-label*='download' i]",
    "a[title*='print' i]",
    "a[title*='download' i]",
    "a[href$='.pdf']",
    # Fallback: the first svg-bearing button in the tournament header strip.
    "header button:has(svg)",
]


def _human_pause(min_s: float = 1.5, max_s: float = 4.0) -> None:
    time.sleep(random.uniform(min_s, max_s))


def _check_cloudflare(page: Page) -> None:
    if page.locator("#challenge-form, #cf-challenge-running").count() > 0:
        raise CloudflareChallengeError(
            "Cloudflare challenge detected. Re-run `bwf-draw setup` and complete the check manually."
        )


# Cookie consent banners — try to dismiss before capturing the bracket.
# Order matters: most specific (BWF uses CookieBot) first, generic last.
_COOKIE_ACCEPT_SELECTORS = [
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
    "#CybotCookiebotDialogBodyButtonAccept",
    "#CybotCookiebotDialogBodyLevelButtonAccept",
    "#onetrust-accept-btn-handler",
    "button#accept-cookies",
    "button[aria-label*='accept' i][aria-label*='cookie' i]",
    "button:has-text('Accept All')",
    "button:has-text('Accept all')",
    "button:has-text('I Accept')",
    "button:has-text('Accept')",
    "button:has-text('同意する')",
    "button:has-text('すべて同意')",
]


def dismiss_cookie_banner(page: Page, timeout_ms: int = 4000) -> bool:
    """Click whichever cookie-accept button shows up first. Returns True if dismissed."""
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        for sel in _COOKIE_ACCEPT_SELECTORS:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    loc.click(timeout=2000)
                    page.wait_for_timeout(400)
                    return True
            except Exception:
                continue
        page.wait_for_timeout(250)
    return False


def _find_print_trigger(page: Page):
    for sel in _PRINT_SELECTORS:
        loc = page.locator(sel).first
        try:
            if loc.count() > 0 and loc.is_visible():
                return loc
        except Exception:
            continue
    return None


def _save_response_pdf(response: Response, dest: Path) -> bool:
    ctype = (response.headers or {}).get("content-type", "")
    if "application/pdf" not in ctype.lower() and not response.url.lower().endswith(".pdf"):
        return False
    try:
        body = response.body()
    except Exception:
        return False
    dest.write_bytes(body)
    return True


def fetch_event_pdf(
    context: BrowserContext,
    event: str,
    url: str,
    out_dir: Path,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{event}.pdf"

    page = context.new_page()
    page.add_init_script(_PRINT_HOOK)

    captured: dict[str, Optional[Path]] = {"path": None}

    # 2) New-tab/popup capture
    def on_popup(popup: Page) -> None:
        try:
            popup.wait_for_load_state("domcontentloaded", timeout=15000)
        except PlaywrightTimeoutError:
            pass
        if popup.url.lower().endswith(".pdf"):
            try:
                resp = popup.context.request.get(popup.url)
                if resp.ok:
                    dest.write_bytes(resp.body())
                    captured["path"] = dest
            except Exception:
                pass
        try:
            popup.close()
        except Exception:
            pass

    context.on("page", on_popup)

    # 1+2 combined: any response with PDF content type for this page
    def on_response(resp: Response) -> None:
        if captured["path"] is not None:
            return
        if _save_response_pdf(resp, dest):
            captured["path"] = dest

    page.on("response", on_response)

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        _check_cloudflare(page)
        dismiss_cookie_banner(page)
        # Let the SPA render the bracket (icons appear after data load).
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            pass
        _human_pause()

        trigger = _find_print_trigger(page)
        if trigger is None:
            # No icon found — fall back to printing the rendered page directly.
            return _printtopdf_fallback(page, dest)

        # Move mouse a little, then click and watch for any of the 3 capture paths.
        box = trigger.bounding_box()
        if box:
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        try:
            with page.expect_download(timeout=8000) as dl_info:
                trigger.click()
            download: Download = dl_info.value
            download.save_as(str(dest))
            captured["path"] = dest
        except PlaywrightTimeoutError:
            # No download fired — popup/response handlers may already have captured.
            pass

        # Give popup/response handlers a moment to settle.
        deadline = time.time() + 8
        while captured["path"] is None and time.time() < deadline:
            page.wait_for_timeout(250)

        if captured["path"] is None:
            # 3) window.print() override path
            requested = False
            try:
                requested = bool(page.evaluate("() => window.__bwfPrintRequested"))
            except Exception:
                requested = False
            if requested:
                return _printtopdf_fallback(page, dest)
            # Last resort: render the page anyway.
            return _printtopdf_fallback(page, dest)

        return dest
    finally:
        try:
            context.remove_listener("page", on_popup)
        except Exception:
            pass
        try:
            page.close()
        except Exception:
            pass


def _printtopdf_fallback(page: Page, dest: Path) -> Path:
    page.emulate_media(media="print")
    pdf_bytes = page.pdf(
        format="A4",
        landscape=False,
        print_background=True,
        margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
    )
    dest.write_bytes(pdf_bytes)
    page.emulate_media(media="screen")
    return dest
