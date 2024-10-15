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
            The Shapely Point object.

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
            A Shapely LineString object.

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

        TODO:
            - support donuts

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
