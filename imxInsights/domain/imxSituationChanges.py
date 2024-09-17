from dataclasses import dataclass

from lxml.etree import _Element as Element


@dataclass
class SituationChanges:
    created: list[str]
    updated: list[str]
    deleted: list[str]

    @staticmethod
    def from_element(element: Element):
        created_elem = element.find("Created")
        updated_elem = element.find("Updated")
        deleted_elem = element.find("Deleted")

        created = (
            created_elem.text.split()
            if created_elem is not None and created_elem.text
            else []
        )
        updated = (
            updated_elem.text.split()
            if updated_elem is not None and updated_elem.text
            else []
        )
        deleted = (
            deleted_elem.text.split()
            if deleted_elem is not None and deleted_elem.text
            else []
        )

        return SituationChanges(created, updated, deleted)
