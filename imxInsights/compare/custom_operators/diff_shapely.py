from deepdiff import DeepDiff  # type: ignore
from deepdiff.model import DiffLevel  # type: ignore
from deepdiff.operator import BaseOperator  # type: ignore
from shapely import LineString, Point
from shapely.geometry.base import BaseGeometry


class ShapelyPointDiffer(BaseOperator):
    """
    Custom DeepDiff operator for comparing Shapely Point objects and
    reporting their differences in coordinates.
    """

    def __init__(self, regex_paths: list[str]):
        super().__init__(regex_paths)

    def give_up_diffing(self, level: DiffLevel, diff_instance: DeepDiff) -> bool:
        """
        Compares two Shapely Point objects and reports differences in their coordinates.

        Args:
            level: The comparison level containing the two Point objects to compare.
            diff_instance: The instance of DeepDiff used to report the differences.

        Returns:
            bool: True if the comparison is completed and differences are reported.
        """
        if level.t1 is None and level.t2 is not None:
            diff_instance.custom_report_result(
                "type_changes",
                level,
            )
            return True
        elif level.t1 is not None and level.t2 is None:
            diff_instance.custom_report_result(
                "type_changes",
                level,
            )
            return True
        elif level.t1 == level.t2:
            return True

        p1: Point = Point(level.t1.split(",")) if level.t1 else Point()
        p2: Point = Point(level.t2.split(",")) if level.t2 else Point()
        is_changed: bool = False

        # Check if XY coordinates are different
        xy_distance: float = self._calculate_xy_distance(p1, p2)
        if self._is_xy_different(xy_distance):
            is_changed = True

        # Check if Z coordinates are different
        z_distance: float | str = self._compare_z_coordinates(p1, p2)
        if self._is_z_different(z_distance):
            is_changed = True

        # Report results if changes are detected
        if is_changed:
            almost_equal: bool = self._check_almost_equal(p1, p2)
            self._report_differences(
                diff_instance, level, almost_equal, xy_distance, z_distance
            )

        return True

    def _calculate_xy_distance(self, p1: Point, p2: Point) -> float:
        """Calculate the planar XY distance between two points."""
        return p1.distance(p2)

    def _is_xy_different(self, xy_distance: float) -> bool:
        """Check if the XY distance is greater than zero."""
        return xy_distance > 0.0

    def _compare_z_coordinates(self, p1: Point, p2: Point) -> float | str:
        """Compare Z coordinates of two points and return the Z distance or status."""
        # todo: make literals for string values
        if p1.has_z and p2.has_z:
            z_distance: float = p2.z - p1.z
            return z_distance if abs(z_distance) > 0.0 else "no change in z"
        elif p1.has_z:
            return "removed"
        elif p2.has_z:
            return "added"
        return "no z"

    def _is_z_different(self, z_distance: float | str) -> bool:
        """Check if the Z distance indicates a difference."""
        return z_distance != "no z"

    def _check_almost_equal(self, p1: Point, p2: Point) -> bool:
        """Check if the two points are almost equal."""
        return p1.equals_exact(p2, 1e-6)

    def _report_differences(
        self,
        diff_instance: DeepDiff,
        level: DiffLevel,
        almost_equal: bool,
        xy_distance: float,
        z_distance: float | str,
    ) -> None:
        """Report the detected differences."""
        diff_instance.custom_report_result("values_changed", level)
        diff_instance.custom_report_result(
            "diff_analyse",
            level,
            {
                "type": "ShapelyPointDiffer",
                "point_almost_equal": almost_equal,
                "point_xy_distance": round(xy_distance, 3),
                "point_z_distance": z_distance
                if isinstance(z_distance, str)
                else round(z_distance, 4),
                "display": f"almost_equal: {almost_equal}\nplanar distance: {round(xy_distance, 3)}\nz_distance: {z_distance if isinstance(z_distance, str) else round(z_distance, 4)}",
            },
        )


class ShapelyLineDiffer(BaseOperator):
    """Deepdiff custom Shapely LineString differ."""

    def __init__(self, regex_paths: list[str]):
        super().__init__(regex_paths)

    def give_up_diffing(self, level: DiffLevel, diff_instance: DeepDiff) -> bool:
        """
        Compare two Shapely LineString objects and report differences.

        Args:
            level: The current comparison level with t1 and t2 representing LineString objects.
            diff_instance: DeepDiff instance to report the differences.

        Returns:
            bool: Always returns True after diffing and reporting the result.
        """

        if level.t1 is None and level.t2 is not None:
            diff_instance.custom_report_result(
                "type_changes",
                level,
            )
            return True
        elif level.t1 is not None and level.t2 is None:
            diff_instance.custom_report_result(
                "type_changes",
                level,
            )
            return True
        elif level.t1 == level.t2:
            return True

        l1: LineString = (
            LineString(
                [tuple(map(float, item.split(","))) for item in level.t1.split(" ")]
            )
            if level.t1
            else LineString()
        )
        l2: LineString = (
            LineString(
                [tuple(map(float, item.split(","))) for item in level.t2.split(" ")]
            )
            if level.t2
            else LineString()
        )
        is_changed: bool = False

        # Check if lines are almost equal
        almost_equal: bool = self._check_almost_equal(l1, l2)
        if not almost_equal:
            is_changed = True

        # Perform buffer-based comparison
        intersection_over_union: float = self._compare_buffer_intersections(l1, l2)
        if intersection_over_union < 0.98:
            is_changed = True

        # Compare lengths and coordinates
        length_difference: float = self._compare_lengths(l1, l2)
        if length_difference > 0.0:
            is_changed = True

        coordinate_difference: int = self._compare_coordinates(l1, l2)
        if coordinate_difference != 0:
            is_changed = True

        # Compare Z-values if applicable
        z_difference: float | str = self._compare_z_coordinates(l1, l2)
        # todo: make literals for string values
        if z_difference != "no z" or z_difference != "no change in z":
            is_changed = True

        # Report differences if changes are detected
        if is_changed:
            self._report_differences(
                diff_instance,
                level,
                almost_equal,
                intersection_over_union,
                length_difference,
                coordinate_difference,
                z_difference,
            )

        return True

    def _check_almost_equal(self, l1: LineString, l2: LineString) -> bool:
        """Check if the two LineString geometries are almost equal."""
        return l1.equals_exact(l2, 1e-6)

    def _compare_buffer_intersections(self, l1: LineString, l2: LineString) -> float:
        """
        Compare the buffer intersections of two LineStrings and return the Intersection-over-Union (IoU).
        """
        line_1_buffer: BaseGeometry = l1.buffer(1)
        line_2_buffer: BaseGeometry = l2.buffer(1)

        union_area: float = line_1_buffer.union(line_2_buffer).area
        overlap_area: float = line_1_buffer.intersection(line_2_buffer).area

        return overlap_area / union_area if union_area != 0 else 0

    def _compare_lengths(self, l1: LineString, l2: LineString) -> float:
        """Compare the lengths of two LineStrings."""
        return abs(l1.length - l2.length)

    def _compare_coordinates(self, l1: LineString, l2: LineString) -> int:
        """Compare the number of coordinates in two LineStrings."""
        return len(l2.coords) - len(l1.coords)

    def _compare_z_coordinates(self, l1: LineString, l2: LineString) -> float | str:
        """Compare the Z coordinates of two LineStrings."""
        # todo: make literals for string values
        if l1.has_z and l2.has_z:
            max_z_difference = self._get_max_z_difference(l1, l2)
            return max_z_difference if max_z_difference != 0 else "no change in z"
        elif l1.has_z:
            return "removed"
        elif l2.has_z:
            return "added"
        return "no z"

    def _get_max_z_difference(self, l1: LineString, l2: LineString) -> float:
        """
        Calculate the maximum Z-coordinate difference between the two LineStrings.
        """
        max_distance = []
        for point in l1.coords:
            max_distance.append(self._calculate_z_distance(Point(point), l2))

        for point in l2.coords:
            max_distance.append(self._calculate_z_distance(Point(point), l1))

        return max(abs(d) for d in max_distance) if max_distance else 0

    def _calculate_z_distance(self, point: Point, line: LineString) -> float:
        """
        Calculate the Z-coordinate difference between a point and the closest point on a LineString.
        """
        measure = line.project(point)
        interpolated_point = line.interpolate(measure)
        return point.z - interpolated_point.z

    def _report_differences(
        self,
        diff_instance: DeepDiff,
        level: DiffLevel,
        almost_equal: bool,
        intersection_over_union: float,
        length_difference: float,
        coordinate_difference: int,
        z_difference: float | str,
    ) -> None:
        """Report the detected differences using DeepDiff."""
        diff_instance.custom_report_result("values_changed", level)
        diff_instance.custom_report_result(
            "diff_analyse",
            level,
            {
                "type": "ShapelyLineDiffer",
                "line_almost_equal": almost_equal,
                "intersection_over_union": round(intersection_over_union, 3),
                "line_planer_length_difference": round(length_difference, 3),
                "line_coordinate_difference": coordinate_difference,
                "line_max_z_distance": round(z_difference, 3)
                if isinstance(z_difference, float)
                else z_difference
                if isinstance(z_difference, str)
                else round(z_difference, 3),
                "display": f"almost_equal: {almost_equal}\nintersection over union: {round(intersection_over_union, 3)}\nplaner length difference: {round(length_difference, 3)}",
            },
        )
