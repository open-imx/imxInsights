from collections.abc import Callable, Iterable

from imxInsights.domain.imxObject import ImxObject
from imxInsights.repo.tree.buildExceptions import BuildExceptions


def add_refs(
    objects: Iterable[ImxObject],
    find: Callable[[str], ImxObject],
    exceptions: BuildExceptions,
):
    for imx_object in objects:
        pass

        # xpath_query = ".//*[@*[substring(name(), string-length(name()) - 2) = 'Ref' or substring(name(), string-length(name()) - 3) = 'Refs']]"
        # elements_with_ref_attributes = imx_object.element.xpath(xpath_query)
        # if len(elements_with_ref_attributes) != 0:
        #     print()
        #
        # xpath_query = ".//*[substring(name(), string-length(name()) - 2) = 'Ref' or substring(name(), string-length(name()) - 3) = 'Refs']"
        # elements_with_ref_tags = imx_object.element.xpath(xpath_query)
        # if len(elements_with_ref_tags) != 0:
        #     print()

        # ref = [value for key, value in imx_object.properties.items() if key.endswith('Ref')]
        # refs = [value.split(" ") for key, value in imx_object.properties.items() if key.endswith('Refs')]
