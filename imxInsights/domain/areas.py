from dataclasses import dataclass

from lxml.etree import _Element as Element
from shapely import Polygon

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

    def get_geojson(
        self,
        as_wgs: bool = True,
        base_props: dict | None = None,
        user_props: dict | None = None,
    ) -> ShapelyGeoJsonFeatureCollection:
        def _compact(d: dict | None) -> dict:
            return {k: v for k, v in (d or {}).items() if v is not None}

        base_props = _compact(base_props)
        user_props = _compact(user_props)

        features = []

        if self.user_area:
            props = base_props | user_props
            features.append(
                self.user_area.as_geojson_feature(as_wgs=as_wgs, extra_properties=props)
            )

        if self.work_area:
            features.append(
                self.work_area.as_geojson_feature(
                    as_wgs=as_wgs, extra_properties=base_props
                )
            )

        if self.context_area:
            features.append(
                self.context_area.as_geojson_feature(
                    as_wgs=as_wgs, extra_properties=base_props
                )
            )

        return ShapelyGeoJsonFeatureCollection(
            features, crs=CrsEnum.WGS84 if as_wgs else CrsEnum.RD_NEW_NAP
        )
