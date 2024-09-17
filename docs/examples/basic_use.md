

One of the main differences between a single IMX file and a containerized IMX is that a single file can represent multiple situations. 
A containerized IMX, on the other hand, is a snapshot in time and can be seen as a single situation. 
For more information, refer to the [way of working section](/context/way_of_working/)

To maintain consistency and ease of use, the APIs for handling both single and containerized IMX files are designed to be as similar as possible. 
This allows end users to switch between single and containerized IMX files with minimal changes to their code. 


!!! info "Single file IMX"
    In this case, the IMX is a single XML file containing a situation or a project with an initial situation and optional a new situation. 
    ***You need to define the situation of interest.***

!!! info "Containerized IMX" 
    In this case, the IMX is a container holding multiple XML files that represent a snapshot in time. 
    ***You do not need to define a situation.***

The basic examples below can be switched using the tabs, making the differences clear.


*todo: migrate to new [tab](https://facelessuser.github.io/pymdown-extensions/extensions/blocks/plugins/tab/) ensure javascript tab syncer*

## Load file

=== "SingleImx"
    ```py
    --8<-- "docs/examples/basic_use/singleImx_main.py:0:4"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/basic_use/containerImx_main.py:0:3"
    ```

## Get file metadata
=== "SingleImx"
    ```py
    --8<-- "docs/examples/basic_use/singleImx_main.py:6:8"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/basic_use/containerImx_main.py:6:10"
    ```

## Get build exceptions
=== "SingleImx"
    ```py
    --8<-- "docs/examples/basic_use/singleImx_main.py:10:12"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/basic_use/containerImx_main.py:13:15"
    ```

## Query Objects
=== "SingleImx"
    ```py
    --8<-- "docs/examples/basic_use/singleImx_main.py:12:"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/basic_use/containerImx_main.py:16:"
    ```

## MultiContainer
=== "SingleImx"
    ```py
    --8<-- "docs/examples/basic_use/singleImx_multi_repo.py"
    ```
=== "ContainerImx"
    ```py
    --8<-- "docs/examples/basic_use/container_imx_multi_repo.py"
    ```

## Compair Objects
***Below is a preview feature, changes will be made!***

```py
--8<-- "docs/examples/basic_use/compair_main.py"
```

