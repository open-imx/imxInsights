from lxml.etree import _Element as Element


class ImxContainerFileReference:
    """Represents a file reference."""

    def __init__(self):
        self._parent_document_name: str | None = None
        self._parent_hashcode: str | None = None

    @property
    def parent_document_name(self) -> str | None:
        """
        The name of the parent document.

        Returns:
             The name of the reference file.
        """
        return self._parent_document_name

    @property
    def parent_hashcode(self) -> str | None:
        """
        The hashcode of the parent document.

        Returns:
             The hash of the reference file.
        """
        return self._parent_hashcode

    @classmethod
    def from_element(cls, element: Element) -> "ImxContainerFileReference":
        self = cls()
        self._parent_hashcode = element.get("parentHashcode", "")
        self._parent_document_name = element.get("parentDocumentName", "")

        return self
