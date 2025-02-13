from collections import defaultdict
from collections.abc import Callable

from imxInsights.domain.imxObject import ImxObject
from imxInsights.domain.imxReferenceObjects import ImxRef


def process_references(
    imx_object: ImxObject,
    properties: dict[str, str],
    find: Callable[[str], ImxObject | None],
) -> None:
    """
    Helper function to process references in given properties dictionary.

    :param imx_object: The object to which references are added.
    :param properties: The dictionary to check for references.
    :param find: A callable that retrieves an ImxObject by its identifier.
    """
    for prop_key, prop_value in properties.items():
        if prop_key.endswith("Ref") and prop_value != imx_object.puic:
            if not any(
                ref.field == prop_key and ref.lookup == prop_value
                for ref in imx_object.refs
            ):
                imx_object.refs.append(
                    ImxRef(prop_key, prop_value, prop_value, find(prop_value))
                )

        elif prop_key.endswith("Refs"):
            for item in prop_value.split():
                if item != imx_object.puic and not any(
                    ref.field == prop_key and ref.lookup == item
                    for ref in imx_object.refs
                ):
                    imx_object.refs.append(
                        ImxRef(prop_key, prop_value, item, find(item))
                    )


def add_refs(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
) -> None:
    """
    Populates references in imx_objects within the tree dictionary.

    :param tree_dict: A dictionary mapping PUICs to lists of ImxObjects.
    :param find: A callable that retrieves an ImxObject by its identifier.
    """
    for key, imx_objects in tree_dict.items():
        for imx_object in imx_objects:
            process_references(imx_object, imx_object.properties, find)
            process_references(imx_object, imx_object.extension_properties, find)
