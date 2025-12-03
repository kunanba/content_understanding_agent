# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Content Understanding Agent

block_cipher = None

a = Analysis(
    ['build_desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app.py', '.'),
        ('agent.py', '.'),
        ('function_tools.py', '.'),
        ('validation_tools.py', '.'),
        ('.env', '.'),
    ],
    hiddenimports=[
        'streamlit',
        'streamlit.runtime.scriptrunner.magic_funcs',
        'streamlit.components.v1',
        'azure.ai.projects',
        'azure.ai.agents',
        'azure.identity',
        'azure.storage.blob',
        'azure.ai.inference',
        'altair',
        'pandas',
        'numpy',
        'pillow',
        'watchdog',
        'validators',
    ],
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
    [],
    exclude_binaries=True,
    name='ContentUnderstandingAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Show console for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add your .ico file path here if you have an icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ContentUnderstandingAgent',
)
