## Comparing IMX Containers and Situations



!!! danger "Warning!"  

    This feature is currently in development. Sections of code that are commented out are not yet functional.


Using the `ImxSingleFile` and `ImxMultiRepo` classes, you can seamlessly compare IMX containers or specific scenarios across different versions of the IMX format. Objects sharing the same PUIC are recognized as identical, which simplifies comparisons across various contexts and versions.

We leverage Pandas to manage tabular data, facilitating the analysis and export of comparison results to Excel. Our implementation features custom diff operators tailored for IMX data, and we enhance visualization with color-coded styles on output borders, allowing for quick identification of discrepancies.

While we support comparisons between different IMX versions, this feature requires explicit selection. Below, we have some sample code to illustrate how to use these classes effectively:

## MultiRepo
If IMX objects share the same unique key (puic) this is used to collect multiple instances in different containers. 
The order is crucial for comparison. Currently, we support more than two containers, but the diff is limited to A vs. B. 
Timeline comparisons will be supported in the future.

First we need to create a multy repo, then we need to get the compare.

=== "SingleImx"
    ```py
    --8<-- "docs/examples/compare/singleImx_compare.py::15"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/compare/containerImx_compare.py::16"
    ```
=== "Different IMX version"
    ```py
    --8<-- "docs/examples/compare/different_imx_version_compare.py::17"
    ```

## Get pandas dataframe
Each row represents an IMX object, while the columns denote the attribute or element values. 
We utilize the IMX path to identify an object type or generate an Excel report of all paths. 
For added items, we prefix them with `++`, for deleted items `--` and for changes we denote changes with `->`.

We use color highlighting to detect changes in dataframes and Excel exports. 
This visual aid helps easily spot differences between values, making data comparison more efficient and user-friendly.

```py
--8<-- "docs/examples/compare/singleImx_compare.py:16:23"
```

### Excel
It is what it is... the world still runs on Excel, so we've provided an Excel output.
```py
--8<-- "docs/examples/compare/singleImx_compare.py:25:29"
```


## GeoJSON

Basically the same as a DataFrame, but when GML coordinates are present, they also include geometry. 
RailConnections are supported, and future features will include other objects without GML.

```py
--8<-- "docs/examples/compare/singleImx_compare.py:30:"
```
