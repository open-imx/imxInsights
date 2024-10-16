# Distribution and installation

## Version 0.1.x

Until we achieve the MVP of the library, we will build a Python wheel upon each release, which you can download from GitHub. 
In the future, we will release the new version on PyPI.

!!! info  
    ***We recommend using the stable and feature richer 0.1.0 release on for imx versions "1.2.4" and "5.0.0".***

The 0.1.x version of imxInsights is distributed on [PYPI](https://pypi.org) and can be installed by the following pip command:

```
pip install imxInsights
```

## ImxInsights v0.2.x
This project is still in development, currently you have two options:

1. **Download the repository from github** build a wheel and use it now.
2. **Wait for the official release**, then download the wheel file and install it via pip.
3. **Wait for the official pypi** and install it via pip.

We aim to release it on pypi end of Q4 2024.


## Code samples and snippets
Below are minimal examples to load single imx file or imx containers. 
For more code samples and snippets in the example section / folder and use the api reference for exploration.


### Load Single File IMX

```py
--8<-- "docs/examples/basic_use/singleImx_main.py::8"
```


### Load Containerized IMX

```py
--8<-- "docs/examples/basic_use/containerImx_main.py::11"
```


### Get Insights

=== "SingleImx"
    ```py
    --8<-- "docs/examples/basic_use/singleImx_main.py:9:"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/basic_use/containerImx_main.py:12:"
    ```
