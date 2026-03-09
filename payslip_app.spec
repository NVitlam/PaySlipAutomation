# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for PayslipApp

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Collect google packages before Analysis
extra_datas = []
extra_binaries = []
extra_hiddenimports = []

for pkg in ['google_auth_oauthlib', 'googleapiclient', 'google.auth']:
    try:
        result = collect_all(pkg)
        if len(result) == 3:
            datas, binaries, hiddenimports = result
        elif len(result) == 2:
            datas, hiddenimports = result
            binaries = []
        else:
            continue
        extra_datas += datas
        extra_binaries += binaries
        extra_hiddenimports += hiddenimports
    except Exception:
        extra_hiddenimports += collect_submodules(pkg)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=extra_binaries,
    datas=extra_datas,
    hiddenimports=[
        'google.auth.transport.requests',
        'google.oauth2.credentials',
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery',
        'googleapiclient._helpers',
        'pypdf',
    ] + extra_hiddenimports,
    hookspath=[],
    hooksconfig={},
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PayslipApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
