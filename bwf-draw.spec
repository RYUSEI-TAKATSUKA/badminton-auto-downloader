# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the BWF ドロー表 ダウンローダ Windows GUI build.

Build with:
    pyinstaller bwf-draw.spec --noconfirm

Output:
    dist/BWF Draw/                  (folder bundle)
        BWF Draw.exe
        ...

Distribute by zipping the entire `dist/BWF Draw/` folder.
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
