import pyproj
from shapely.geometry import LineString, Point, Polygon


class ShapelyTransform:
    """A utility class to transform shapley objects between coordinate systems using pyproj."""

    rd = pyproj.CRS("EPSG:28992")
    wgs = pyproj.CRS("EPSG:4326")
    transformer_to_wgs = pyproj.Transformer.from_crs(rd, wgs)
    transformer_to_rd = pyproj.Transformer.from_crs(wgs, rd)

    @classmethod
    def rd_to_wgs(
        cls, shapely: Point | LineString | Polygon
    ) -> Point | LineString | Polygon:
        """
        Convert a Shapely geometry from RD (Rijksdriehoekstelsel) coordinates (EPSG:28992) to WGS84 coordinates (EPSG:4326).

        Args:
            shapely: A Shapely geometry in RD coordinates.

        Returns:
            A Shapely geometry in WGS84 coordinates.

        """
        if isinstance(shapely, Point):
            if shapely.has_z:
                return Point(
                    *cls.transformer_to_wgs.transform(shapely.x, shapely.y), shapely.z
                )
            return Point(*cls.transformer_to_wgs.transform(shapely.x, shapely.y))

        elif isinstance(shapely, LineString):
            if shapely.has_z:
                transformed_coords = cls.transformer_to_wgs.transform(*shapely.xy)
                return LineString(
                    zip(*transformed_coords, list([_[2] for _ in shapely.coords]))
                )
            return LineString(zip(*cls.transformer_to_wgs.transform(*shapely.xy)))

        elif isinstance(shapely, Polygon):
            if shapely.has_z:
                transformed_coords = cls.transformer_to_wgs.transform(
                    *shapely.exterior.xy
                )
                return Polygon(
                    zip(
                        *transformed_coords,
                        list([_[2] for _ in shapely.exterior.coords]),
                    )
                )
            return Polygon(zip(*cls.transformer_to_wgs.transform(*shapely.exterior.xy)))

        else:
            raise NotImplementedError(f"{shapely} not implemented")

    @classmethod
    def wgs_to_rd(
        cls, shapely: Point | LineString | Polygon
    ) -> Point | LineString | Polygon:
        """
        Convert a Shapely geometry from WGS84 coordinates (EPSG:4326) to RD (Rijksdriehoekstelsel) coordinates.

        Args:
            shapely: A Shapely geometry in WGS84 coordinates.

        Returns:
            A Shapely geometry in RD coordinates.

        """
        if isinstance(shapely, Point):
            if shapely.has_z:
                return Point(
                    *cls.transformer_to_rd.transform(shapely.x, shapely.y), shapely.z
                )
            return Point(*cls.transformer_to_rd.transform(shapely.x, shapely.y))

        elif isinstance(shapely, LineString):
            if shapely.has_z:
                transformed_coords = cls.transformer_to_rd.transform(*shapely.xy)
                return LineString(
                    zip(*transformed_coords, list([_[2] for _ in shapely.coords]))
                )
            return LineString(zip(*cls.transformer_to_rd.transform(*shapely.xy)))

        elif isinstance(shapely, Polygon):
            if shapely.has_z:
                transformed_coords = cls.transformer_to_rd.transform(
                    *shapely.exterior.xy
                )
                return Polygon(
                    zip(
                        *transformed_coords,
                        list([_[2] for _ in shapely.exterior.coords]),
                    )
                )
            return Polygon(zip(*cls.transformer_to_rd.transform(*shapely.exterior.xy)))

        else:
            raise NotImplementedError(f"{shapely} not implemented")
