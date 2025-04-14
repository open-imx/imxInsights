import numpy as np
from numpy.typing import NDArray
from shapely import LineString, Point

from imxInsights.utils.measure_3d.measureEnums import (
    ProjectionPointPosition,
    ProjectionStatus,
)
from imxInsights.utils.measure_3d.measureResult import MeasureResult


class MeasureLine:
    def __init__(
        self, line: list[list[float]] | NDArray[np.float64] | LineString
    ) -> None:
        self.shapely_line, self._line_array, self.is_3d = self._process_input(line)
        self._cum_lengths_2d, self._cum_lengths_3d = (
            self._compute_cumulative_distances()
        )

    @staticmethod
    def _process_input(
        line: list[list[float]] | NDArray[np.float64] | LineString,
    ) -> tuple[LineString, NDArray[np.float64], bool]:
        """Validate and process input line into a 3D array and LineString."""
        if isinstance(line, LineString):
            shapely_line = line
            coords_array = np.array(list(line.coords), dtype=float)
        else:
            # assume it's raw coordinates (list or array) and create a LineString
            shapely_line = LineString(line)
            coords_array = np.asarray(line, dtype=float)

        MeasureLine._validate_line_array(coords_array)
        coords_array, is_3d = MeasureLine._standardize_to_3d(coords_array)
        return shapely_line, coords_array, is_3d

    @staticmethod
    def _validate_line_array(coords_array: NDArray[np.float64]) -> None:
        """Ensure the coordinates array is a 2D array with 2 or 3 columns."""
        if coords_array.ndim != 2 or coords_array.shape[1] not in (2, 3):
            raise ValueError(
                "Input line must be a 2D array with shape (N, 2) or (N, 3)."
            )

    @staticmethod
    def _standardize_to_3d(
        coords_array: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], bool]:
        """Ensure the coordinates array has 3 columns (x, y, z)."""

        # If input only has 2 columns (2D points), add a 3rd column with zeros for Z values
        if coords_array.shape[1] == 2:
            coords_array = np.column_stack(
                (coords_array, np.zeros(coords_array.shape[0]))
            )
            return coords_array, False

        return coords_array, True

    def _compute_cumulative_distances(
        self,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64] | None]:
        """Compute cumulative 2D and 3D distances along the line."""

        # Compute 2D segment lengths (using only x and y)
        seg_lengths_2d = self._compute_segment_lengths(self._line_array[:, :2])

        # Cumulative sum of 2D segment lengths, starting with 0
        cum_lengths_2d = np.insert(np.cumsum(seg_lengths_2d), 0, 0)

        cum_lengths_3d = None
        if self.is_3d:
            # If the line is 3D, compute 3D segment lengths
            seg_lengths_3d = self._compute_segment_lengths(self._line_array)

            # Cumulative sum of 3D segment lengths, starting with 0
            cum_lengths_3d = np.insert(np.cumsum(seg_lengths_3d), 0, 0)

        return cum_lengths_2d, cum_lengths_3d

    @staticmethod
    def _compute_segment_lengths(coords: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute lengths of segments between consecutive coordinates."""

        # Calculate the difference between each pair of consecutive coordinates
        # This gives vectors pointing from one point to the next
        diffs = np.diff(coords, axis=0)

        # Compute the Euclidean norm (length) of each difference vector
        # This gives the segment length between each consecutive pair
        lengths = np.linalg.norm(diffs, axis=1)

        return lengths

    def project(
        self, point: list[float] | NDArray[np.float64] | Point
    ) -> MeasureResult:
        # TODO: if not 3d we should only have input 3d if 3d!
        # TODO: add threshold_distance option

        point = self._validate_and_process_point(point)

        # Use shapely project as it haz tested perpendicular projection and interpolated z it return 2d measures!
        input_point_shapely_2d, proj_measure_shapely_2d, proj_point_shapely = (
            self._shapely_projection(point)
        )

        seg_index, prev_point_3d, next_point_3d = self._get_segment_data(
            proj_measure_shapely_2d
        )

        proj_point_3d = np.array(*proj_point_shapely.coords)
        measure_3d = self._get_3d_measure(proj_point_3d, prev_point_3d, seg_index)

        is_perpendicular = self._is_perpendicular_projection(input_point_shapely_2d)
        side_of_line, projection_angle = self._get_projection_status(
            is_perpendicular,
            point,
            prev_point_3d,
            next_point_3d,
            proj_measure_shapely_2d,
        )

        shapely_projection = Point(proj_point_3d)

        # TODO: add distance to line in 2d and 3d
        # TODO: add precision rounding (just cut it!)
        # TODO: add confidence score based on over and undershoot and angle or perpendicular
        # TODO: add on line azimuth from functional direction
        # TODO: add on line azimuth from azimuth
        return MeasureResult(
            point_to_project=Point(point),
            projection_line=self.shapely_line,
            projected_point=shapely_projection,
            measure_2d=proj_measure_shapely_2d,
            measure_3d=measure_3d,
            side=side_of_line,
            projection_status=projection_angle,
        )

    @staticmethod
    def _validate_and_process_point(point: Point | list | np.ndarray) -> np.ndarray:
        """Ensure point is a 3D NumPy array."""
        if isinstance(point, Point):
            point = np.array(point.coords[0], dtype=float)
        else:
            # assume it's a raw list/array and convert it to a NumPy array
            point = np.asarray(point, dtype=float)

        # Validate that the point is a 1D array with 2 or 3 elements
        if point.ndim != 1 or point.shape[0] not in (2, 3):
            raise ValueError("Point must be a 1D array with 2 or 3 elements.")

        # If the point is 2D (only x and y), append a 0.0 for the z-coordinate
        if point.shape[0] == 2:
            point = np.append(point, 0.0)

        return point

    def _shapely_projection(self, point: np.ndarray) -> tuple[Point, float, Point]:
        # we should make the point 2d before projection
        input_point_shapely_2d = Point(float(point[0]), float(point[1]))
        # measures in shapely are in 2d, in most GIS applications the z is 'along the ride'
        proj_measure_shapely_2d = self.shapely_line.project(input_point_shapely_2d)

        # we forced 2d lines to z =0 so we allways get a 3d point
        proj_point_shapely = self.shapely_line.interpolate(proj_measure_shapely_2d)

        return input_point_shapely_2d, proj_measure_shapely_2d, proj_point_shapely

    def _get_segment_data(self, proj_measure_shapely: float):
        # shapely return a 2d measure, so we should use 2d length!
        seg_index = (
            np.searchsorted(self._cum_lengths_2d, proj_measure_shapely, side="right")
            - 1
        )
        seg_index = np.int64(min(max(int(seg_index), 0), len(self._cum_lengths_2d) - 2))
        prev_point_3d = self._line_array[seg_index]
        next_point_3d = self._line_array[seg_index + 1]
        return seg_index, prev_point_3d, next_point_3d

    def _get_projection_status(
        self,
        is_perpendicular: bool,
        point: np.ndarray,
        prev_point_3d: np.ndarray,
        next_point_3d: np.ndarray,
        proj_measure_shapely: float,
    ) -> tuple[ProjectionPointPosition, ProjectionStatus]:
        side_of_line = ProjectionPointPosition.UNDEFINED

        if is_perpendicular:
            side_of_line = self._determine_side(
                Point(point), Point(prev_point_3d[:2]), Point(next_point_3d[:2])
            )
            projection_angle = ProjectionStatus.PERPENDICULAR
        elif proj_measure_shapely == 0:
            # if not perpendicular and 0 length we assume its undershooting the line
            projection_angle = ProjectionStatus.UNDERSHOOT
        elif proj_measure_shapely == self.shapely_line.length:
            # if not perpendicular and length max we assume its overshooting the line
            projection_angle = ProjectionStatus.OVERSHOOT
        else:
            # we cant reverse point by projecting on measure and offset!

            # TODO: calculate angle so we can use it to recreate input point
            side_of_line = self._determine_side(
                Point(point), Point(prev_point_3d[:2]), Point(next_point_3d[:2])
            )
            projection_angle = ProjectionStatus.ANGLE

        return side_of_line, projection_angle

    def _get_projected_z(
        self, seg_index, proj_measure_shapely, prev_point_3d, next_point_3d
    ) -> float:
        seg_length = (
            self._cum_lengths_2d[seg_index + 1] - self._cum_lengths_2d[seg_index]
        )
        interpolation_factor_t = (
            0.0
            if seg_length == 0
            else (proj_measure_shapely - self._cum_lengths_2d[seg_index]) / seg_length
        )
        proj_z = prev_point_3d[2] + interpolation_factor_t * (
            next_point_3d[2] - prev_point_3d[2]
        )
        return proj_z

    def _get_3d_measure(self, proj_point_3d, prev_point_3d, seg_index) -> float | None:
        measure_3d = None
        if self.is_3d:
            # Calculate 3D distance along the segment
            d_segment = np.linalg.norm(proj_point_3d - prev_point_3d)
            # Total 3D distance
            if self._cum_lengths_3d is not None:
                measure_3d = self._cum_lengths_3d[seg_index] + d_segment
            else:
                # Decide what should happen if it's None!
                measure_3d = None
            # measure_3d = self._cum_lengths_3d[seg_index] + d_segment
        return measure_3d

    @staticmethod
    def _determine_side(
        point: Point, segment_start: Point, segment_end: Point
    ) -> ProjectionPointPosition:
        delta_x = segment_end.x - segment_start.x
        delta_y = segment_end.y - segment_start.y

        # Compute the cross product (2D determinant)
        cross = delta_x * (point.y - segment_start.y) - delta_y * (
            point.x - segment_start.x
        )

        if cross > 0:
            return ProjectionPointPosition.LEFT
        elif cross < 0:
            return ProjectionPointPosition.RIGHT
        else:
            return ProjectionPointPosition.ON_LINE

    def _is_perpendicular_projection(self, point: Point, tol: float = 1e-7) -> bool:
        # Project the point onto the line.
        proj_distance = self.shapely_line.project(point)
        proj_point = self.shapely_line.interpolate(proj_distance)

        # Identify the segment containing the projection.
        coords = list(self.shapely_line.coords)
        cum_distance = 0.0
        segment = None

        # TODO: reduce for looping its expansive
        for i in range(len(coords) - 1):
            seg_start = coords[i]
            seg_end = coords[i + 1]
            seg_line = LineString([seg_start, seg_end])
            seg_length = seg_line.length
            if cum_distance <= proj_distance <= cum_distance + seg_length:
                segment = (seg_start, seg_end)
                break
            cum_distance += seg_length

        if segment is None:
            raise ValueError("Projection did not fall on any segment of the line.")

        # Compute the direction vector of the segment in 2D.
        seg_start, seg_end = segment
        seg_start_2d = np.array(seg_start)[:2]
        seg_end_2d = np.array(seg_end)[:2]
        seg_vec_2d = seg_end_2d - seg_start_2d

        norm_seg = np.linalg.norm(seg_vec_2d)
        if norm_seg == 0:
            raise ValueError("Encountered a segment with zero length.")
        seg_unit = seg_vec_2d / norm_seg

        # Compute the vector from the projected point to the original point in 2D.
        pt_coords_2d = np.array(point.coords[0])[:2]
        proj_coords_2d = np.array(proj_point.coords[0])[:2]
        pt_vec = pt_coords_2d - proj_coords_2d

        # Check for orthogonality using the dot product.
        dot_product = np.dot(seg_unit, pt_vec)
        return abs(dot_product) < tol
