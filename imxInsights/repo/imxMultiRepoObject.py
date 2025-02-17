from imxInsights.domain.imxObject import ImxObject


class ImxMultiRepoObject:
    def __init__(
        self, imx_objects: tuple[ImxObject | None, ...], container_order: list[str]
    ):
        self.imx_objects = imx_objects
        self.container_order: tuple[str, ...] = tuple(container_order)

    def get_by_container_id(self, container_id: str) -> ImxObject | None:
        """Retrieve the ImxObject for a specific container."""
        if container_id not in self.container_order:
            raise ValueError(f"container_id: {container_id} not present")

        container_index = self.container_order.index(container_id)
        return (
            self.imx_objects[container_index]
            if container_index < len(self.imx_objects)
            else None
        )

    @property
    def puic(self) -> str:
        return [_.puic for _ in self.imx_objects if _ is not None][0]

    def __iter__(self):
        for item in self.imx_objects:
            if item is not None:
                yield item

    def __repr__(self):
        return f"<MultiRepoImxObject {self.imx_objects} >"

    # def compare_list(self) -> list[ChangedImxObject]:
    #     return [
    #         result
    #         for idx in range(1, len(self.container_order))
    #         if (
    #             result := self.compare(
    #                 self.container_order[idx - 1], self.container_order[idx]
    #             )
    #         )
    #         is not None
    #     ]
    #
    # def compare(
    #     self, container_id_t1: str, container_id_t2: str
    # ) -> ChangedImxObject | None:
    #     t1 = self.get_by_container_id(container_id_t1)
    #     t2 = self.get_by_container_id(container_id_t2)
    #     if t1 or t2:
    #         return ChangedImxObject(
    #             t1=t1,
    #             t2=t2,
    #         )
    #     return None
