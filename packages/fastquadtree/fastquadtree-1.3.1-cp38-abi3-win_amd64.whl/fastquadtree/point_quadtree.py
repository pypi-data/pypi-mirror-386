# point_quadtree.py
from __future__ import annotations

from typing import Any, Literal, Tuple, overload

from ._base_quadtree import Bounds, _BaseQuadTree
from ._item import Point, PointItem
from ._native import QuadTree as QuadTreeF32, QuadTreeF64, QuadTreeI32, QuadTreeI64

_IdCoord = Tuple[int, float, float]

DTYPE_MAP = {
    "f32": QuadTreeF32,
    "f64": QuadTreeF64,
    "i32": QuadTreeI32,
    "i64": QuadTreeI64,
}


class QuadTree(_BaseQuadTree[Point, _IdCoord, PointItem]):
    """
    Point version of the quadtree. All geometries are 2D points (x, y).
    High-level Python wrapper over the Rust quadtree engine.

    Performance characteristics:
        Inserts: average O(log n) <br>
        Rect queries: average O(log n + k) where k is matches returned <br>
        Nearest neighbor: average O(log n) <br>

    Thread-safety:
        Instances are not thread-safe. Use external synchronization if you
        mutate the same tree from multiple threads.

    Args:
        bounds: World bounds as (min_x, min_y, max_x, max_y).
        capacity: Max number of points per node before splitting.
        max_depth: Optional max tree depth. If omitted, engine decides.
        track_objects: Enable id <-> object mapping inside Python.
        dtype: Data type for coordinates and ids in the native engine. Default is 'f32'. Options are 'f32', 'f64', 'i32', 'i64'.

    Raises:
        ValueError: If parameters are invalid or inserts are out of bounds.
    """

    def __init__(
        self,
        bounds: Bounds,
        capacity: int,
        *,
        max_depth: int | None = None,
        track_objects: bool = False,
        dtype: str = "f32",
    ):
        super().__init__(
            bounds,
            capacity,
            max_depth=max_depth,
            track_objects=track_objects,
            dtype=dtype,
        )

    @overload
    def query(
        self, rect: Bounds, *, as_items: Literal[False] = ...
    ) -> list[_IdCoord]: ...
    @overload
    def query(self, rect: Bounds, *, as_items: Literal[True]) -> list[PointItem]: ...
    def query(
        self, rect: Bounds, *, as_items: bool = False
    ) -> list[PointItem] | list[_IdCoord]:
        """
        Return all points inside an axis-aligned rectangle.

        Args:
            rect: Query rectangle as (min_x, min_y, max_x, max_y).
            as_items: If True, return Item wrappers. If False, return raw tuples.

        Returns:
            If as_items is False: list of (id, x, y) tuples.
            If as_items is True: list of Item objects.

        Example:
            ```python
            results = qt.query((10.0, 10.0, 20.0, 20.0), as_items=True)
            for item in results:
                print(f"Found point id={item.id_} at {item.geom} with obj={item.obj}")
            ```
        """
        if not as_items:
            return self._native.query(rect)
        if self._store is None:
            raise ValueError("Cannot return results as items with track_objects=False")
        return self._store.get_many_by_ids(self._native.query_ids(rect))

    @overload
    def nearest_neighbor(
        self, xy: Point, *, as_item: Literal[False] = ...
    ) -> _IdCoord | None: ...
    @overload
    def nearest_neighbor(
        self, xy: Point, *, as_item: Literal[True]
    ) -> PointItem | None: ...
    def nearest_neighbor(
        self, xy: Point, *, as_item: bool = False
    ) -> PointItem | _IdCoord | None:
        """
        Return the single nearest neighbor to the query point.

        Args:
            xy: Query point (x, y).
            as_item: If True, return Item. If False, return (id, x, y).

        Returns:
            The nearest neighbor or None if the tree is empty.
        """
        t = self._native.nearest_neighbor(xy)
        if t is None or not as_item:
            return t
        if self._store is None:
            raise ValueError("Cannot return result as item with track_objects=False")
        id_, _x, _y = t
        it = self._store.by_id(id_)
        if it is None:
            raise RuntimeError("Internal error: missing tracked item")
        return it

    @overload
    def nearest_neighbors(
        self, xy: Point, k: int, *, as_items: Literal[False] = ...
    ) -> list[_IdCoord]: ...
    @overload
    def nearest_neighbors(
        self, xy: Point, k: int, *, as_items: Literal[True]
    ) -> list[PointItem]: ...
    def nearest_neighbors(self, xy: Point, k: int, *, as_items: bool = False):
        """
        Return the k nearest neighbors to the query point in order of increasing distance.

        Args:
            xy: Query point (x, y).
            k: Number of neighbors to return.
            as_items: If True, return Item wrappers. If False, return raw tuples.
        Returns:
            If as_items is False: list of (id, x, y) tuples.
            If as_items is True: list of Item objects.
        """
        raw = self._native.nearest_neighbors(xy, k)
        if not as_items:
            return raw
        if self._store is None:
            raise ValueError("Cannot return results as items with track_objects=False")
        out: list[PointItem] = []
        for id_, _x, _y in raw:
            it = self._store.by_id(id_)
            if it is None:
                raise RuntimeError("Internal error: missing tracked item")
            out.append(it)
        return out

    def _new_native(self, bounds: Bounds, capacity: int, max_depth: int | None) -> Any:
        """Create the native engine instance."""
        rust_cls = DTYPE_MAP.get(self._dtype)
        if rust_cls is None:
            raise TypeError(f"Unsupported dtype: {self._dtype}")
        return rust_cls(bounds, capacity, max_depth)

    @classmethod
    def _new_native_from_bytes(cls, data: bytes, dtype: str = "f32") -> Any:
        """Create a new native engine instance from serialized bytes."""
        rust_cls = DTYPE_MAP.get(dtype)
        if rust_cls is None:
            raise TypeError(f"Unsupported dtype: {dtype}")
        return rust_cls.from_bytes(data)

    @staticmethod
    def _make_item(id_: int, geom: Point, obj: Any | None) -> PointItem:
        return PointItem(id_, geom, obj)
