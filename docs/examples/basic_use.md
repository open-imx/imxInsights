

One of the main differences between a single IMX file and a containerized IMX is that a single file can represent multiple situations. 
A containerized IMX, on the other hand, is a snapshot in time and can be seen as a single situation.

To maintain consistency and ease of use, the APIs for handling both single and containerized IMX files are designed to be as similar as possible. 
This allows end users to switch between single and containerized IMX files with minimal changes to their code. 


!!! info "Single file IMX"
    In this case, the IMX is a single XML file containing a situation or a project with an initial situation and optional a new situation. 
    ***You need to define the situation of interest.***

!!! info "Containerized IMX" 
    In this case, the IMX is a container holding multiple XML files that represent a snapshot in time. 
    ***You do not need to define a situation.***

The basic examples below can be switched using the tabs, making the differences clear.


## Load file

The `imxInsights` package provides two main ways to load IMX files, depending on the IMX version and file structure:

- **For versions up to 12:** IMX data is stored as a single XML file containing two situations (scenarios). The `ImxSingleFile` class handles loading and managing these individual XML files.

- **From version 12 onwards:** IMX data is packaged in a container format (e.g., ZIP archive or directory structure) that holds multiple files, allowing more flexibility. The `ImxContainer` class is used to handle and load these containers.


=== "SingleImx"
    ```py
    --8<-- "docs/examples/basic_use/singleImx_main.py:0:4"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/basic_use/containerImx_main.py:0:3"
    ```

## Get file metadata

To retrieve metadata from IMX files, there are distinct approaches depending on the file type:

-  For `ImxSingleFile` you can obtain all necessary metadata in a single call.

-  For `ImxContainer` retrieving metadata from containers requires individual calls for each file within the container.

=== "SingleImx"
    ```py
    --8<-- "docs/examples/basic_use/singleImx_main.py:6:8"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/basic_use/containerImx_main.py:6:10"
    ```

## Get build exceptions
When loading an IMX file, various errors may occur. These errors are listed and logged, allowing you to review them after the loading process. You can look up build exceptions for both single files and container files.

For example, you can retrieve exceptions using the following code:

=== "SingleImx"
    ```py
    --8<-- "docs/examples/basic_use/singleImx_main.py:10:12"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/basic_use/containerImx_main.py:13:15"
    ```

## Query Objects
After loading an IMX file, you can effortlessly extract valuable information from it. For a detailed list of available options, please consult the API reference. Below are the key concepts for querying both single and container files, which utilize a consistent API for seamless interaction.

When working with `ImxSingleFile`, remember to interact with specific instances to retrieve information. With `ImxContainer`, you can directly access the object for your queries.

=== "SingleImx"
    ```py
    --8<-- "docs/examples/basic_use/singleImx_main.py:12:"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/basic_use/containerImx_main.py:16:"
    ```

## Comparing IMX Containers and Situations

Using the `ImxSingleFile` and `ImxMultiRepo` classes, you can seamlessly compare IMX containers or specific scenarios across different versions of the IMX format. Objects sharing the same PUIC are recognized as identical, which simplifies comparisons across various contexts and versions.

We leverage Pandas to manage tabular data, facilitating the analysis and export of comparison results to Excel. Our implementation features custom diff operators tailored for IMX data, and we enhance visualization with color-coded styles on output borders, allowing for quick identification of discrepancies.

While we support comparisons between different IMX versions, this feature requires explicit selection. Below, we have some sample code to illustrate how to use these classes effectively:

=== "SingleImx"
    ```py
    --8<-- "docs/examples/basic_use/singleImx_compare.py"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/basic_use/containerImx_compare.py"
    ```
=== "Different IMX version"
    ```py
    --8<-- "docs/examples/basic_use/different_imx_version_compare.py"
    ```

