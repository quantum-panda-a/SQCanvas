from shapely.geometry import Polygon

from qcanvas.shapes.store import ShapeRecord, ShapeStore


def test_shape_record():
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    rec = ShapeRecord(
        component="Q1",
        label="metal",
        geometry=poly,
        layer=2,
        subtract=False,
        helper=False,
        kind="poly",
        width=None,
        metadata={"custom": 123},
    )
    assert rec.component == "Q1"
    assert rec.label == "metal"
    assert rec.layer == 2
    assert rec.metadata["custom"] == 123


def test_shape_store():
    store = ShapeStore()
    assert store.is_empty()
    assert len(store) == 0
    assert store.bounds() == (0.0, 0.0, 0.0, 0.0)

    p1 = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    p2 = Polygon([(3, 3), (5, 3), (5, 5), (3, 5)])
    helper_poly = Polygon([(10, 10), (12, 10), (12, 12), (10, 12)])

    r1 = ShapeRecord("Q1", "metal", p1, layer=1)
    r2 = ShapeRecord("Q2", "cutout", p2, layer=2, subtract=True)
    r3 = ShapeRecord("Q1", "refpoint", helper_poly, layer=1, helper=True)

    store.add(r1)
    store.add_many([r2, r3])

    assert len(store) == 3
    assert not store.is_empty()
    assert "3 records" in repr(store)
    assert list(store) == [r1, r2, r3]
    assert store.as_records() == [r1, r2, r3]

    assert store.components() == ["Q1", "Q2"]
    assert store.layers() == [1, 2]

    # Helper geometries are ignored in bounds()
    minx, miny, maxx, maxy = store.bounds()
    assert (minx, miny, maxx, maxy) == (0.0, 0.0, 5.0, 5.0)

    # Filter
    assert store.filter(component="Q1") == [r1, r3]
    assert store.filter(layer=2) == [r2]
    assert store.filter(subtract=True) == [r2]
    assert store.filter(helper=True) == [r3]
    assert store.by_component("Q2") == [r2]
    assert store.by_layer(1) == [r1, r3]

    # Removal
    removed = store.remove(label="refpoint")
    assert removed == 1
    assert len(store) == 2

    store.clear()
    assert store.is_empty()
