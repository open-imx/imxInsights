from shapely.geometry import LineString, Point

from imxInsights.utils.measure_3d.measureCalculator import MeasureLine


def test_point_projection(load_test_features):
    print()
    for feature_data in load_test_features:
        description = feature_data["properties"]["description"]

        point_to_project = feature_data["geometry"]["coordinates"]
        line_coords = feature_data["properties"]["projection_line"]

        line = LineString(line_coords)
        measure_line = MeasureLine(line)
        point = Point(point_to_project)
        projection_result = measure_line.project(point)

        assert projection_result is not None, f"Projectie mislukt voor {description}"

        results = feature_data["properties"]
        assert f"{projection_result.projected_point}" == results["result_point"], f"failed projected point :{description}"
        assert f"{projection_result.measure_3d}" == results["result_measure_3d"], f"failed 3d measure :{description}"
        assert f"{projection_result.measure_2d}" == results["result_measure_2d"], f"failed 2d measure :{description}"
        assert f"{projection_result.side}" == results["ProjectionPointPosition"], f"failed side of line :{description}"
        assert f"{projection_result.projection_status}" == results["ProjectionStatus"], f"failed projection status :{description}"

        print(f"✅ {description}: Projectie succesvol")
