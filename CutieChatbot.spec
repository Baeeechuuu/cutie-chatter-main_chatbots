# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['cutie.py'],
    pathex=[],
    binaries=[],
    datas=[('ui_chatbot.html', '.'), ('auth.html', '.'), ('cutiechatter_users.db', '.'), ('model_checkpoints', 'model_checkpoints'), ('icons', 'icons'), ('themes', 'themes'), ('background', 'background')],
    hiddenimports=['PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui', 'requests', 'json'],
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
    name='CutieChatbot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
