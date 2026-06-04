# -*- mode: python ; coding: utf-8 -*-
# PyInstaller build spec for CVmate. Produces a single-file dist\CVmate.exe.
# Build with:  build.bat   (or:  pyinstaller --clean --noconfirm CVmate.spec)

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []

# Bundle data files, binaries, and submodules for packages PyInstaller's
# default analysis tends to miss (customtkinter assets, the Gemini SDK's
# generated protobufs, grpc's compiled extensions, pdf/font resources).
for _pkg in (
    "customtkinter",
    "google.generativeai",
    "google.ai.generativelanguage",
    "grpc",
    "pdfplumber",
    "pdfminer",
    "reportlab",
):
    try:
        _d, _b, _h = collect_all(_pkg)
        datas += _d
        binaries += _b
        hiddenimports += _h
    except Exception:
        pass

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CVmate",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
