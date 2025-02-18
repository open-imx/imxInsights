# imxInsights

![imxInsights logo](https://raw.githubusercontent.com/open-imx/imxInsights/main/docs/assets/logo.svg#only-dark#gh-dark-mode-only)
![imxInsights logo](https://raw.githubusercontent.com/open-imx/imxInsights/main/docs/assets/logo-light.svg#only-light#gh-light-mode-only)

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/imxInsights)
[![PyPI - Status](https://img.shields.io/pypi/status/imxInsights)](https://pypi.org/project/imxInsights/)

[![GitHub](https://badgen.net/badge/icon/github?icon=github&label)](https://github.com/open-imx/imxInsights)
[![Documentation Status](https://readthedocs.org/projects/ansicolortags/badge/?version=latest)](http://ansicolortags.readthedocs.io/?badge=latest)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
![PyPI - License](https://img.shields.io/pypi/l/imxInsights)

**Documentation**: <a href="https://open-imx.github.io/imxInsights/" target="_blank">https://open-imx.github.io/imxInsights/</a>

**Source Code**: <a href="https://github.com/open-imx/imxInsights" target="_blank">https://github.com/open-imx/imxInsights</a>

***THIS LIBRARY*** is a personal project and therefore no responsibility for the functionality, accuracy, or usage of this library. 
***THE PUBLIC retains full ownership and responsibility for the codebase.***

!!! danger "Warning!"  

    - The goal of `imxInsights` is to extract information from imx files. **Please note that modifying, 
    adding, deleting, or altering data is beyond the scope of this module**.
    - `imxInsights` explicit supports imx versions 1.2.4, 5.0.0, 10.0.0, 11.0.0 and 12.0.0.
    
!!! info "Audience"

    The intended audience for `imxInsights` consists of end users with basic Python knowledge. Therefore, the module offers a minimalistic API that is thoroughly documented. 
    We leverage the remarkable `makedocs` plugins to effortlessly generate a polished website from documentations and markdown files.

## Features
- ✅ IMX file import (1.2.4, 5.0.0, 12.0.0)
- ✅ IMXExtension objects
- ✅ GML & RailConnection Shapely geometry
- ✅ Parent-child as objects
- ✅ IMX data as Pandas DataFrame
- ✅ IMX objects as GeoJSON (WGS or RD)
- ✅ IMX compare between different IMX versions (situations, timeline)
- ✅ Comparison result as Pandas DataFrame & GeoJSON
- ✅ Color changes for better comparison 
- ✅ Excel compare output 
- ✅ Excel container compare chain 

## Open-IMX Initiative
**imxInsights** is part of the **Open-IMX initiative**, which is dedicated to enhancing the accessibility and usability of IMX data. 
This initiative aims to provide a collaborative environment for developers, data analysts and railway professionals to effectively work with IMX data.

### 🗪 Discord Community Channel 🤝

💥 We invite you to join the [👉 open-imx community on Discord](https://discord.gg/wBses7bPFg). 


## This repository host the imx 12.0 implementation     

Transitioning from version 1.2.4 / 5.0.0 to 12.0.0 of this library necessitates extensive changes and significant code 
rewriting due to fundamental shifts in how imx files are utilized. 

!!! danger "New concept, breaking changes!"  
    ***This project is currently under active development and is not yet in its final form.***
    ***As such, there may be frequent changes, incomplete features, or potential instability.***

    ***-   We recommend using the stable and feature richer 0.1.0 release on for imx versions "1.2.4" and "5.0.0".***

## Backlog and Roadmap
<a href="https://github.com/orgs/open-imx/projects/5/" target="_blank">https://github.com/orgs/open-imx/projects/5/</a>

### Contributing

We welcome contributions from everyone! 
If you're interested in contributing to the project, please refer to our [contribution guidelines](https://raw.githubusercontent.com/open-imx/imxInsights/refs/heads/main/CONTRIBUTING.md) for more information. 
For any questions or discussions, feel free to ask in our [Discord channel](https://discord.gg/wBses7bPFg).

## Dependencies
[dateparser](https://pypi.org/project/dateparser/),
[types-dateparser](https://pypi.org/project/types-dateparser/),
[deepdiff](https://pypi.org/project/deepdiff/),
[jinja2](https://pypi.org/project/Jinja2/),
[lxml](https://pypi.org/project/lxml/),
[types-lxml](https://pypi.org/project/types-lxml/),
[loguru](https://pypi.org/project/loguru/),
[networkx](https://pypi.org/project/networkx/),
[types-networkx](https://pypi.org/project/types-networkx/),
[pandas](https://pypi.org/project/pandas/),
[pandas-stubs](https://pypi.org/project/pandas-stubs/),
[pyproj](https://pypi.org/project/pyproj/),
[shapely](https://pypi.org/project/shapely/),
[types-shapely](https://pypi.org/project/types-shapely/),
[tqdm](https://pypi.org/project/tqdm/),
[tqdm-stubs](https://pypi.org/project/tqdm-stubs/),
[xlsxwriter](https://pypi.org/project/XlsxWriter/),
[geojson](https://pypi.org/project/geojson/)

### Development dependencies
[bumpversion](https://pypi.org/project/bumpversion/),
[hatch](https://pypi.org/project/hatch/),
[mkdocs](https://pypi.org/project/mkdocs/),
[mkdocs-material](https://pypi.org/project/mkdocs-material/),
[mkdocstrings](https://pypi.org/project/mkdocstrings/),
[pre-commit](https://pypi.org/project/pre-commit/),
[pytest](https://pypi.org/project/pytest/),
[pytest-asyncio](https://pypi.org/project/pytest-asyncio/),
[pytest-cov](https://pypi.org/project/pytest-cov/),
[ruff](https://pypi.org/project/ruff/),
[filelock](https://pypi.org/project/filelock/),
[distlib](https://pypi.org/project/distlib/),
[mypy](https://pypi.org/project/mypy/)
