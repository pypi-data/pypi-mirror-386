import math
import typing as t
from platynui_native import UiNode, Runtime


def is_num(x: t.Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x))


def is_rect_tuple(v: t.Any) -> bool:
    return isinstance(v, tuple) and len(v) == 4 and all(is_num(n) for n in v)


def test_evaluate_desktop_node(rt_mock_platform: Runtime) -> None:
    items = rt_mock_platform.evaluate("/")
    assert isinstance(items, list)

    # find first UiNode in results
    node = next((it for it in items if isinstance(it, UiNode)), None)
    assert node is not None, "expected at least one UiNode result"

    assert node.role == "Desktop"
    assert node.namespace.as_str() == "control"

    # Bounds should be a 4-tuple (x, y, w, h)
    bounds = node.attribute("Bounds")
    if hasattr(bounds, "to_tuple"):
        bt = getattr(bounds, "to_tuple")()
        assert isinstance(bt, tuple) and len(bt) == 4
        assert all(is_num(n) for n in bt)
    else:
        # Fallback: tolerate implementations that expose plain tuples
        assert is_rect_tuple(bounds)


def test_pointer_and_keyboard_smoke(rt_mock_platform: Runtime) -> None:
    # pointer should be available with mock platform
    pos = rt_mock_platform.pointer_position()
    assert hasattr(pos, "x") and hasattr(pos, "y")
    # move back to same position using Point
    rt_mock_platform.pointer_move_to(pos)

    # keyboard should be available with mock platform
    rt_mock_platform.keyboard_type("a")
