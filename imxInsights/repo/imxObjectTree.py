from collections import defaultdict
from collections.abc import Iterable
from itertools import chain

from lxml.etree import _Element as Element

from imxInsights.domain.imxObject import ImxObject
from imxInsights.exceptions.imxExceptions import ImxDuplicatedPuicsInContainer
from imxInsights.file.imxFile import ImxFile
from imxInsights.repo.builders.addChildren import add_children
from imxInsights.repo.builders.addRefs import add_refs
from imxInsights.repo.builders.buildExceptions import BuildExceptions
from imxInsights.repo.builders.buildRailConnections import build_rail_connections
from imxInsights.repo.builders.extendObjects import extend_objects


class ObjectTree:
    """
    Manages and constructs a tree of ImxObjects, allowing for extensions, validation, and various operations on the tree.

    Attributes:
        tree_dict (defaultdict[str, list[ImxObject]]): The dictionary representing the tree of ImxObjects.
        build_exceptions (BuildExceptions): Holds exceptions encountered during the build process.
    """

    def __init__(self):
        # todo: not private for easy debug, should be private, objects should return stuff
        self.tree_dict: defaultdict[str, list[ImxObject]] = defaultdict(list)
        self._keys: frozenset[str] = frozenset()
        self.build_exceptions: BuildExceptions = BuildExceptions()

    @property
    def keys(self) -> frozenset[str]:
        """
        Returns the set of keys currently in the tree dictionary.

        Returns:
            frozenset[str]: The set of keys in the tree dictionary.
        """
        return self._keys

    def update_keys(self) -> None:
        """
        Updates the set of keys in the tree dictionary.

        Marks for internal use.
        """
        self._keys = frozenset[str](key for key in self.tree_dict.keys())

    def add_imx_element(self, element: Element, imx_file: ImxFile, container_id: str):
        """
        Adds an ImxObject derived from an XML element to the tree.

        Marks for internal use.

        Args:
            element (Element): The XML element to be added.
            imx_file (ImxFile): The ImxFile associated with the element.
            container_id (str): The container ID to associate with the ImxObject.
        """
        tree_to_add = self._create_tree_dict(
            ImxObject.lookup_tree_from_element(element, imx_file), container_id
        )
        self._validate_and_build(tree_to_add, imx_file, element)

    def add_imx_file(self, imx_file: ImxFile, container_id: str) -> None:
        """
        Adds an ImxObject derived from an ImxFile to the tree.

        Marks for internal use.

        Args:
            imx_file (ImxFile): The ImxFile to be added.
            container_id (str): The container ID to associate with the ImxObject.
        """
        tree_to_add = self._create_tree_dict(
            ImxObject.lookup_tree_from_imx_file(imx_file), container_id
        )
        self._validate_and_build(tree_to_add, imx_file)

    def _validate_and_build(
        self,
        tree_to_add: defaultdict[str, list[ImxObject]],
        imx_file: ImxFile,
        element: Element | None = None,
    ):
        """
        Validates and builds the tree structure from the provided dictionary.

        Ensures no duplicate PUICs exist in the container and integrates the new tree into the current tree.

        Args:
            tree_to_add (defaultdict[str, list[ImxObject]]): The tree dictionary to be added.
            imx_file (ImxFile): The ImxFile associated with the objects.
            element (Element, optional): The XML element associated with the objects. Defaults to None.
        """
        duplicates = [k for (k, v) in tree_to_add.items() if len(v) > 1]
        if len(duplicates) != 0:
            for puic in duplicates:
                self.build_exceptions.add(ImxDuplicatedPuicsInContainer(), puic)

        for key, value in tree_to_add.items():
            if key not in self._keys:
                self.tree_dict[key] = value
            else:
                for item in value:
                    self.tree_dict[key].append(item)

        self.update_keys()

        extend_objects(self.tree_dict, self.build_exceptions, imx_file, element)
        add_children(self.tree_dict, self.find)
        build_rail_connections(self.get_by_types, self.find, self.build_exceptions)
        add_refs(self.tree_dict, self.find)

        # todo: classify area

    @staticmethod
    def _create_tree_dict(
        objects: Iterable[ImxObject], container_id: str
    ) -> defaultdict[str, list[ImxObject]]:
        """
        Creates a tree dictionary from a list of ImxObjects.

        Marks for internal use.

        Args:
            objects (Iterable[ImxObject]): The list of ImxObjects.
            container_id (str): The container ID to associate with the ImxObjects.

        Returns:
            defaultdict[str, list[ImxObject]]: The created tree dictionary.

        Raises:
            AssertionError: If multiple objects have the same PUIC.
        """

        result = defaultdict[str, list[ImxObject]](list)

        for o in objects:
            o.container_id = container_id
            result[o.puic].append(o)
        duplicated = [o for o in objects if len(result[o.puic]) != 1]
        assert (
            len(duplicated) == 0
        ), f"KeyError, multiple results for {[item.puic for item in duplicated]}"
        return result

    def duplicates(self) -> list[str]:
        """
        Checks for duplicate PUICs in the tree.

        Returns:
            list[str]: The list of duplicate PUICs.
        """
        return [k for (k, v) in self.tree_dict.items() if len(v) > 1]

    def get_all(self) -> Iterable[ImxObject]:
        """
        Retrieves all objects in the tree, ensuring no duplicates.

        Returns:
            Iterable[ImxObject]: An iterable of all ImxObjects.

        Raises:
            ImxDuplicatedPuicsInContainer: If duplicate PUICs are found.
        """
        duplicates = self.duplicates()
        if len(duplicates) != 0:
            raise ImxDuplicatedPuicsInContainer(data=duplicates)
        return chain(*self.tree_dict.values())

    def find(self, key: str | ImxObject) -> ImxObject | None:
        """
        Finds an object in the tree by its key or ImxObject.

        Args:
            key (str | ImxObject): The key or ImxObject to find.

        Returns:
            ImxObject | None: The found ImxObject, or None if not found.

        Raises:
            AssertionError: If multiple objects are found for the given key.
        """
        if isinstance(key, ImxObject):
            key = key.puic

        if key not in self._keys:
            return None

        match = self.tree_dict[key]
        assert len(match) == 1, f"KeyError, multiple results for {key}"
        return match[0]

    def get_all_types(self) -> list[str]:
        """
        Retrieves all unique object types in the tree.

        Returns:
            list[str]: A list of all unique object types.
        """
        return list(set([item[0].tag for item in self.tree_dict.values()]))

    def get_by_types(self, object_types: list[str]) -> list[ImxObject]:
        """
        Retrieves objects of specified types from the tree.

        Args:
            object_types (list[str]): The list of object types to retrieve.

        Returns:
            list[ImxObject]: The list of matching ImxObjects.
        """
        return [
            item[0] for item in self.tree_dict.values() if item[0].tag in object_types
        ]

    def get_all_paths(self) -> list[str]:
        """
        Retrieves all unique object paths in the tree.

        Returns:
            list[str]: A list of all unique object paths.
        """
        return list(set([item[0].path for item in self.tree_dict.values()]))

    def get_by_paths(self, object_paths: list[str]) -> list[ImxObject]:
        """
        Retrieves objects of specified paths from the tree.

        Args:
            object_paths (list[str]): The list of object paths to retrieve.

        Returns:
            list[ImxObject]: The list of matching ImxObjects.
        """
        return [
            item[0] for item in self.tree_dict.values() if item[0].path in object_paths
        ]
