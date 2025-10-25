"""Standard plotting models."""

from himena.standards.plotting import layout, models
from himena.standards.plotting.layout import (
    BaseLayoutModel,
    SingleAxes,
    SingleStackedAxes,
    Row,
    Column,
    Grid,
    Axes,
)
from himena.standards.plotting.models import (
    Line,
    Scatter,
    Bar,
    Band,
    Span,
    ErrorBar,
    Histogram,
    Texts,
)

# 3D

from himena.standards.plotting.layout3d import (
    Axes3D,
    SingleAxes3D,
)
from himena.standards.plotting.models3d import (
    Scatter3D,
    Line3D,
    Surface3D,
    Mesh3D,
)

from himena.standards.plotting.components import StyledText, Axis, BasePlotModel
from himena.standards.plotting._api import (
    figure,
    row,
    column,
    grid,
    figure_3d,
    figure_stack,
)

__all__ = [
    "models",
    "layout",
    "figure",
    "figure_3d",
    "figure_stack",
    "row",
    "column",
    "grid",
    "BaseLayoutModel",
    "SingleAxes",
    "SingleStackedAxes",
    "Row",
    "Column",
    "Grid",
    "Axes",
    "Axis",
    "BasePlotModel",
    "Line",
    "Scatter",
    "Bar",
    "Band",
    "Span",
    "ErrorBar",
    "Histogram",
    "Texts",
    "StyledText",
    "Axes3D",
    "SingleAxes3D",
    "Scatter3D",
    "Line3D",
    "Surface3D",
    "Mesh3D",
]
