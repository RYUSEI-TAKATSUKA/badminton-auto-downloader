# bwf-draw

BWF World Tour 大会ページの「印刷アイコン」から取得できる PDF を **5 種目（MS / WS / MD / WD / XD）まとめて 1 ファイルに結合**してローカル保存するツール。

CLI 版（macOS / Windows / Linux）と、技術リテラシー不問の **GUI 配布版**（Windows `.exe` / macOS `.app`）の 2 形態。

---

## 仕組み（要点）

- 当該サイト (`bwfworldtour.bwfbadminton.com`) は Cloudflare の bot 検知が強く、ヘッドレスや stealth プラグインだけでは弾かれる（JA3/JA4 まで照合される）
- そこで **インストール済みの Google Chrome バイナリそのもの**を Playwright の `launch_persistent_context(channel="chrome")` で起動 → JA4・User-Agent・Canvas・WebGL・拡張一覧まで“本物の Chrome”として通す
- プロファイルは専用ディレクトリ（開発時は `profile/`、配布版は `%LOCALAPPDATA%\BWF Draw\profile`）を使い回す
- 初回だけ「セットアップ」で 1 度サイトを訪問 → Cloudflare クッキーが残り、以降は自動

---

## 開発者向け（CLI / macOS）

### 必要環境

- Python 3.10+
- Google Chrome がインストール済み

### セットアップ

```bash
cd "/Users/takatsukahikaru/Documents/バドミントン協会/badminton-auto-douwnloader"

python3.13 -m venv .venv
source .venv/bin/activate
pip install -e .

# 専用 Chrome プロファイルを Cloudflare 通過済みにする（初回のみ）
bwf-draw setup
```

### 使い方

```bash
bwf-draw "https://bwfworldtour.bwfbadminton.com/tournament/5227/petronas-malaysia-open-2026/draws/full-draw/md"
# → output/petronas-malaysia-open-2026_combined.pdf
```

---

## 配布版を作る（開発者作業）

エンドユーザはアプリをダブルクリックで使います。配布物は **GitHub Actions で自動ビルド**します。

### 共通の流れ

1. このリポジトリを GitHub にプッシュ（プライベートでも OK）
   ```bash
   git init && git add . && git commit -m "initial"
   gh repo create badminton-auto-douwnloader --private --source=. --push
   ```
2. GitHub の **Actions** タブで対象のワークフローを開く
3. **Run workflow** を押す
4. 5〜10 分待つ → Artifacts に ZIP が出来る
5. ZIP をエンドユーザに配布

### Windows 版

| 項目 | 値 |
|---|---|
| Workflow | `Build Windows .exe` |
| Spec | `bwf-draw.spec` |
| Artifact | `BWF-Draw-windows.zip` |
| 配布先 | Windows 10 / 11 |

> **ローカル Windows でビルドする場合**:
> ```powershell
> python -m venv .venv
> .venv\Scripts\activate
> pip install -e . pyinstaller
> pyinstaller bwf-draw.spec --noconfirm
> # → dist\BWF Draw\ ができる
> ```

### macOS 版

| 項目 | 値 |
|---|---|
| Workflow | `Build macOS .app` |
| Spec | `bwf-draw-mac.spec` |
| Artifact | `BWF-Draw-mac-arm64.zip` (Apple Silicon) / `BWF-Draw-mac-intel.zip` (Intel Mac) |
| 配布先 | macOS 11 (Big Sur) 以降 |

ワークフローは Apple Silicon 用と Intel 用を**並行ビルド**します。配布先の Mac の CPU に合わせた ZIP を渡してください（M1/M2/M3/M4 → arm64、それ以前 → intel）。

> **ローカル Mac でビルドする場合**:
> ```bash
> source .venv/bin/activate
> pip install pyinstaller
> pyinstaller bwf-draw-mac.spec --noconfirm
> # → dist/BWF Draw.app ができる
> # ホストの Mac と同じアーキ向けにしか作れない点に注意
> ```
> 注: Homebrew の Python を使う場合は `brew install python-tk@3.11` などで Tk を入れておく必要があります。

---

## エンドユーザ向け（Windows）

### 同梱ファイル: 「BWF Draw 使い方.txt」に書く内容

```
■ 必要なもの
1. Google Chrome（https://www.google.com/chrome/ から無料インストール）

■ 初回だけ
1. 配布された ZIP を好きな場所に展開（デスクトップでも OK）
2. 「BWF Draw」フォルダを開く
3. 「BWF Draw.exe」をダブルクリック
   → 初回は Windows SmartScreen 警告が出ます。
     「詳細情報」→「実行」 で開いてください
4. 開いたウィンドウで「初回セットアップ（最初に一度）」ボタンを押す
5. Chrome 窓が開きます。BWF サイトのページを 1〜2 回クリックしてから
   Chrome 窓の「×」で閉じる
6. 完了

■ 毎回の使い方
1. 「BWF Draw.exe」をダブルクリック
2. BWF の大会ページ URL をブラウザのアドレスバーからコピー
   例: https://bwfworldtour.bwfbadminton.com/tournament/5227/petronas-malaysia-open-2026/draws/full-draw/md
3. アプリの「大会 URL」欄に貼り付け
4. 「ダウンロード開始」ボタンを押す
5. 自動で Chrome が開いて 5 種目分を取得 → 結合 PDF が出来上がる
6. 完了ダイアログが出たら、「出力フォルダを開く」ボタンで結果を確認
   保存場所: ドキュメント\BWF Draws\<大会名>_combined.pdf

■ うまくいかないとき
- 「Cloudflare に止められました」と出たら → もう一度「初回セットアップ」を実行
- それでもダメ → 配布元に連絡
```

## エンドユーザ向け（macOS）

### 同梱ファイル: 「BWF Draw 使い方.txt」に書く内容

```
■ 必要なもの
1. Google Chrome（https://www.google.com/chrome/ から無料インストール）
2. macOS 11 (Big Sur) 以降

■ 初回だけ
1. 配布された ZIP をダブルクリックで解凍
2. 出てきた「BWF Draw.app」をアプリケーションフォルダにドラッグ
3. アプリケーションフォルダの「BWF Draw」を【右クリック】→「開く」
   ※ ダブルクリックだと「壊れている」「開けません」と出ます。
     必ず右クリック→「開く」→確認ダイアログで「開く」を押してください
   ※ それでも開けない場合は、ターミナル（アプリケーション → ユーティリティ）で:
        xattr -cr "/Applications/BWF Draw.app"
     を実行してから再度ダブルクリック
4. 開いたウィンドウで「初回セットアップ（最初に一度）」ボタンを押す
5. Chrome 窓が開きます。BWF サイトのページを 1〜2 回クリックしてから
   Chrome 窓の「×」で閉じる
6. 完了

■ 毎回の使い方
1. アプリケーションフォルダの「BWF Draw」をダブルクリック
2. BWF の大会ページ URL をブラウザのアドレスバーからコピー
   例: https://bwfworldtour.bwfbadminton.com/tournament/5227/petronas-malaysia-open-2026/draws/full-draw/md
3. アプリの「大会 URL」欄に貼り付け
4. 「ダウンロード開始」ボタンを押す
5. 自動で Chrome が開いて 5 種目分を取得 → 結合 PDF が出来上がる
6. 完了ダイアログが出たら、「出力フォルダを開く」ボタンで結果を確認
   保存場所: 書類（Documents）/BWF Draws/<大会名>_combined.pdf

■ うまくいかないとき
- 「壊れているため開けません」と出る → 上の手順 3 の xattr コマンドを実行
- 「Cloudflare に止められました」と出たら → もう一度「初回セットアップ」を実行
- それでもダメ → 配布元に連絡
```

---

## トラブルシューティング（開発者）

- **Cloudflare challenge detected** → `bwf-draw setup` を再実行
- **Chrome が起動しない** → Google Chrome をインストール、または `playwright install chrome`
- **PDF が 0 バイト/真っ白** → `bwf_draw/fetcher.py:_human_pause()` を長めに調整
- **GitHub Actions ビルドが失敗** → Actions ログを確認。Playwright の collect_all が大きいので 5〜10 分かかります

## 安全運用のコツ

- 1 日に何十回も叩かない（毎週 2〜3 大会の頻度であればまず問題なし）
- ヘッドレスにしない
- `profile/` をリポジトリにコミットしない（`.gitignore` 済み）

## アーキテクチャ

```
bwf_draw/
├── browser.py    # 実 Chrome + 永続プロファイル起動
├── cli.py        # CLI エントリ（bwf-draw コマンド）
├── gui.py        # tkinter GUI エントリ（Windows .exe の中身）
├── fetcher.py    # 印刷アイコンクリック → PDF キャプチャ
├── merger.py     # pypdf で 5 PDF を結合
├── paths.py      # クロスプラットフォームのパス解決
└── url.py        # URL → 5 種目 URL 生成

bwf_draw_launcher.py            # PyInstaller のエントリポイント
bwf-draw.spec                   # Windows .exe ビルド設定
bwf-draw-mac.spec               # macOS .app ビルド設定
.github/workflows/build-windows.yml  # Windows ビルド CI
.github/workflows/build-mac.yml      # macOS arm64+intel 並行ビルド CI
```
