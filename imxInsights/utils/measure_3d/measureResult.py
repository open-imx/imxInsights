from dataclasses import dataclass

from shapely import LineString, Point

from imxInsights.utils.measure_3d.measureEnums import (
    ProjectionPointPosition,
    ProjectionStatus,
)
from imxInsights.utils.shapely.shapely_geojson import ShapelyGeoJsonFeature


@dataclass
class MeasureResult:
    point_to_project: Point
    projection_line: LineString
    projected_point: Point
    measure_2d: float
    measure_3d: float | None
    side: ProjectionPointPosition
    projection_status: ProjectionStatus

    def __repr__(self) -> str:
        return (
            f"MeasureResult("
            f"point_to_project={self.point_to_project}, "
            f"projected_point={self.projected_point}, "
            f"side={self.side}, "
            f"measure_2d={self.measure_2d:.3f}, "
            f"measure_3d={self.measure_3d}, "
            f"overshoot_undershoot={self.projection_status.value})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    def as_geojson_features(
        self, include_perpendicular: bool = True
    ) -> list[ShapelyGeoJsonFeature]:
        """Export measure results as GeoJSON features."""
        features = [
            self._input_point_feature(),
            self._projection_line_feature(),
            self._projected_point_feature(),
        ]

        if include_perpendicular:
            features.append(self._perpendicular_line_feature())

        return features

    def _projected_point_feature(self) -> ShapelyGeoJsonFeature:
        return ShapelyGeoJsonFeature(
            [self.projected_point],
            {
                "type": "projected_point",
                "measure_2d": self.measure_2d,
                "measure_3d": self.measure_3d,
                "side": self.side.value,
                "projection_status": self.projection_status.value,
            },
        )

    def _input_point_feature(self) -> ShapelyGeoJsonFeature:
        return ShapelyGeoJsonFeature([self.point_to_project], {"type": "input_point"})

    def _projection_line_feature(self) -> ShapelyGeoJsonFeature:
        return ShapelyGeoJsonFeature(
            [self.projection_line], {"type": "projection_line"}
        )

    def _perpendicular_line_feature(self) -> ShapelyGeoJsonFeature:
        return ShapelyGeoJsonFeature(
            [LineString([self.point_to_project, self.projected_point])],
            {"type": "perpendicular_line"},
        )
