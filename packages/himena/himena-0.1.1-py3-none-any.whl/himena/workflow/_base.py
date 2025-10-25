from typing import Any, Iterator, TYPE_CHECKING
from datetime import datetime as _datetime
import uuid

from pydantic import BaseModel, Field


if TYPE_CHECKING:
    from himena.types import WidgetDataModel
    from himena.workflow import Workflow
    import in_n_out as ino


class WorkflowStep(BaseModel):
    """The base class for a single step in a workflow."""

    type: str
    """Literal string that describes the type of the instance."""

    datetime: _datetime = Field(default_factory=_datetime.now)
    """The timestamp of the creation of this instance."""

    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4())
    """The unique identifier of the workflow step across runtime."""

    process_output: bool = Field(default=False)
    """Whether the output of this step should be processed by application."""

    def iter_parents(self) -> Iterator[uuid.UUID]:
        raise NotImplementedError("This method must be implemented in a subclass.")

    def _get_model_impl(self, wf: "Workflow") -> "WidgetDataModel":
        raise NotImplementedError("This method must be implemented in a subclass.")

    def get_model(
        self,
        wf: "Workflow",
        *,
        force_process_output: bool = False,
        metadata: Any | None = None,
    ) -> "WidgetDataModel":
        if win := wf._mock_main_window.window_for_id(self.id):
            out = win.to_model()
            return out
        model = self._get_model_impl(wf)
        model.workflow = wf
        if metadata is not None:
            model.metadata = metadata
        if self.process_output or force_process_output:
            self._current_store().process(model)
        return model

    def __repr_args__(self):  # simplify the repr output
        for arg in super().__repr_args__():
            if arg[0] in ("type", "datetime", "id"):
                continue
            yield arg

    def __str__(self):
        return repr(self)

    def _current_store(self) -> "ino.Store":
        from himena.widgets import current_instance

        return current_instance().model_app.injection_store

    def construct_workflow(self) -> "Workflow":
        from himena.workflow import Workflow

        return Workflow(steps=[self])
