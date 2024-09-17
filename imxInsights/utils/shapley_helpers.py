import pyproj

# from lxml import etree as ET
from lxml.etree import _Element as Element
from shapely import LineString, Point, Polygon


class GmlShapleyFactory:
    @classmethod
    def gml_point_to_shapely(cls, gml_point_coordinates: str) -> Point:
        """
        Converts a GML point coordinate string to a Shapely Point object.

        Args:
            gml_point_coordinates (str): The GML point coordinate string in the format "(x,y)".

        Returns:
            (Shapely.Point): The Shapely Point object.

        """
        coordinates = [
            float(x)
            for x in gml_point_coordinates.replace("(", "")
            .replace(")", "")
            .replace("'", "")
            .replace(" ", "")
            .split(",")
        ]
        return Point(coordinates)

    @classmethod
    def gml_linestring_to_shapely(cls, gml_linestring_coordinates: str) -> LineString:
        """
        Converts a GML linestring coordinate string to a Shapely LineString object.

        Args:
            gml_linestring_coordinates (str): A string of GML linestring coordinates in "x,y" format separated by spaces.

        Returns:
            (Shapely.LineString): A Shapely LineString object.

        """
        return LineString(
            [
                tuple(map(float, x.split(",")))
                for x in gml_linestring_coordinates.split(" ")
            ]
        )

    @classmethod
    def gml_polygon_to_shapely(cls, gml_linestring_coordinates: str) -> Polygon:
        """
        Converts a GML polygon to a Shapely Polygon object.

        Args:
            gml_linestring_coordinates (str): A string containing the GML coordinates of the polygon.

        Returns:
            (Polygon): A Shapely Polygon object.

        """
        return Polygon(
            [
                tuple(map(float, x.split(",")))
                for x in gml_linestring_coordinates.split(" ")
            ]
        )

    @classmethod
    def shapley(cls, gml_element: Element):
        point = gml_element.find(".//{http://www.opengis.net/gml}Point")
        if point is not None:
            coordinates_element = point.find(
                ".//{http://www.opengis.net/gml}coordinates"
            )
            if coordinates_element is not None and coordinates_element.text is not None:
                return cls.gml_point_to_shapely(coordinates_element.text)

        linestring = gml_element.find(".//{http://www.opengis.net/gml}LineString")
        if linestring is not None:
            coordinates_element = linestring.find(
                ".//{http://www.opengis.net/gml}coordinates"
            )
            if coordinates_element is not None and coordinates_element.text is not None:
                return cls.gml_linestring_to_shapely(coordinates_element.text)

        polygon = gml_element.findall(".//{http://www.opengis.net/gml}Polygon")
        if len(polygon) == 1:
            coordinates_element = polygon[0].find(
                ".//{http://www.opengis.net/gml}coordinates"
            )
            if coordinates_element is not None and coordinates_element.text is not None:
                return cls.gml_polygon_to_shapely(coordinates_element.text)

        raise NotImplementedError(
            f"gml shapley generation for {gml_element.tag} not supported"
        )


class ShapelyTransform:
    """A utility class to transform between RD and WGS84 coordinate systems."""

    rd = pyproj.CRS("EPSG:28992")
    wgs = pyproj.CRS("EPSG:4326")
    transformer_to_wgs = pyproj.Transformer.from_crs(rd, wgs)
    transformer_to_rd = pyproj.Transformer.from_crs(wgs, rd)

    @classmethod
    def rd_to_wgs(
        cls, shapely: Point | LineString | Polygon
    ) -> Point | LineString | Polygon:
        """
        Convert a Shapely geometry from Dutch RD (Rijksdriehoekstelsel) coordinates (EPSG:28992) to WGS84 coordinates (EPSG:4326).

        Args:
            shapely (Union[Point, LineString, Polygon]): A Shapely geometry in Dutch RD coordinates.

        Returns:
            (Union[Point, LineString, Polygon]): A Shapely geometry in WGS84 coordinates.

        """
        return cls._convert(shapely, cls.transformer_to_wgs)

    @staticmethod
    def _convert(
        shapely: Point | LineString | Polygon, transformer: pyproj.Transformer
    ) -> Point | LineString | Polygon:
        if isinstance(shapely, Point):
            return Point(*reversed(transformer.transform(shapely.x, shapely.y)))

        elif isinstance(shapely, LineString):
            return LineString(zip(*reversed(transformer.transform(*shapely.coords.xy))))

        elif isinstance(shapely, Polygon):
            return LineString(
                zip(*reversed(transformer.transform(*shapely.exterior.coords.xy)))
            )
        else:
            return shapely


def reverse_line(shapely_polyline: LineString) -> LineString:
    """
    Reverses the order of coordinates in a Shapely LineString object.

    Args:
        shapely_polyline (LineString): The LineString object to reverse.

    Returns:
        (LineString): A new LineString object with the coordinates in reverse order.

    """
    return LineString(list(shapely_polyline.coords)[::-1])
