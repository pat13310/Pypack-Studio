# -*- mode: python ; coding: utf-8 -*-

# Fichier de spécification PyInstaller pour install_wizard.py

a = Analysis(
    ['install_wizard.py'],
    pathex=[],
    binaries=[],
    datas=[('..\\res\\*', 'res')], # Inclure les ressources
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
    a.zipfiles,
    a.datas, # Inclure les données analysées
    [],
    name='setup', # Nom de l'exécutable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Application GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='..\\res\\pypack.ico' # Icône de l'exécutable
)