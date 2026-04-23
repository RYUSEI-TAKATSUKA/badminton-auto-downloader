# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the BWF ドロー表 ダウンローダ macOS .app bundle.

Build with:
    pyinstaller bwf-draw-mac.spec --noconfirm

Output:
    dist/BWF Draw.app/   ← drag this to /Applications and distribute as a zip

Architecture: defaults to the host arch. Build on arm64 for Apple Silicon
distribution; build on macos-13 (Intel) for Intel users.
"""

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("playwright")

block_cipher = None

a = Analysis(
    ["bwf_draw_launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BWF Draw",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="BWF Draw",
)

app = BUNDLE(
    coll,
    name="BWF Draw.app",
    icon=None,
    bundle_identifier="com.bwfdraw.app",
    info_plist={
        "CFBundleName": "BWF Draw",
        "CFBundleDisplayName": "BWF Draw",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
    },
)
