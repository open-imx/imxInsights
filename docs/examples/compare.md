## Comparing IMX Containers and Situations

Using the `ImxSingleFile` and `ImxMultiRepo` classes, you can seamlessly compare IMX containers or specific scenarios across different versions of the IMX format. Objects sharing the same PUIC are recognized as identical, which simplifies comparisons across various contexts and versions.

We leverage Pandas to manage tabular data, facilitating the analysis and export of comparison results to Excel. Our implementation features custom diff operators tailored for IMX data, and we enhance visualization with color-coded styles on output borders, allowing for quick identification of discrepancies.

While we support comparisons between different IMX versions, this feature requires explicit selection. Below, we have some sample code to illustrate how to use these classes effectively:

=== "SingleImx"
    ```py
    --8<-- "docs/examples/compare/singleImx_compare.py"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/compare/containerImx_compare.py"
    ```
=== "Different IMX version"
    ```py
    --8<-- "docs/examples/compare/different_imx_version_compare.py"
    ```
