from copy import deepcopy

from imxInsights.compare.compareMultiRepo import ImxCompareMultiRepo
from imxInsights.repo.imxRepo import ImxRepo
from imxInsights.repo.tree.imxMultiObjectTree import MultiObjectTree


class ImxMultiRepo:
    """
    Represents a collection of ImxContainers.

    Attributes:
        containers: A list of ImxContainers.

    Args:
        containers: A list of ImxContainers.
        version_safe: If True, ensures all containers have the same IMX version.

    Raises:
        ValueError: If version_safe is True and containers have different IMX versions.
    """

    def __init__(self, containers: list[ImxRepo], version_safe: bool = True):
        if version_safe:
            versions = [item.imx_version for item in containers]
            if not all(x == versions[0] for x in versions):
                # todo: make IMX error
                raise ValueError(  # noqa TRY003
                    "Containers should have same imx version, use version_safe to explicit ignore versions"
                )

        # this will copy the element not the references
        containers = deepcopy(containers)
        self.containers: list[ImxRepo] = [item for item in containers]
        self.container_order: tuple[str, ...] = tuple(
            [item.container_id for item in self.containers]
        )
        self._tree: MultiObjectTree = MultiObjectTree()
        self._merge_containers(self.containers)

    @staticmethod
    def _merge_tree(source_tree, destination_tree):
        """
        Merge two tree structures.

        Args:
            source_tree: The source tree to merge.
            destination_tree: The destination tree to merge into.
        """
        for key, value in source_tree.items():
            if key in destination_tree:
                destination_tree[key].extend(value)
            else:
                destination_tree[key] = list(value)

    @staticmethod
    def _remove_tree(source_tree, destination_tree):
        """
        Remove items from a tree structure.

        Args:
            source_tree: The source tree containing items to remove.
            destination_tree: The destination tree to remove items from.
        """
        for key, value in source_tree.items():
            if key in destination_tree:
                destination_tree[key] = [
                    item for item in destination_tree[key] if item not in value
                ]

    def _merge_containers(self, containers: list[ImxRepo]):
        """
        Merge the tree structures of multiple containers.

        Args:
            containers (list[ImxRepo]): The list of containers to merge.
        """
        for container in containers:
            self._merge_tree(container._tree.tree_dict, self._tree.tree_dict)
            self._merge_tree(
                container._tree.build_extensions.exceptions,
                self._tree.build_extensions.exceptions,
            )
        self._tree.update_keys()

    def add_container(self, container: ImxRepo):
        """
        Add an ImxContainer to the MultiContainer.

        Args:
            container (ImxRepo): The container to add.
        """
        container = deepcopy(container)
        self.containers.append(container)
        self._merge_tree(container._tree.tree_dict, self._tree.tree_dict)
        self._merge_tree(
            container._tree.build_extensions.exceptions,
            self._tree.build_extensions.exceptions,
        )

    def remove_container(self, container: ImxRepo):
        """
        Remove an ImxContainer from the MultiContainer.

        Args:
            container (ImxRepo): The container to remove.
        """
        self.containers.remove(container)
        self._remove_tree(container._tree.tree_dict, self._tree.tree_dict)
        self._remove_tree(
            container._tree.build_extensions.exceptions,
            self._tree.build_extensions.exceptions,
        )

    def compare(self) -> ImxCompareMultiRepo:
        """Returns the compair of the repository

        returns:
            A ImxCompareMultiRepo object
        """
        return ImxCompareMultiRepo.from_multi_repo(
            self._tree, self.container_order, self.containers
        )
