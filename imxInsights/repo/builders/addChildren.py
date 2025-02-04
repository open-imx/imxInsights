from collections import defaultdict
from collections.abc import Callable

from imxInsights.domain.imxObject import ImxObject


def add_children(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
) -> None:
    """
    Adds child objects to each IMX object in a tree dictionary.

    ??? info
        This function iterates over each IMX object in the provided tree dictionary, finds
        its child elements by their unique identifiers (PUIC), and assigns these child objects
        to the `children` attribute of the parent IMX object.

    Args:
        tree_dict: A dictionary containing lists of IMX objects indexed by their unique identifiers.
        find: A callable to find an IMX object by its unique identifier (PUIC).
    """

    for key, values in tree_dict.items():
        for value in values:
            if value.element is not None:
                elements_with_puic = value.element.xpath(".//*[@puic]")
                children = [
                    find(element.get("puic"))
                    for element in elements_with_puic
                    if value.puic != element.get("puic")
                ]
                value.children = children
