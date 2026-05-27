# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the ToolSym Sim (dataset-generation) app.

Bundle as a one-folder app:

    pyinstaller installers/toolsym-sim.spec

This bundle ships the heavy 3D dependencies (pyvista, vtk, cadquery /
OCP) so users don't need a Python install at all.
"""

from __future__ import annotations

from pathlib import Path

block_cipher = None

REPO_ROOT = Path(SPECPATH).parent.resolve()
ENTRY = str(REPO_ROOT / "apps" / "toolsym_sim" / "__main__.py")
ICON = str(REPO_ROOT / "toolsym" / "resources" / "app_icon.ico")

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
        # Heavy 3D — only in the sim bundle.
        "pyvista",
        "vtk",
        "vtkmodules.util.numpy_support",
        "cadquery",
        "OCP",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["matplotlib.tests", "PyQt5", "PyQt6", "tkinter"],
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
    name="toolsym-sim",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    name="toolsym-sim",
)
