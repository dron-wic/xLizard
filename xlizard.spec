# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: builds dist/xLizard/xLizard.exe (onedir, more reliable on Win10/11)

block_cipher = None

hidden = [
    "xlizard",
    "xlizard.gui",
    "xlizard.xlizard",
    "xlizard.thresholds",
    "xlizard.combined_metrics",
    "xlizard.sourcemonitor_metrics",
    "xlizard.cognitive_complexity",
    "xlizard.xlizard_ext",
    "xlizard.xlizard_ext.htmloutput",
    "xlizard.xlizard_ext.xmloutput",
    "xlizard.xlizard_ext.csvoutput",
    "xlizard.xlizard_ext.checkstyleoutput",
    "xlizard.xlizard_ext.auto_open",
    "xlizard.xlizard_ext.xlizardcognitive",
    "xlizard.xlizard_ext.xlizardnd",
    "xlizard.xlizard_ext.xlizardmccabe",
    "xlizard.xlizard_ext.xlizardmodified",
    "xlizard.xlizard_ext.xlizardnonstrict",
    "xlizard.xlizard_ext.xlizardns",
    "xlizard.xlizard_ext.xlizardgotocount",
    "xlizard.xlizard_ext.xlizardreturncount",
    "xlizard.xlizard_ext.xlizardpathcount",
    "xlizard.xlizard_ext.xlizardio",
    "xlizard.quality_score",
    "xlizard.xlizard_languages",
    "xlizard.xlizard_languages.clike",
    "xlizard.xlizard_languages.code_reader",
    "jinja2",
    "tqdm",
    "pathspec",
]

a = Analysis(
    ["run_xlizard.py"],
    pathex=["."],
    binaries=[],
    datas=[("xlizard.json", ".")],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pandas",
        "numpy",
        "pytest",
        "_pytest",
        "py",
        "PIL",
        "Pillow",
        "openpyxl",
        "lxml",
        "matplotlib",
        "scipy",
        "IPython",
        "notebook",
        "tkinter.test",
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
    name="xLizard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI, no black console window
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
    upx=True,
    upx_exclude=[],
    name="xLizard",
)
