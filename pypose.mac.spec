# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['pypose/pypose.py'],
             pathex=['pypose'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Pypose v2',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Pypose v2')

app = BUNDLE(coll,
             name='Pypose.app',
             icon='icon.icns',
             bundle_identifier='com.3wnbr1.pypose',
             info_plist={
                 'NSPrincipleClass': 'NSApplication',
                 'NSAppleScriptEnabled': False,
                 'NSHighResolutionCapable': True,
                 'NSRequiresAquaSystemAppearance': False
             })
