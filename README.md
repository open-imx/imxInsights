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

**Source Code**: <a href="https://github.com/ImxEra/imxInsights" target="_blank">https://github.com/open-imx/imxInsights</a>

***THIS LIBRARY*** is a personal project and therefore no responsibility for the functionality, accuracy, or usage of this library. 
***THE PUBLIC retains full ownership and responsibility for the codebase.*** 

!!! danger "Warning!"  

    - The goal of `imxInsights` is to extract information from imx files. **Please note that modifying, 
    adding, deleting, or altering data is beyond the scope of this module**.
    - `imxInsights` explicit supports imx versions 1.2.4, 5.0.0, 10.0.0, 11.0.0 and 12.0.0.
    
!!! info "Audience"

    The intended audience for `imxInsights` consists of end users with basic Python knowledge. Therefore, the module offers a minimalistic API that is thoroughly documented. 
    We leverage the remarkable `makedocs` plugins to effortlessly generate a polished website from documentations and markdown files.


## This repository host the imx 12.0 implementation     

Transitioning from version 1.2.4 / 5.0.0 to 12.0.0 of this library necessitates extensive changes and significant code 
rewriting due to fundamental shifts in how imx files are utilized. Below, we outline a comprehensive roadmap that will 
be continually updated until we reach the first stable version.


!!! danger "New concept, breaking changes!"  
    ***This project is currently under active development and is not yet in its final form.***
    ***As such, there may be frequent changes, incomplete features, or potential instability.***

    ***-   We recommend using the stable and feature richer 0.1.0 release on for imx versions "1.2.4" and "5.0.0".***

### Roadmap

####  Q3-2 2024 - MVP library release on PyPI
![](https://progress-bar.dev/10?title=progresses)

- [X] Imx Compair imx version ignore
- [X] Compair object type between 2 versions
- [X] Compair as pandas dataframe
- [X] Excel compair output
- [X] Excel diff color dataframe and excel
- [ ] Compair object metadata overview
- [ ] Imx data as Geojson
- [ ] Compair as geojson
- [ ] Imx container metadata
- [ ] Imx single file metadata
- [ ] 3d Measure calculator
- [ ] Documentation update
- [ ] min tests coverage 95%
- [ ] clean git by fresh upload 🎉
- [ ] GitHub actions release on pypi


####  Q4-1 2024
- [ ] (Imx) Area's and area classifier
- [ ] Ref as objects
- [ ] nice ref display
- [ ] parent path display
- [ ] km by linear referencing
- [ ] RailConnectionInfos class
- [ ] TrackFragments support
- [ ] implement puic as a concept instead of passing keys to make clear what we use as a key.


#### Backlog current features implementation
- [ ] Compair object type as timeline
- [ ] graph implementation
- [ ] generate graph geometry
- [ ] Situation changes support (read and check)
- [ ] graph end user api
- [ ] Imx 1.0-RC release on pypi


## Supported Python Versions
This library is compatible with ***Python 3.10*** and above. 

!!! warning  
    ***Python Typehints are awesome therefor 3.9 and below will NOT be supported***.


## Features
- [X] Imx 1.2.4 5.0.0 and 12.0.0 file import
- [X] Imx single file 
- [X] Imx zip container
- [X] ImxExtension objects
- [X] GML shapley geometry
- [X] RailConnection shapley geometry
- [X] Known parent and children
- [X] Imx data as Pandas dataframe


## Quick Start
todo

## Distribution and installation
todo

## Code samples and snippets
todo

## Contributing
Contributions welcome! For more information on the design of the library, see [contribution guidelines for this project](CONTRIBUTING.md).

