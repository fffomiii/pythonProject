# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['my_package\\code.py'],
    pathex=[],
    binaries=[],
    datas=[('my_package\\server_settings.json', 'my_package'), ('my_package\\settings.json', 'my_package'), ('my_package\\files.json', 'my_package'), ('my_package\\highlighting_settings.json', 'my_package'), ('my_package\\processing.json', 'my_package')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='code',
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
