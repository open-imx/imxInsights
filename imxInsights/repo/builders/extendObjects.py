from collections import defaultdict

from lxml.etree import _Element as Element

from imxInsights.domain.imxObject import ImxObject
from imxInsights.exceptions import ErrorLevelEnum
from imxInsights.exceptions.imxExceptions import ImxUnconnectedExtension
from imxInsights.file.imxFile import ImxFile
from imxInsights.repo.builders.buildExceptions import BuildExceptions
from imxInsights.repo.config import Configuration, get_valid_version


def extend_objects(
    tree_dict: defaultdict[str, list[ImxObject]],
    build_exceptions: BuildExceptions,
    imx_file: ImxFile,
    element: Element | None,
):
    """
    Extends IMX objects in a tree structure with additional properties and handles exceptions.

    ??? info
        This function iterates over objects of specific types within an IMX file and attempts to extend them
        using corresponding objects found in a tree dictionary. If the extension is successful, it merges the
        properties of the objects. If not, it logs appropriate warnings.

    Args:
        tree_dict: A dictionary containing lists of IMX objects indexed by their unique identifiers.
        build_exceptions: An object to collect exceptions that occur during the build process.
        imx_file: An object representing the IMX file to be processed.
        element: An optional XML element to narrow down the search scope within the IMX file.

    Raises:
        ValueError: If `element` is None and `imx_file.root` is also None.
    """

    def _extend_imx_object():
        """
        Extends a single IMX object with properties from an extension object.

        This function determines whether an IMX object can be extended by checking
        the hash and parent hash of the objects. If they match, the properties of
        the extension object are merged into the original object.
        """
        extend = False
        imx_file_extension_obj = extension_object.imx_file

        # get hash
        if hasattr(imx_file_extension_obj, "base_reference"):
            base_reference = imx_file_extension_obj.base_reference
        else:
            base_reference = None
        parent_hashcode = base_reference.parent_hashcode if base_reference else None

        # determinate if extend
        if imx_file_extension_obj.file_hash == imx_object.imx_file.file_hash:
            extend = True
        elif parent_hashcode == imx_object.imx_file.file_hash:
            extend = True
        else:
            build_exceptions.add(
                ImxUnconnectedExtension(
                    f"{imx_file_extension_obj.path} hash of base reference file is not valid, cannot extend {imx_object.path} with puic {imx_object.puic}",
                    ErrorLevelEnum.WARNING,
                ),
                puic_to_find,
            )

        if extend:
            imx_object.extend_imx_object(extension_object)

    # main method
    valid_version = get_valid_version(imx_file.imx_version)
    for object_type, ref_attr in Configuration.get_object_type_to_extend_config(
        valid_version
    ).__dict__.items():
        if element is None:
            if imx_file.root is not None:
                objects = [
                    ImxObject(element=element, imx_file=imx_file)
                    for element in imx_file.root.findall(
                        f".//{{http://www.prorail.nl/IMSpoor}}{object_type}"
                    )
                ]
            else:
                # Handle the case where imx_file.root is None
                # Perhaps raise an exception or handle differently based on your application logic
                raise ValueError("imx_file.root is None when element is None")  # noqa: TRY003
        else:
            objects = [
                ImxObject(element=element, imx_file=imx_file)
                for element in element.findall(
                    f".//{{http://www.prorail.nl/IMSpoor}}{object_type}"
                )
            ]
        for extension_object in objects:
            puic_to_find = extension_object.properties[ref_attr[0]]
            if puic_to_find in tree_dict.keys():
                object_to_extend = tree_dict[puic_to_find]
                for imx_object in object_to_extend:
                    _extend_imx_object()
            else:
                build_exceptions.add(
                    ImxUnconnectedExtension(
                        f"{extension_object.path} reffed object with {puic_to_find} not present in dataset, cannot extend object",
                        ErrorLevelEnum.WARNING,
                    ),
                    puic_to_find,
                )
