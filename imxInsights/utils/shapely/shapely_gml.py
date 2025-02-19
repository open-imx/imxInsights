from lxml.etree import _Element as Element
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)


class GmlShapelyFactory:
    @staticmethod
    def parse_coordinates(coord_text: str):
        """Parses GML coordinate text into a list of (x, y) tuples."""
        return [tuple(map(float, x.split(","))) for x in coord_text.strip().split()]

    @classmethod
    def gml_point_to_shapely(cls, gml_coordinates: str) -> Point:
        return Point(cls.parse_coordinates(gml_coordinates)[0])

    @classmethod
    def gml_linestring_to_shapely(cls, gml_coordinates: str) -> LineString:
        return LineString(cls.parse_coordinates(gml_coordinates))

    @classmethod
    def gml_polygon_to_shapely(cls, gml_element: Element) -> Polygon:
        """Converts a GML polygon to a Shapely Polygon object, supporting holes."""
        outer_boundary = gml_element.find(
            ".//{http://www.opengis.net/gml}outerBoundaryIs//{http://www.opengis.net/gml}coordinates"
        )
        inner_boundaries = gml_element.findall(
            ".//{http://www.opengis.net/gml}innerBoundaryIs//{http://www.opengis.net/gml}coordinates"
        )

        if outer_boundary is None or outer_boundary.text is None:
            raise ValueError("Polygon must have an outer boundary")

        exterior = cls.parse_coordinates(outer_boundary.text)
        interiors = [
            cls.parse_coordinates(inner.text)
            for inner in inner_boundaries
            if inner.text
        ]

        return Polygon(exterior, interiors)

    @classmethod
    def gml_multipoint_to_shapely(cls, gml_element: Element) -> MultiPoint:
        points = [
            cls.gml_point_to_shapely(point.text)
            for point in gml_element.findall(
                ".//{http://www.opengis.net/gml}coordinates"
            )
            if point.text
        ]
        return MultiPoint(points)

    @classmethod
    def gml_multilinestring_to_shapely(cls, gml_element: Element) -> MultiLineString:
        lines = [
            cls.gml_linestring_to_shapely(line.text)
            for line in gml_element.findall(
                ".//{http://www.opengis.net/gml}coordinates"
            )
            if line.text
        ]
        return MultiLineString(lines)

    @classmethod
    def gml_multipolygon_to_shapely(cls, gml_element: Element) -> MultiPolygon:
        polygons = [
            cls.gml_polygon_to_shapely(polygon)
            for polygon in gml_element.findall(".//{http://www.opengis.net/gml}Polygon")
        ]
        return MultiPolygon(polygons)

    @classmethod
    def shapely(
        cls, gml_element: Element
    ) -> Point | LineString | Polygon | MultiPoint | MultiLineString | MultiPolygon:
        ns = "{http://www.opengis.net/gml}"

        if (point := gml_element.find(f".//{ns}Point")) is not None:
            coordinates = point.find(f".//{ns}coordinates")
            if coordinates is not None and coordinates.text:
                return cls.gml_point_to_shapely(coordinates.text)

        if (linestring := gml_element.find(f".//{ns}LineString")) is not None:
            coordinates = linestring.find(f".//{ns}coordinates")
            if coordinates is not None and coordinates.text:
                return cls.gml_linestring_to_shapely(coordinates.text)

        if (polygon := gml_element.find(f".//{ns}Polygon")) is not None:
            return cls.gml_polygon_to_shapely(polygon)

        if (multipoint := gml_element.find(f".//{ns}MultiPoint")) is not None:
            return cls.gml_multipoint_to_shapely(multipoint)

        if (multilinestring := gml_element.find(f".//{ns}MultiLineString")) is not None:
            return cls.gml_multilinestring_to_shapely(multilinestring)

        if (multipolygon := gml_element.find(f".//{ns}MultiPolygon")) is not None:
            return cls.gml_multipolygon_to_shapely(multipolygon)

        first_child = gml_element[0].tag if len(gml_element) > 0 else "Unknown"
        raise NotImplementedError(
            f"GML to Shapely conversion for {first_child!r} is not supported"
        )
