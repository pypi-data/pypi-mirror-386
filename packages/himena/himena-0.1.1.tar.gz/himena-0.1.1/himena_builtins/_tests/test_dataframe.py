import numpy as np
from numpy.testing import assert_equal
import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
import pandas as pd
import polars as pl
from himena import MainWindow, StandardType, create_model
from himena.testing.subwindow import WidgetTester
from himena.workflow import CommandExecution
from himena_builtins.qt.dataframe import QDataFrameView, QDataFramePlotView
from himena_builtins.qt.widgets.dataframe import select_columns
from himena_builtins.qt.basic import QDictView

_Ctrl = Qt.KeyboardModifier.ControlModifier

@pytest.mark.parametrize(
    "df",
    [
        {"a": [1, -2], "b": [3.0, -4.0], "str": ["a", "b"]},
        {"a": [3], "b": ["ggg"]},
        pd.DataFrame({"a": [1, -2], "b": [3.0, -4.0], "str": ["a", "b"]}),
        pl.DataFrame({"a": [1, -2], "b": [3.0, -4.0], "str": ["a", "b"]}),
    ],
)
def test_dataframe(himena_ui: MainWindow, qtbot: QtBot, df):
    with WidgetTester(QDataFrameView(himena_ui)) as tester:
        tester.update_model(value=df)
        qtbot.addWidget(tester.widget)
        table = tester.widget
        table.selection_model.set_ranges([(slice(1, 2), slice(1, 3))])
        table.copy_data()
        table._make_context_menu()
        table.model().headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole)
        table.model().headerData(0, Qt.Orientation.Vertical, Qt.ItemDataRole.ToolTipRole)
        qtbot.keyClick(tester.widget, Qt.Key.Key_F, modifier=_Ctrl)
        qtbot.keyClick(tester.widget, Qt.Key.Key_C, modifier=_Ctrl)
        qtbot.keyClick(tester.widget, Qt.Key.Key_V, modifier=_Ctrl)
        qtbot.keyClick(tester.widget, Qt.Key.Key_Z, modifier=_Ctrl)
        qtbot.keyClick(tester.widget, Qt.Key.Key_Y, modifier=_Ctrl)
        finder = tester.widget._finder_widget
        assert finder is not None
        finder._line_edit.setText("b")
        qtbot.keyClick(finder, Qt.Key.Key_Enter)
        qtbot.keyClick(finder, Qt.Key.Key_Enter, modifier=Qt.KeyboardModifier.ShiftModifier)
        assert type(tester.to_model().value) is type(df)
        tester.is_modified()
        assert tester.widget._hor_header._data_model_for_drag() is not None
        table.selection_model.append((slice(0, 3), slice(0, 1)), column=True)
        tester.widget._hor_header._process_move_event(0)
        tester.widget._hor_header._process_move_event(1)
        select_columns(tester.to_model())([0])

def test_dataframe_plot(himena_ui: MainWindow, qtbot: QtBot):
    x = np.linspace(0, 3, 20)
    df = {"x": x, "y": np.sin(x * 2), "z": np.cos(x * 2)}
    with WidgetTester(QDataFramePlotView(himena_ui)) as tester:
        tester.update_model(value=df)
        tester.cycle_model()
        qtbot.addWidget(tester.widget)
        tester.widget._table_widget.selection_model.move_to(0, 1)
        tester.widget._table_widget.selection_model.set_ranges([(slice(0, 20), slice(1, 2))])

def test_dataframe_command(himena_ui: MainWindow):
    win = himena_ui.add_object(
        {"a": [1, 2], "b": ["p", "q"]},
        type=StandardType.DATAFRAME,
    )
    himena_ui.exec_action("builtins:dataframe:header-to-row")
    assert isinstance(step := win.to_model().workflow.last(), CommandExecution)
    assert step.command_id == "builtins:dataframe:header-to-row"
    win = himena_ui.add_object(
        {"a": [1, 2], "b": ["p", "q"]},
        type=StandardType.DATAFRAME,
    )
    himena_ui.exec_action("builtins:dataframe:series-as-array", with_params={"column": "a"})
    himena_ui.current_window = win
    himena_ui.exec_action("builtins:dataframe:select-columns-by-name", with_params={"columns": ["b"]})
    assert _data_frame_equal(himena_ui.current_model.value, {"b": ["p", "q"]})
    himena_ui.current_window = win
    himena_ui.exec_action("builtins:dataframe:filter", with_params={"column": "b", "operator": "eq", "value": "p"})
    assert _data_frame_equal(himena_ui.current_model.value, {"a": [1], "b": ["p"]})
    himena_ui.current_window = win
    himena_ui.exec_action("builtins:dataframe:sort", with_params={"column": "b", "descending": True, "inplace": True})
    assert _data_frame_equal(himena_ui.current_model.value, {"a": [2, 1], "b": ["q", "p"]})
    assert _data_frame_equal(win.to_model().value, {"a": [2, 1], "b": ["q", "p"]})
    assert win.to_model().workflow.last().command_id == "builtins:dataframe:sort"

    win = himena_ui.current_window
    fn = create_model(
        lambda x: x + 1,
        type=StandardType.FUNCTION,
        add_empty_workflow=True,
    )
    himena_ui.exec_action(
        "builtins:dataframe:new-column-using-function",
        with_params={
            "input_column_name": "a",
            "function": fn,
            "output_column_name": "a2",
        },
        window_context=win,
    )

@pytest.mark.parametrize(
    "df",
    [
        {"a": np.array([1, -2]), "b": np.array([3.0, -4.0]), "str": np.array(["a", "b"])},
        pd.DataFrame({"a": [1, -2], "b": [3.0, -4.0], "str": ["a", "b"]}),
        pl.DataFrame({"a": [1, -2], "b": [3.0, -4.0], "str": ["a", "b"]}),
    ],
)
def test_copy_on_write(himena_ui: MainWindow, qtbot: QtBot, df):
    view = QDataFrameView(himena_ui)
    qtbot.addWidget(view)
    with WidgetTester(view) as tester:
        tester.update_model(value=df, type=StandardType.DATAFRAME)
        view.edit_item(0, 0, "100")
        assert_equal(np.array(tester.to_model().value["a"]), [100, -2])
        assert_equal(np.array(df["a"]), [1, -2])
        view2 = QDataFrameView(himena_ui)
        qtbot.addWidget(view2)
        view2.update_model(view.to_model())
        view.edit_item(1, 1, "0.1")
        assert_equal(np.array(tester.to_model().value["b"]), [3.0, 0.1])
        assert_equal(np.array(df["b"]), [3.0, -4.0])
        assert_equal(np.array(view2.to_model().value["b"]), [3.0, -4.0])

def test_edit_dataframe(himena_ui: MainWindow, qtbot: QtBot):
    df = {
        "int": [1, 3, 5, 7],
        "float": [1.0, -2.0, 3.5, -4.2],
        "str": ["a", "b", "c3", "ddd"],
    }
    view = QDataFrameView(himena_ui)
    qtbot.addWidget(view)
    with WidgetTester(view) as tester:
        tester.update_model(value=df, type=StandardType.DATAFRAME)
        view.edit_item(0, 0, "100")
        assert np.array(tester.to_model().value["int"]).tolist() == [100, 3, 5, 7]
        view.undo()
        assert np.array(tester.to_model().value["int"]).tolist() == [1, 3, 5, 7]
        view.redo()
        assert np.array(tester.to_model().value["int"]).tolist() == [100, 3, 5, 7]
        view.copy_data()
        view.selection_model.set_ranges([(slice(1, 4), slice(0, 1))])
        view.paste_data("200\n300\n400")
        assert np.array(tester.to_model().value["int"]).tolist() == [100, 200, 300, 400]
        view.undo()
        assert np.array(tester.to_model().value["int"]).tolist() == [100, 3, 5, 7]
        view.redo()
        assert np.array(tester.to_model().value["int"]).tolist() == [100, 200, 300, 400]
        view.selection_model.set_ranges([(slice(1, 4), slice(0, 1))])
        view.paste_data("-1")
        assert np.array(tester.to_model().value["int"]).tolist() == [100, -1, -1, -1]
        view.undo()
        assert np.array(tester.to_model().value["int"]).tolist() == [100, 200, 300, 400]
        view.redo()
        assert np.array(tester.to_model().value["int"]).tolist() == [100, -1, -1, -1]
        view.selection_model.set_ranges([(slice(1, 2), slice(0, 3))])
        view.paste_data("10\t20\txxx")
        assert np.array(tester.to_model().value["int"]).tolist() == [100, 10, -1, -1]
        assert np.array(tester.to_model().value["float"]).tolist() == [1.0, 20.0, 3.5, -4.2]
        assert np.array(tester.to_model().value["str"]).tolist() == ["a", "xxx", "c3", "ddd"]
        view.undo()
        assert np.array(tester.to_model().value["int"]).tolist() == [100, -1, -1, -1]
        assert np.array(tester.to_model().value["float"]).tolist() == [1.0, -2.0, 3.5, -4.2]
        assert np.array(tester.to_model().value["str"]).tolist() == ["a", "b", "c3", "ddd"]
        view.redo()
        assert np.array(tester.to_model().value["int"]).tolist() == [100, 10, -1, -1]
        assert np.array(tester.to_model().value["float"]).tolist() == [1.0, 20.0, 3.5, -4.2]
        assert np.array(tester.to_model().value["str"]).tolist() == ["a", "xxx", "c3", "ddd"]
        view.selection_model.set_ranges([(slice(1, 2), slice(0, 1))])
        view.paste_data("10\t20\txxx\n10\t20\tyyy")
        assert np.array(tester.to_model().value["int"]).tolist() == [100, 10, 10, -1]
        assert np.array(tester.to_model().value["float"]).tolist() == [1.0, 20.0, 20.0, -4.2]
        assert np.array(tester.to_model().value["str"]).tolist() == ["a", "xxx", "yyy", "ddd"]
        view.undo()
        assert np.array(tester.to_model().value["int"]).tolist() == [100, 10, -1, -1]
        assert np.array(tester.to_model().value["float"]).tolist() == [1.0, 20.0, 3.5, -4.2]
        assert np.array(tester.to_model().value["str"]).tolist() == ["a", "xxx", "c3", "ddd"]
        view.redo()
        assert np.array(tester.to_model().value["int"]).tolist() == [100, 10, 10, -1]
        assert np.array(tester.to_model().value["float"]).tolist() == [1.0, 20.0, 20.0, -4.2]
        assert np.array(tester.to_model().value["str"]).tolist() == ["a", "xxx", "yyy", "ddd"]


@pytest.mark.parametrize(
    "input_value",
    [
        {"a": 2, "b": "string", "cc": -1.4, "nan": np.nan, "empty": None},
        {"maybe_array": np.arange(5), "maybe_list": [1, 2, 3], "maybe_dict": {"a": 1}},
    ],
)
def test_dict_view(himena_ui: MainWindow, qtbot: QtBot, input_value):
    view = QDictView(himena_ui)
    qtbot.addWidget(view)
    with WidgetTester(view) as tester:
        tester.update_model(value=input_value, type=StandardType.DICT)
        tester.cycle_model()

def _data_frame_equal(a: dict, b: dict):
    for k in a.keys():
        if not np.all(a[k] == b[k]):
            return False
    return True
