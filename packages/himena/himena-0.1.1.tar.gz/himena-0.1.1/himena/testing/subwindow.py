from __future__ import annotations
from typing import Any, Generic, TypeVar, overload

from himena.plugins import _checker
from himena.types import DragDataModel, DropResult, Size, WidgetDataModel
from himena.style import default_style
from himena.widgets import current_instance
from himena.workflow import ProgrammaticMethod

_W = TypeVar("_W")


class WidgetTester(Generic[_W]):
    def __init__(self, widget: _W):
        self._widget = widget

    def __enter__(self) -> WidgetTester[_W]:
        _checker.call_theme_changed_callback(self._widget, default_style())
        _checker.call_widget_activated_callback(self._widget)
        _checker.call_widget_added_callback(self._widget)
        if hasattr(self._widget, "control_widget"):
            self._widget.control_widget()
        if hasattr(self._widget, "size_hint"):
            hint = self._widget.size_hint()
            _checker.call_widget_resized_callback(
                self._widget, Size(200, 200), Size(*hint)
            )
        if hasattr(self._widget, "is_editable"):
            self._widget.is_editable()
        if hasattr(self._widget, "set_editable"):
            self._widget.set_editable(False)
            self._widget.set_editable(True)
        return self

    def __exit__(self, *args):
        if hasattr(self._widget, "is_modified"):
            self._widget.is_modified()
        _checker.call_widget_closed_callback(self._widget)

    @overload
    def update_model(self, model: WidgetDataModel) -> WidgetTester[_W]: ...
    @overload
    def update_model(
        self,
        value: Any,
        *,
        type: str | None = None,
        metadata: Any | None = None,
        **kwargs,
    ) -> WidgetTester[_W]: ...

    def update_model(self, value, **kwargs) -> WidgetTester[_W]:
        model = self._norm_model_input(value, **kwargs)
        self._widget.update_model(model)
        return self

    def to_model(self) -> WidgetDataModel:
        model = self._widget.to_model()
        if not isinstance(model, WidgetDataModel):
            raise TypeError(
                f"Widget {self.widget!r} returned {model!r}, expected WidgetDataModel"
            )
        model.workflow = ProgrammaticMethod().construct_workflow()
        return model

    def cycle_model(self) -> tuple[WidgetDataModel, WidgetDataModel]:
        """Cycle `update_model` and `to_model` and return both.

        This function is useful for testing the consistency of widget's `update_model`
        and `to_model`.
        """
        model = self.to_model()
        self.update_model(model)
        return model, self.to_model()

    @overload
    def drop_model(self, model: WidgetDataModel) -> DropResult: ...
    @overload
    def drop_model(
        self,
        value: Any,
        *,
        type: str | None = None,
        metadata: Any | None = None,
        **kwargs,
    ) -> DropResult: ...

    def drop_model(self, value, **kwargs):
        """Emulate dropping a model into the widget.

        The input can be either a `WidgetDataModel` or the input of `WidgetDataModel`.

        ``` python
        tester.drop_model(WidgetDataModel(value=..., type=...))
        tester.drop_model(value=..., type=...)
        ```
        """
        model = self._norm_model_input(value, **kwargs)
        drag_data_model = DragDataModel(getter=model, type=model.type)
        if not drag_data_model.widget_accepts_me(self.widget):
            try:
                allowed = self.widget.allowed_drop_types()
            except AttributeError:
                allowed = []
            raise ValueError(
                f"Widget {self.widget!r} does not accept dropping {model.type}. Allowed types are: {allowed}"
            )
        model.workflow = ProgrammaticMethod().construct_workflow()
        out = self.widget.dropped_callback(model)
        if out is None:
            out = DropResult()
        elif not isinstance(out, DropResult):
            raise TypeError(
                f"Widget {self.widget!r} returned {out!r}, expected DropResult"
            )
        if out.command_id is not None:
            returned_model = current_instance().exec_action(
                out.command_id,
                model_context=self.to_model(),
                with_params=out.with_params,
                process_model_output=False,
            )
            if not isinstance(returned_model, WidgetDataModel):
                raise ValueError(
                    f"Command {out.command_id} did not return a WidgetDataModel."
                )
            self.update_model(returned_model)
        return out

    def is_modified(self) -> bool:
        return self._widget.is_modified()

    @property
    def widget(self) -> _W:
        return self._widget

    def _norm_model_input(self, val, **kwargs) -> WidgetDataModel:
        if isinstance(val, WidgetDataModel):
            if kwargs:
                raise TypeError("Cannot specify both model and kwargs")
            return val
        else:
            if kwargs.get("type") is None:
                try:
                    kwargs["type"] = self._widget.model_type()
                except AttributeError:
                    raise TypeError("`type` argument must be specified") from None
            return WidgetDataModel(value=val, **kwargs)
