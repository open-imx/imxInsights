from dataclasses import dataclass

from lxml.etree import _Element as Element
from shapely import Polygon
from shapely.geometry import GeometryCollection, MultiPolygon

from imxInsights.utils.shapely.shapely_geojson import (
    CrsEnum,
    ShapelyGeoJsonFeature,
    ShapelyGeoJsonFeatureCollection,
)
from imxInsights.utils.shapely.shapely_gml import GmlShapelyFactory
from imxInsights.utils.shapely.shapely_transform import ShapelyTransform


@dataclass
class Area:
    name: str
    coordinates: str
    shapely: Polygon

    @staticmethod
    def from_element(element: Element, name: str | None = None) -> "Area":
        coordinates_element = element.find(".//{http://www.opengis.net/gml}coordinates")
        if coordinates_element is None or coordinates_element.text is None:
            raise ValueError("Coordinates element or its text content is missing.")  # noqa: TRY003

        coordinates = coordinates_element.text
        tag_str = str(element.tag)
        name_value = tag_str.split("}")[1] if not name else name

        return Area(
            name=name_value,
            coordinates=coordinates,
            shapely=Polygon(GmlShapelyFactory.parse_coordinates(coordinates)),
        )

    def as_geojson_feature(
        self,
        as_wgs: bool = True,
        extra_properties: dict | None = None,
    ) -> ShapelyGeoJsonFeature:
        geom = self.shapely
        if as_wgs:
            geom = ShapelyTransform.rd_to_wgs(geom)

        props = {"area": self.name}
        if extra_properties:
            props = props | extra_properties

        return ShapelyGeoJsonFeature([geom], properties=props)


@dataclass
class ImxAreas:
    user_area: Area | None = None
    work_area: Area | None = None
    context_area: Area | None = None

    @staticmethod
    def from_element(element: Element) -> "ImxAreas":
        self = ImxAreas()

        user_area = element.find(".//{http://www.prorail.nl/IMSpoor}UserArea")
        if user_area is not None:
            self.user_area = Area.from_element(user_area)

        work_area = element.find(".//{http://www.prorail.nl/IMSpoor}WorkArea")
        if work_area is not None:
            self.work_area = Area.from_element(work_area)

        context_area = element.find(".//{http://www.prorail.nl/IMSpoor}ContextArea")
        if context_area is not None:
            self.context_area = Area.from_element(context_area)

        return self

    @staticmethod
    def _fix(g):
        """Return a valid geometry; quick-fix invalid rings with buffer(0)."""
        if g is None:
            return None
        try:
            return g if g.is_valid else g.buffer(0)
        except Exception:
            return g

    @staticmethod
    def _explode_polys(g):
        """Extract polygon parts from any geometry for GeoJSON features."""
        if g is None:
            return []
        if isinstance(g, Polygon):
            return [g]
        if isinstance(g, MultiPolygon):
            return list(g.geoms)
        if isinstance(g, GeometryCollection):
            return [p for p in g.geoms if isinstance(p, Polygon)]
        return []

    @staticmethod
    def _feature(name: str, geoms: list, as_wgs: bool, props: dict | None):
        if not geoms:
            return None
        if as_wgs:
            geoms = [ShapelyTransform.rd_to_wgs(g) for g in geoms]
        properties = {"area": name}
        if props:
            properties |= props
        return ShapelyGeoJsonFeature(geoms, properties=properties)

    def get_geojson(
        self,
        as_wgs: bool = True,
        base_props: dict | None = None,
        user_props: dict | None = None,
        make_donuts: bool = True,
    ) -> ShapelyGeoJsonFeatureCollection:
        def _compact(d: dict | None) -> dict:
            return {k: v for k, v in (d or {}).items() if v is not None}

        base_props = _compact(base_props)
        user_props = _compact(user_props)

        u = self._fix(self.user_area.shapely) if self.user_area else None
        w = self._fix(self.work_area.shapely) if self.work_area else None
        c = self._fix(self.context_area.shapely) if self.context_area else None

        # boolean differences for donuts
        if make_donuts:
            w_cut = w.difference(u) if (w is not None and u is not None) else w
            c_cut = c.difference(w) if (c is not None and w is not None) else c
        else:
            w_cut, c_cut = w, c

        features = []

        # context, work, user for draw order
        if c_cut:
            cf = self._feature(
                name=(self.context_area.name if self.context_area else "ContextArea"),
                geoms=self._explode_polys(c_cut),
                as_wgs=as_wgs,
                props=base_props,
            )
            if cf:
                features.append(cf)

        if w_cut:
            wf = self._feature(
                name=(self.work_area.name if self.work_area else "WorkArea"),
                geoms=self._explode_polys(w_cut),
                as_wgs=as_wgs,
                props=base_props,
            )
            if wf:
                features.append(wf)

        if u is not None:
            uf = self._feature(
                name=(self.user_area.name if self.user_area else "UserArea"),
                geoms=self._explode_polys(u),
                as_wgs=as_wgs,
                props=(base_props | user_props),
            )
            if uf:
                features.append(uf)

        return ShapelyGeoJsonFeatureCollection(
            features, crs=CrsEnum.WGS84 if as_wgs else CrsEnum.RD_NEW_NAP
        )
