# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['PrajnaPlayer_v16.5.2.py'],
    pathex=[],
    binaries=[('/Applications/VLC.app/Contents/MacOS/lib/libvlc.dylib', '.'), ('/Applications/VLC.app/Contents/MacOS/lib/libvlccore.dylib', '.')],
    datas=[('assets', 'assets'), ('/Applications/VLC.app/Contents/MacOS/plugins', 'plugins')],
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
    [],
    exclude_binaries=True,
    name='PrajnaPlayer_v16.5.2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['prajna.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PrajnaPlayer_v16.5.2',
)
app = BUNDLE(
    coll,
    name='PrajnaPlayer_v16.5.2.app',
    icon='prajna.icns',
    bundle_identifier=None,
)
