# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the ToolSym TCM (analysis) app.

Bundle as a one-folder app (cleanest for users with antivirus):

    pyinstaller installers/toolsym-tcm.spec

Output: dist/toolsym-tcm/toolsym-tcm.exe (Windows) or equivalent.
"""

from __future__ import annotations

import sys
from pathlib import Path

block_cipher = None

REPO_ROOT = Path(SPECPATH).parent.resolve()
ENTRY = str(REPO_ROOT / "apps" / "toolsym_tcm" / "__main__.py")
ICON = str(REPO_ROOT / "toolsym" / "resources" / "app_icon.ico")

# Bundle the JSON spec and any other resources alongside the executable.
datas = [
    (str(REPO_ROOT / "toolsym" / "data"), "toolsym/data"),
    (str(REPO_ROOT / "toolsym" / "resources"), "toolsym/resources"),
    (str(REPO_ROOT / "toolsym" / "widgets" / "theme.qss"), "toolsym/widgets"),
]

a = Analysis(
    [ENTRY],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "scipy.signal",
        "scipy.optimize",
        "scipy.ndimage",
        "PIL.Image",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "matplotlib.tests",
        "PyQt5",
        "PyQt6",
        "tkinter",
        "pyvista",   # excluded from TCM bundle; lives in sim bundle
        "vtk",
        "cadquery",
    ],
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
    name="toolsym-tcm",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX often triggers antivirus
    console=False,
    icon=ICON if Path(ICON).is_file() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="toolsym-tcm",
)
