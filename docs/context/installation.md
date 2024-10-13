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
[xlsxwriter](https://pypi.org/project/XlsxWriter/)


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
