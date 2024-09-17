# Distribution and installation

Until we achieve the MVP of the library, we will build a Python wheel upon each release, which you can download from GitHub. 
In the future, we will release the new version on PyPI.


## Version 0.1.x
!!! info  
    ***We recommend using the stable and feature richer 0.1.0 release on for imx versions "1.2.4" and "5.0.0".***

The 0.1.x version of imxInsights is distributed on [PYPI](https://pypi.org) and can be installed by the following pip command:

```
pip install imxInsights
```


## Code samples and snippets
Below are minimal examples to load single imx file or imx containers. 
For more code samples and snippets in the example section / folder and use the api reference for exploration.


### Single file IMX

```py
--8<-- "docs/examples/basic_use/singleImx_main.py"
```


### Containerized IMX


```py
--8<-- "docs/examples/basic_use/containerImx_main.py"
```


## Dependencies

[lxml](https://lxml.de/)
, [shapely](https://pypi.org/project/shapely/)
, [pyproj](https://pypi.org/project/pyproj/)
, [loguru](https://pypi.org/project/loguru/)
, [pandas](https://pandas.pydata.org/)
, [xlsxwriter](https://pypi.org/project/XlsxWriter/)

### Development dependencies
[hatch](https://github.com/pypa/hatch)
, [ruff](https://github.com/astral-sh/ruff)
, [mypy](https://mypy.readthedocs.io/en/stable/)
, [bumpversion](https://github.com/peritus/bumpversion)
, [mkdocs](https://www.mkdocs.org/)
, [mkdocstrings](https://github.com/mkdocstrings/mkdocstrings)
, [mkdocs-material](https://squidfunk.github.io/mkdocs-material/)
