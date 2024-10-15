import warnings
from collections import defaultdict
from collections.abc import Iterable
from typing import Optional

from lxml.etree import _Element as Element
from shapely import (
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.geometry import GeometryCollection

from imxInsights.domain.imxGeographicLocation import ImxGeographicLocation
from imxInsights.file.containerizedImx.imxDesignCoreFile import ImxDesignCoreFile
from imxInsights.file.containerizedImx.imxDesignPetalFile import ImxDesignPetalFile
from imxInsights.file.imxFile import ImxFile
from imxInsights.utils.flatten_unflatten import flatten_dict
from imxInsights.utils.xml_helpers import (
    find_parent_entity,
    find_parent_with_tag,
    lxml_element_to_dict,
    trim_tag,
)


class ImxObject:
    """
    Represents an object within an IMX file.

    ??? info
        This class is used to encapsulate the data and functionality for an object within an IMX file.
        It contains attributes parsed from the XML element representing the object, and methods to
        manipulate and query the object.

    Todo:
        = Find way to make immutable after building repo.
        - Move back to repo, specific types like trackassets should be in domain.

    Args:
        element: The XML element representing the object.
        imx_file: The IMX file associated with the object.
        parent: The parent ImxObject of the object. Defaults to None.

    Attributes:
        element: Returns the XML element representing the object.
        tag: Returns the tag of the XML element.
        path: Returns the path of the object within the XML structure.
        name: Returns the name attribute of the XML element.
        puic: Returns the puic attribute of the XML element.
        geometry: Object geometer
        geographic_location: Returns the geographic location associated with the object.
    """

    def __init__(
        self,
        element: Element,
        imx_file: ImxFile,
        parent: Optional["ImxObject"] = None,
    ):
        self._element: Element = element
        self.imx_file: ImxFile | ImxDesignCoreFile | ImxDesignPetalFile = imx_file
        self.parent: ImxObject | None = parent
        self.children: list[ImxObject | None] = []
        self.imx_extensions: list[ImxObject] = []
        self._geometry: (
            LineString
            | Point
            | Polygon
            | MultiLineString
            | MultiPoint
            | MultiPolygon
            | GeometryCollection
        ) = GeometryCollection()
        self.properties: dict[str, str] = flatten_dict(
            lxml_element_to_dict(self._element)
        )
        self.imx_situation: str | None = self._get_imx_situation()
        self.container_id: str | None = None

    def __repr__(self) -> str:
        return f"<ImxObject {self.path} puic={self.puic} name='{self.name}'/>"

    @property
    def get_parent_path(self):
        if self.parent is None:
            return self.puic
        return self.parent.get_parent_path + "." + self.puic

    @property
    def element(self) -> Element:
        return self._element

    @property
    def tag(self) -> str:
        return trim_tag(self._element.tag)

    @property
    def path(self) -> str:
        tags = [parent.tag for parent in self._parents_generator()]
        tags.reverse()
        tags.append(self.tag)
        return ".".join(tags)

    @property
    def name(self) -> str:
        return self._element.get("name", "")

    @property
    def puic(self) -> str:
        return self._element.get("puic", "")

    @property
    def geographic_location(self) -> ImxGeographicLocation | None:
        return ImxGeographicLocation.from_element(self._element)

    @property
    def geometry(
        self,
    ) -> (
        LineString
        | Point
        | Polygon
        | MultiLineString
        | MultiPoint
        | MultiPolygon
        | GeometryCollection
    ):
        if self.geographic_location is not None:
            return self.geographic_location.shapely
        return self._geometry

    @geometry.setter
    def geometry(
        self,
        geometry: LineString
        | Point
        | Polygon
        | MultiLineString
        | MultiPoint
        | MultiPolygon
        | GeometryCollection,
    ):
        self._geometry = geometry

    @property
    def extension_properties(self) -> dict[str, str]:
        extensions_dict = defaultdict(list)
        for item in self.imx_extensions:
            extensions_dict[f"extension.{item.tag}"].append(item.properties)
        # todo: make flatten_dict also handle defaultdict
        return flatten_dict(dict(extensions_dict))

    def extend_imx_object(self, imx_extension_object: "ImxObject") -> None:
        """
        Extends the current ImxObject with another ImxObject.

        Args:
            imx_extension_object (ImxObject): The ImxObject to extend with.
        """
        self.imx_extensions.append(imx_extension_object)

    def _get_imx_situation(self) -> str | None:
        """Retrieves the situation tag (pre imx 12.0) from the element.

        Returns:
            str or None: The situation or None if no matching is found.
        """
        namespace = "{http://www.prorail.nl/IMSpoor}"
        tags = [
            f"{namespace}Situation",
            f"{namespace}InitialSituation",
            f"{namespace}NewSituation",
        ]
        parent_element = find_parent_with_tag(self._element, tags)
        if parent_element is not None:
            return parent_element.tag.removeprefix(namespace)
        return None

    def _parents_generator(self) -> Iterable["ImxObject"]:
        """
        A generator that yields the parents of the object.

        Yields:
            ImxObject: The parent of the object.
        """
        parent = self.parent
        while parent is not None:
            yield parent
            parent = parent.parent

    def can_compare(self, other: Optional["ImxObject"]) -> bool:
        """
        Checks if the object can be compared with another object.

        Args:
            other (ImxObject): The other ImxObject to compare with.

        Returns:
            bool: True if the objects can be compared, False otherwise.
        """
        if other is None:
            return True

        if other.puic != self.puic:
            return False

        if other.path != self.path:
            warnings.warn(
                f"Cannot compare {self.path} with {other.path}, tags do not match"
            )
            return False

        return True

    @staticmethod
    def _get_lookup_tree_from_element(
        entities: list[Element], imx_file: ImxFile
    ) -> list["ImxObject"]:
        """
        Generates a lookup tree from a list of XML entities.

        Args:
            entities (List[Element]): The list of XML entities.
            imx_file (ImxFile): The IMX file associated with the entities.

        Returns:
            List[ImxObject]: The lookup tree generated from the XML entities.
        """
        lookup: dict[Element, ImxObject] = {}
        result: list[ImxObject] = []

        for entity in entities:
            parent_element = find_parent_entity(entity)
            parent: ImxObject | None = None

            if parent_element is not None:
                if parent_element in lookup:
                    parent = lookup[parent_element]
                else:
                    warnings.warn("Parent entity not found in lookup")

            obj = ImxObject(parent=parent, element=entity, imx_file=imx_file)
            lookup[entity] = obj
            result.append(obj)

        return result

    @classmethod
    def lookup_tree_from_imx_file(cls, imx_file: ImxFile) -> list["ImxObject"]:
        """
        Generates a lookup tree from an IMX file.

        Args:
            imx_file (ImxFile): The IMX file.

        Returns:
            List[ImxObject]: The lookup tree generated from the IMX file.
        """
        imx_key = "@puic"

        if imx_file.root is None:
            raise ValueError(  # noqa: TRY003
                "IMX file root element is None. Cannot generate lookup tree."
            )

        entities = imx_file.root.findall(f".//*[{imx_key}]")
        return cls._get_lookup_tree_from_element(entities, imx_file)

    @classmethod
    def lookup_tree_from_element(
        cls, element: Element, imx_file: ImxFile
    ) -> list["ImxObject"]:
        """
        Generates a lookup tree from a specific XML element within an IMX file.

        Args:
            element (Element): The XML element to start building the lookup tree from.
            imx_file (ImxFile): The IMX file associated with the XML element.

        Returns:
            List[ImxObject]: The lookup tree generated from the XML element.
        """
        imx_key = "@puic"
        entities = element.findall(f".//*[{imx_key}]")
        return cls._get_lookup_tree_from_element(entities, imx_file)
