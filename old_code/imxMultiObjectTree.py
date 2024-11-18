# from collections.abc import Iterable
#
# from imxInsights.domain.imxObject import ImxObject
# from imxInsights.repo.tree.imxObjectTree import ObjectTree
#
#
# class MultiObjectTree(ObjectTree):
#     """
#     Represents a tree structure of multiple ImxObject lists.
#
#     Inherits from ObjectTree.
#
#     Attributes:
#         Inherits attributes from ObjectTree.
#     """
#
#     def __init__(self):
#         super().__init__()
#
#     def get_all(self) -> Iterable[list[ImxObject]]:  # type: ignore
#         """
#         Get an iterable of all ImxObjects in the tree.
#
#         Returns:
#             Iterable[ImxObject]: An iterable of all ImxObjects in the tree.
#         """
#         return list(self.tree_dict.values())
#
#     def find(self, key: str | ImxObject) -> list[ImxObject]:  # type: ignore
#         """
#         Find an ImxObject by key or by another ImxObject.
#
#         Args:
#             key (Union[str, ImxObject]): The key or ImxObject to search for.
#
#         Returns:
#             Optional[ImxObject]: The found ImxObject, or None if not found.
#         """
#         if isinstance(key, ImxObject):
#             key = key.puic
#
#         if key not in self._keys:
#             return []
#
#         match = self.tree_dict[key]
#         return match
#
#     def get_by_types(self, object_types: list[str]) -> list[list[ImxObject]]:  # type: ignore
#         """
#         Get all ImxObjects that match the specified types.
#
#         Args:
#             object_types (list[str]): The list of types to match against.
#
#         Returns:
#             list[list[ImxObject]]: A list of lists of ImxObjects matching the types.
#         """
#         return [
#             item
#             for item in self.tree_dict.values()
#             if any(sub_item.tag in object_types for sub_item in item)
#         ]
#
#     def get_by_paths(self, object_paths: list[str]) -> list[list[ImxObject]]:  # type: ignore
#         """
#         Get all ImxObjects that match the specified paths.
#
#         Args:
#             object_paths (list[str]): The list of paths to match against.
#
#         Returns:
#             list[list[ImxObject]]: A list of lists of ImxObjects matching the paths.
#         """
#         return [
#             item
#             for item in self.tree_dict.values()
#             if any(sub_item.path in object_paths for sub_item in item)
#         ]
