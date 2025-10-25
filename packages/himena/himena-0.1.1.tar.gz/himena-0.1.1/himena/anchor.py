from __future__ import annotations

from typing import TYPE_CHECKING
from himena.types import WindowRect

if TYPE_CHECKING:
    from typing import Self


class WindowAnchor:
    def apply_anchor(
        self,
        main_window_size: tuple[int, int],
        sub_window_size: tuple[int, int],
    ) -> WindowRect | None:
        return None

    def update_for_window_rect(
        self,
        main_window_size: tuple[int, int],
        window_rect: WindowRect,
    ) -> Self:
        return self


NoAnchor = WindowAnchor()


class TopLeftConstAnchor(WindowAnchor):
    def __init__(self, left: int, top: int):
        self._left = left
        self._top = top

    def apply_anchor(
        self,
        main_window_size: tuple[int, int],
        sub_window_size: tuple[int, int],
    ) -> WindowRect:
        w, h = sub_window_size
        return WindowRect.from_tuple(self._left, self._top, w, h)

    def update_for_window_rect(
        self,
        main_window_size: tuple[int, int],
        window_rect: WindowRect,
    ) -> Self:
        return TopLeftConstAnchor(window_rect.left, window_rect.top)


class TopRightConstAnchor(WindowAnchor):
    def __init__(self, right: int, top: int):
        self._right = right
        self._top = top

    def apply_anchor(
        self,
        main_window_size: tuple[int, int],
        sub_window_size: tuple[int, int],
    ) -> WindowRect:
        main_w, _ = main_window_size
        w, h = sub_window_size
        return WindowRect.from_tuple(main_w - self._right - w, self._top, w, h)

    def update_for_window_rect(
        self,
        main_window_size: tuple[int, int],
        window_rect: WindowRect,
    ) -> Self:
        w0 = main_window_size[0]
        return TopRightConstAnchor(w0 - window_rect.right, window_rect.top)


class BottomLeftConstAnchor(WindowAnchor):
    def __init__(self, left: int, bottom: int):
        self._left = left
        self._bottom = bottom

    def apply_anchor(
        self,
        main_window_size: tuple[int, int],
        sub_window_size: tuple[int, int],
    ) -> WindowRect:
        _, main_h = main_window_size
        w, h = sub_window_size
        return WindowRect.from_tuple(self._left, main_h - self._bottom - h, w, h)

    def update_for_window_rect(
        self,
        main_window_size: tuple[int, int],
        window_rect: WindowRect,
    ) -> Self:
        h0 = main_window_size[1]
        return BottomLeftConstAnchor(window_rect.left, h0 - window_rect.bottom)


class BottomRightConstAnchor(WindowAnchor):
    def __init__(self, right: int, bottom: int):
        self._right = right
        self._bottom = bottom

    def apply_anchor(
        self,
        main_window_size: tuple[int, int],
        sub_window_size: tuple[int, int],
    ) -> WindowRect:
        main_w, main_h = main_window_size
        w, h = sub_window_size
        return WindowRect.from_tuple(
            main_w - self._right - w, main_h - self._bottom - h, w, h
        )

    def update_for_window_rect(
        self,
        main_window_size: tuple[int, int],
        window_rect: WindowRect,
    ) -> Self:
        w0, h0 = main_window_size
        return BottomRightConstAnchor(w0 - window_rect.right, h0 - window_rect.bottom)


class AllCornersAnchor(WindowAnchor):
    def apply_anchor(
        self,
        main_window_size: tuple[int, int],
        sub_window_size: tuple[int, int],
    ) -> WindowRect:
        return WindowRect.from_tuple(0, 0, *main_window_size)


def anchor_to_dict(anchor: WindowAnchor) -> dict:
    """Convert an anchor to a json-serializable dictionary."""
    if isinstance(anchor, TopLeftConstAnchor):
        return {"type": "top-left-const", "left": anchor._left, "top": anchor._top}
    if isinstance(anchor, TopRightConstAnchor):
        return {"type": "top-right-const", "right": anchor._right, "top": anchor._top}
    if isinstance(anchor, BottomLeftConstAnchor):
        return {
            "type": "bottom-left-const",
            "left": anchor._left,
            "bottom": anchor._bottom,
        }
    if isinstance(anchor, BottomRightConstAnchor):
        return {
            "type": "bottom-right-const",
            "right": anchor._right,
            "bottom": anchor._bottom,
        }
    if anchor is NoAnchor:
        return {"type": "no-anchor"}
    raise ValueError(f"Unknown anchor type: {anchor!r}")


def dict_to_anchor(data: dict) -> WindowAnchor:
    if data["type"] == "top-left-const":
        return type_to_anchor_class(data["type"])(data["left"], data["top"])
    if data["type"] == "top-right-const":
        return type_to_anchor_class(data["type"])(data["right"], data["top"])
    if data["type"] == "bottom-left-const":
        return type_to_anchor_class(data["type"])(data["left"], data["bottom"])
    if data["type"] == "bottom-right-const":
        return type_to_anchor_class(data["type"])(data["right"], data["bottom"])
    if data["type"] == "no-anchor":
        return NoAnchor
    raise ValueError(f"Unknown anchor type: {data['type']}")


def type_to_anchor_class(typ: str) -> type[WindowAnchor]:
    if typ == "top-left-const":
        return TopLeftConstAnchor
    if typ == "top-right-const":
        return TopRightConstAnchor
    if typ == "bottom-left-const":
        return BottomLeftConstAnchor
    if typ == "bottom-right-const":
        return BottomRightConstAnchor
    if typ == "no-anchor":
        return NoAnchor
    raise ValueError(f"Unknown anchor type: {typ}")
