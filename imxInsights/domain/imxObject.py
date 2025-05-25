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
from imxInsights.domain.imxReferenceObjects import ImxRef
from imxInsights.file.containerizedImx.imxDesignCoreFile import ImxDesignCoreFile
from imxInsights.file.containerizedImx.imxDesignPetalFile import ImxDesignPetalFile
from imxInsights.file.imxFile import ImxFile
from imxInsights.utils.flatten_unflatten import (
    flatten_dict,
    reindex_dict,
    remove_sourceline_from_dict,
    sort_dict_by_sourceline,
)
from imxInsights.utils.xml_helpers import (
    find_parent_entity,
    find_parent_with_tag,
    lxml_element_to_dict,
    trim_tag,
)


class ImxObject:
    """
    Represents an object within an IMX file.

    !!! info
        This class is used to encapsulate the data and functionality for an object within an IMX file.
        It contains attributes parsed from the XML element representing the object, and methods to
        manipulate and query the object. In the future we will add specific domain objects like
        TrackAssets, RailConnections ect.

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
        self.properties: dict[str, str] = self._set_properties()
        self.imx_situation: str | None = self._get_imx_situation()
        self.container_id: str | None = None
        self.refs: list[ImxRef] = []

    def __repr__(self) -> str:
        return f"<ImxObject {self.path} puic={self.puic} name='{self.name}'/>"

    def _set_properties(self):
        return remove_sourceline_from_dict(
            reindex_dict(
                sort_dict_by_sourceline(
                    flatten_dict(lxml_element_to_dict(self._element))
                )
            )
        )

    @property
    def parent_path(self):
        if self.parent is None:
            return self.puic
        return self.parent.parent_path + "." + self.puic

    @property
    def element(self) -> Element:
        return self._element

    @property
    def tag(self) -> str:
        return trim_tag(
            f"{self._element.tag.decode('utf-8')}"
            if isinstance(self._element.tag, bytes)
            else f"{self._element.tag}"
        )

    @property
    def path(self) -> str:
        tags = [parent.tag for parent in self._parents_generator()]
        tags.reverse()
        tags.append(self.tag)
        return ".".join(tags)

    @property
    def path_to_root(self) -> str:
        def process_tag(tag):
            if tag[0] == "{":
                namespace, local_name = tag[1:].split("}", 1)
                if namespace == "http://www.opengis.net/gml":
                    return f"gml:{local_name}"
                return local_name
            return tag

        path = []
        element = self._element
        while element is not None:
            path.append(process_tag(element.tag))
            parent = element.getparent()
            if parent is None:
                break
            element = parent
        return ".".join(reversed(path))

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
        return flatten_dict(dict(extensions_dict))

    def get_imx_property_dict(
        self,
        add_extension_properties: bool = True,
        add_parent: bool = True,
        add_children: bool = True,
        add_geometry: bool = False,
    ) -> dict[str, str]:
        """
        Retrieve a dictionary containing IMX properties, including the tag, path,
        properties, and optionally extension properties and geometry.
        Args:
            add_extension_properties : A dictionary of additional extension properties to include in the result.
            add_parent: Includes the parent puic in the result.
            add_children: Includes all puics of children in the result.
            add_geometry: Includes string representing geometry data in the result.
        Returns:
            A dictionary with 'keys' 'values' of all interesting imx properties
        """
        # TODO!: find all property getters / merges for (dataframe) exports
        result = {"tag": self.tag, "path": self.path}
        if add_parent:
            result["parent"] = self.parent.puic if self.parent is not None else ""
        if add_children:
            result["children"] = " ".join(
                [item.puic for item in self.children if item is not None]
            )
        result = result | self.properties
        if add_extension_properties:
            result |= self.extension_properties
        if add_geometry:
            result["geometry"] = self.geometry.wkt
        return result

    def extend_imx_object(self, imx_extension_object: "ImxObject") -> None:
        """
        Extends the current ImxObject with another ImxObject.

        Args:
            imx_extension_object (ImxObject): The ImxObject to extend with.
        """

        imx_extension_object.properties = reindex_dict(
            sort_dict_by_sourceline(imx_extension_object.properties)
        )
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
            tag = parent_element.tag
            if isinstance(tag, str):
                return tag.removeprefix(namespace)
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
        if imx_file.root is None:
            raise ValueError(  # noqa: TRY003
                "IMX file root element is None. Cannot generate lookup tree."
            )
        entities = imx_file.root.findall(".//*[@puic]")
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
        entities = element.findall(".//*[@puic]")
        return cls._get_lookup_tree_from_element(entities, imx_file)
