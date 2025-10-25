# ICP-Engine

[![Python 3.8+](https://img.shields.io/pypi/v/icp_engine.svg)](https://pypi.org/project/icp_engine/)
[![Downloads](https://static.pepy.tech/badge/icp_engine)](https://pepy.tech/project/icp_engine/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Licence Apache2](https://img.shields.io/badge/License-Apache_2-blue)](https://github.com/Zachanardo/ICP-Engine/blob/main/LICENSE)

Native Python 3.8+ bindings for binary analysis and protection detection engine. ICP Engine is a rebranded and enhanced version of Detect-It-Easy (DIE), optimized for the Intellicrack binary analysis platform.

## Install

### From PIP

The easiest and recommended installation is through `pip`.

```console
pip install icp_engine
```

### Using Git

```console
git clone https://github.com/Zachanardo/ICP-Engine
cd ICP-Engine
```

Install Qt into the `build`. It can be easily installed using [`aqt`](https://github.com/miurahr/aqtinstall) as follow (here with Qt version 6.7.3):

```console
python -m pip install aqtinstall --user -U
python -m aqt install-qt -O ./build linux desktop 6.7.3 linux_gcc_64               # linux x64 only
python -m aqt install-qt -O ./build linux_arm64 desktop 6.7.3 linux_gcc_arm64      # linux arm64 only
python -m aqt install-qt -O ./build windows desktop 6.7.3 win64_msvc2019_64        # windows x64 only
python -m aqt install-qt -O ./build mac desktop 6.7.3 clang_64                     # mac only
```

Then you can install the package

```console
python -m pip install . --user -U
```

## Quick start

```python
import icp_engine, pathlib

print(icp_engine.scan_file("c:/windows/system32/ntdll.dll", icp_engine.ScanFlags.DEEP_SCAN))
'PE64'

print(icp_engine.scan_file("../upx.exe", icp_engine.ScanFlags.RESULT_AS_JSON, str(icp_engine.database_path/'db') ))
{
    "detects": [
        {
            "filetype": "PE64",
            "parentfilepart": "Header",
            "values": [
                {
                    "info": "Console64,console",
                    "name": "GNU linker ld (GNU Binutils)",
                    "string": "Linker: GNU linker ld (GNU Binutils)(2.28)[Console64,console]",
                    "type": "Linker",
                    "version": "2.28"
                },
                {
                    "info": "",
                    "name": "MinGW",
                    "string": "Compiler: MinGW",
                    "type": "Compiler",
                    "version": ""
                },
                {
                    "info": "NRV,brute",
                    "name": "UPX",
                    "string": "Packer: UPX(4.24)[NRV,brute]",
                    "type": "Packer",
                    "version": "4.24"
                }
            ]
        }
    ]
}

for db in icp_engine.databases():
    print(db)
C:\Users\User\AppData\Roaming\Python\Python312\site-packages\icp_engine\db\db\ACE
C:\Users\User\AppData\Roaming\Python\Python312\site-packages\icp_engine\db\db\APK\PackageName.1.sg
C:\Users\User\AppData\Roaming\Python\Python312\site-packages\icp_engine\db\db\APK\SingleJar.3.sg
C:\Users\User\AppData\Roaming\Python\Python312\site-packages\icp_engine\db\db\APK\_APK.0.sg
C:\Users\User\AppData\Roaming\Python\Python312\site-packages\icp_engine\db\db\APK\_init
C:\Users\User\AppData\Roaming\Python\Python312\site-packages\icp_engine\db\db\Archive\_init
C:\Users\User\AppData\Roaming\Python\Python312\site-packages\icp_engine\db\db\archive-file
C:\Users\User\AppData\Roaming\Python\Python312\site-packages\icp_engine\db\db\arj
C:\Users\User\AppData\Roaming\Python\Python312\site-packages\icp_engine\db\db\Binary\Amiga loadable.1.sg
C:\Users\User\AppData\Roaming\Python\Python312\site-packages\icp_engine\db\db\Binary\archive.7z.1.sg
[...]
```

## Licenses

Released under Apache 2.0 License and integrates the following repositories:

 - [Detect-It-Easy](https://github.com/horsicq/Detect-It-Easy): MIT license
 - [die_library](https://github.com/horsicq/die_library): MIT license
 - [qt](https://github.com/qt/qt): LGPL license

## Original Project

ICP Engine is a fork of [die-python](https://github.com/elastic/die-python), originally developed by @calladoum-elastic at Elastic.
