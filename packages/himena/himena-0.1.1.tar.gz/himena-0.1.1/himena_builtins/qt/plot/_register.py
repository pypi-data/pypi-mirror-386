from __future__ import annotations

from typing import Callable, overload, TypeVar, TYPE_CHECKING
from cmap import Color
from himena.standards import plotting as hplt

if TYPE_CHECKING:
    from matplotlib import pyplot as plt
    from mpl_toolkits import mplot3d as plt3d

_CONVERSION_RULES: dict[
    type[hplt.BasePlotModel], Callable[[hplt.BasePlotModel, plt.Axes], None]
] = {}

_F = TypeVar("_F", bound=Callable)


@overload
def register_plot_model(
    model_class: type[hplt.BasePlotModel],
    rule: _F,
) -> _F: ...
@overload
def register_plot_model(
    model_class: type[hplt.BasePlotModel],
    rule: None,
) -> Callable[[_F], _F]: ...


def register_plot_model(
    model_class: type[hplt.BasePlotModel],
    rule: Callable[[hplt.BasePlotModel, plt.Axes], None] | None = None,
):
    """Register a matplotlib-specific conversion rule for a plot model."""

    def inner(f):
        _CONVERSION_RULES[model_class] = f
        return f

    return inner if rule is None else inner(rule)


def convert_plot_model(model: hplt.BasePlotModel, ax: plt.Axes):
    if model.__class__ in _CONVERSION_RULES:
        return _CONVERSION_RULES[model.__class__](model, ax)
    raise ValueError(f"Unsupported plot model: {model!r}")


@register_plot_model(hplt.Scatter)
def _add_scatter(model: hplt.Scatter, ax: plt.Axes):
    kwargs = {}
    if model.size is not None:
        kwargs["s"] = model.size**2
    if model.face.color is not None:
        kwargs["c"] = Color(model.face.color).hex
    if model.edge.color is not None:
        kwargs["edgecolors"] = model.edge.color
    ax.scatter(
        model.x, model.y, marker=model.symbol, linewidths=model.edge.width,
        hatch=model.face.hatch, linestyle=model.edge.style or "-", label=model.name,
        **kwargs,
    )  # fmt: skip


@register_plot_model(hplt.Line)
def _add_line(model: hplt.Line, ax: plt.Axes):
    ax.plot(
        model.x, model.y, color=model.edge.color, linewidth=model.edge.width,
        linestyle=model.edge.style, label=model.name,
    )  # fmt: skip


@register_plot_model(hplt.Bar)
def _add_bar(model: hplt.Bar, ax: plt.Axes):
    kwargs = {}
    if model.bar_width is not None:
        kwargs["width"] = model.bar_width
    ax.bar(
        model.x, model.y, color=model.face.color, hatch=model.face.hatch,
        bottom=model.bottom, edgecolor=model.edge.color, **kwargs,
        label=model.name, linewidth=model.edge.width, linestyle=model.edge.style,
    )  # fmt: skip


@register_plot_model(hplt.Histogram)
def _add_hist(model: hplt.Histogram, ax: plt.Axes):
    _add_band(model.to_band(), ax)


@register_plot_model(hplt.ErrorBar)
def _add_errorbar(model: hplt.ErrorBar, ax: plt.Axes):
    ax.errorbar(
        model.x, model.y, xerr=model.x_error, yerr=model.y_error,
        capsize=model.capsize, color=model.edge.color, linewidth=model.edge.width,
        linestyle=model.edge.style, label=model.name,
    )  # fmt: skip


@register_plot_model(hplt.Band)
def _add_band(model: hplt.Band, ax: plt.Axes):
    if model.orient == "vertical":
        func = ax.fill_between
    else:
        func = ax.fill_betweenx
    func(
        model.x, model.y0, model.y1, color=model.face.color, hatch=model.face.hatch,
        edgecolor=model.edge.color, linewidth=model.edge.width,
        linestyle=model.edge.style or "-", label=model.name,
    )  # fmt: skip


@register_plot_model(hplt.Span)
def _add_span(model: hplt.Span, ax: plt.Axes):
    if model.orient == "vertical":
        func = ax.axvspan
    else:
        func = ax.axhspan
    func(
        model.start,
        model.end,
        color=model.face.color,
        hatch=model.face.hatch,
        edgecolor=model.edge.color,
        linewidth=model.edge.width,
        linestyle=model.edge.style,
        label=model.name,
    )


@register_plot_model(hplt.Texts)
def _add_texts(model: hplt.Texts, ax: plt.Axes):
    ha, va = _ANCHOR_MAP[model.anchor]
    for x, y, text in zip(model.x, model.y, model.texts):
        ax.text(
            x, y, text, color=model.color, fontsize=model.size, clip_on=True,
            label=model.name, rotation=model.rotation, ha=ha, va=va,
        )  # fmt: skip


@register_plot_model(hplt.Scatter3D)
def _add_scatter_3d(model: hplt.Scatter3D, ax: plt3d.Axes3D):
    if model.size is not None:
        s = model.size**2
    else:
        s = 20
    ax.scatter(
        model.x, model.y, model.z, s=s, c=Color(model.face.color).hex,
        marker=model.symbol, linewidths=model.edge.width, hatch=model.face.hatch,
        edgecolors=model.edge.color, linestyle=model.edge.style or "-",
        label=model.name,
    )  # fmt: skip


@register_plot_model(hplt.Line3D)
def _add_line_3d(model: hplt.Line3D, ax: plt3d.Axes3D):
    ax.plot(
        model.x, model.y, model.z, color=model.edge.color, linewidth=model.edge.width,
        linestyle=model.edge.style, label=model.name,
    )  # fmt: skip


@register_plot_model(hplt.Surface3D)
def _add_surface_3d(model: hplt.Surface3D, ax: plt3d.Axes3D):
    ax.plot_surface(
        model.x, model.y, model.z, color=model.face.color, edgecolor=model.edge.color,
        linewidth=model.edge.width or 0.0, linestyle=model.edge.style or "-",
        label=model.name,
    )  # fmt: skip


@register_plot_model(hplt.Mesh3D)
def _add_mesh_3d(model: hplt.Mesh3D, ax: plt3d.Axes3D):
    ax.plot_trisurf(
        model.vertices[:, 0], model.vertices[:, 1], model.vertices[:, 2],
        triangles=model.face_indices, color=model.face.color, edgecolor=model.edge.color,
        linewidth=model.edge.width, linestyle=model.edge.style, label=model.name,
    )  # fmt: skip


_ANCHOR_MAP = {
    "center": ("center", "center"),
    "left": ("left", "center"),
    "right": ("right", "center"),
    "top": ("center", "top"),
    "bottom": ("center", "bottom"),
    "top_left": ("left", "top"),
    "top_right": ("right", "top"),
    "bottom_left": ("left", "bottom"),
    "bottom_right": ("right", "bottom"),
}
