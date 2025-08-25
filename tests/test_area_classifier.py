import pytest
from dataclasses import dataclass
from typing import Iterable

from shapely.affinity import translate
from shapely.geometry import Point, Polygon
from shapely.geometry import base as shapely_base

from imxInsights.utils.areaClassifier import AreaClassifier, AreaLike


@dataclass(frozen=True)
class Area(AreaLike):
    name: str | None
    shapely: shapely_base.BaseGeometry


@pytest.fixture
def simple_areas() -> list[Area]:
    # Square A centered at (0,0): [-1,1] x [-1,1]
    square_a = Polygon([(-1, -1), (-1, 1), (1, 1), (1, -1)])
    # Square B translated to the right: x in [1,3], y in [-1,1]
    square_b = translate(square_a, xoff=2, yoff=0)
    return [Area("A", square_a), Area("B", square_b)]


@pytest.fixture
def classifier(simple_areas: Iterable[Area]) -> AreaClassifier[Area]:
    return AreaClassifier(simple_areas)



def idxs(hits) -> set[int]:
    """Return the set of area_index values from hits (order-agnostic)."""
    return {h.area_index for h in hits}


def names(hits) -> set[str | None]:
    return {h.area.name for h in hits}


def test_classify_with_raw_shapely_geometry_within(classifier: AreaClassifier[Area]):
    p = Point(0, 0)
    hits = classifier.classify(p, relation="within")
    assert len(hits) == 1
    h = hits[0]
    assert h.area_index in (0, 1)
    assert names(hits) == {"A"}
    assert h.relation == "within"


def test_classify_with_object_having_geometry_attr(classifier: AreaClassifier[Area]):
    class Obj:
        def __init__(self, geom):
            self.geometry = geom

    o = Obj(Point(2, 0))
    hits = classifier.classify(o, relation="within")
    assert len(hits) == 1
    assert names(hits) == {"B"}


def test_classify_with_custom_geometry_getter(classifier: AreaClassifier[Area]):
    payload = {"x": 2.0, "y": 0.0}

    def getter(d) -> shapely_base.BaseGeometry:
        return Point(d["x"], d["y"])

    hits = classifier.classify(payload, relation="within", geometry_getter=getter)
    assert len(hits) == 1
    assert names(hits) == {"B"}


@pytest.mark.parametrize(
    "relation, point, expected_names",
    [
        ("within", Point(0, 0), {"A"}),
        ("intersects", Point(0, 0), {"A"}),
        ("within", Point(2, 0), {"B"}),
        ("intersects", Point(2, 0), {"B"}),
    ],
)
def test_relations(classifier: AreaClassifier[Area], relation, point, expected_names):
    hits = classifier.classify(point, relation=relation)
    tester = names(hits)
    assert tester == expected_names


def test_classify_many_mixed_inputs(classifier: AreaClassifier[Area]):
    objs = [
        Point(0, 0),     # in A
        Point(2, 0),     # in B
        Point(10, 10),   # in none
    ]
    results = classifier.classify_many(objs, relation="within")
    assert [len(r) for r in results] == [1, 1, 0]
    assert names(results[0]) == {"A"}
    assert names(results[1]) == {"B"}


def test_classify_many_with_geometry_getter(classifier: AreaClassifier[Area]):
    data = [{"pt": (0.0, 0.0)}, {"pt": (2.0, 0.0)}, {"pt": (10.0, 10.0)}]

    def getter(d) -> shapely_base.BaseGeometry:
        x, y = d["pt"]
        return Point(x, y)

    results = classifier.classify_many(data, relation="within", geometry_getter=getter)
    assert [len(r) for r in results] == [1, 1, 0]
    assert names(results[0]) == {"A"}
    assert names(results[1]) == {"B"}



def test_flags_by_name_true_false(classifier: AreaClassifier[Area]):
    p = Point(0, 0)  # in A
    flags = classifier.flags_by_name(p, relation="within")
    assert flags["A"] is True
    assert flags["B"] is False


def test_flags_by_name_no_hits(classifier: AreaClassifier[Area]):
    p = Point(10, 10)  # in none
    flags = classifier.flags_by_name(p, relation="within")
    assert flags["A"] is False
    assert flags["B"] is False


def test_empty_areas_classify_returns_empty():
    empty_classifier = AreaClassifier[Area]([])
    assert empty_classifier.classify(Point(0, 0)) == []


def test_empty_areas_classify_many_returns_lists_of_empty():
    empty_classifier = AreaClassifier[Area]([])
    objs = [Point(0, 0), Point(1, 1)]
    results = empty_classifier.classify_many(objs)
    assert results == [[], []]


def test_object_without_geometry_raises(classifier: AreaClassifier[Area]):
    class Bad:
        pass

    with pytest.raises(AttributeError):
        classifier.classify(Bad())
