from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
import subprocess
import tempfile
from typing import TYPE_CHECKING, Iterator, Literal
from qtpy import QtWidgets as QtW, QtCore, QtGui
from superqt.utils import thread_worker, FunctionWorker

from himena import _drag
from himena.qt._qsvg import QColoredSVGIcon
from himena.types import WidgetDataModel, DragDataModel
from himena.workflow import PathReaderMethod
from himena.consts import MonospaceFontFamily
from himena.plugins import validate_protocol
from himena.widgets import notify, set_status_tip
from himena.style import Theme
from himena_builtins._consts import ICON_PATH

if TYPE_CHECKING:
    from himena.qt import MainWindowQt


class QBaseRemoteExplorerWidget(QtW.QWidget):
    themeChanged = QtCore.Signal(Theme)

    def __init__(self, ui: MainWindowQt):
        super().__init__()

        self.setAcceptDrops(True)

        self._pwd = Path("~")
        self._last_dir = self._pwd
        self._ui = ui
        self._worker: FunctionWorker | None = None
        font = QtGui.QFont(MonospaceFontFamily)

        self._pwd_widget = QtW.QLineEdit()
        self._pwd_widget.setFont(font)
        self._pwd_widget.editingFinished.connect(self._on_pwd_edited)

        self._file_list_widget = QRemoteTreeWidget(self)
        self._file_list_widget.itemActivated.connect(self._read_item_to_gui)
        self._file_list_widget.setFont(font)
        self._file_list_widget.item_copied.connect(self._copy_item_paths)
        self._file_list_widget.item_pasted.connect(self._send_files)
        self._file_list_widget.item_renamed.connect(self._rename_item)
        self._file_list_widget.item_deleted.connect(self._trash_items)

        self._filter_widget = QFilterLineEdit(self)
        self._filter_widget.textChanged.connect(self._file_list_widget._apply_filter)
        self._filter_widget.setVisible(False)
        self._light_background = True
        self._force_sync = False  # for testing

    def _make_mimedata_for_items(
        self,
        items: list[QtW.QTreeWidgetItem],
    ) -> QtCore.QMimeData:
        mime = QtCore.QMimeData()
        mime.setText(
            "\n".join(
                meth.to_str() for meth in self._make_reader_methods_for_items(items)
            )
        )
        mime.setHtml(
            "<br>".join(
                f'<span ftype="{"d" if meth.force_directory else "f"}">{meth.to_str()}</span>'
                for meth in self._make_reader_methods_for_items(items)
            )
        )
        mime.setParent(self)  # this is needed to trace where the MIME data comes from
        return mime

    def _make_reader_methods_for_items(
        self, items: list[QtW.QTreeWidgetItem]
    ) -> list[PathReaderMethod]:
        methods: list[PathReaderMethod] = []
        for item in items:
            typ = item_type(item)
            if typ == "l":
                _, real_path = item.text(0).split(" -> ")
                remote_path = self._pwd / real_path
                is_dir = False
            else:
                remote_path = self._pwd / item.text(0)
                is_dir = typ == "d"
            meth = self._make_reader_method(remote_path, is_dir)
            methods.append(meth)
        return methods

    @thread_worker
    def _read_remote_path_worker(
        self, path: Path, is_dir: bool = False
    ) -> WidgetDataModel:
        return self._make_reader_method(path, is_dir).run()

    def _read_and_add_model(self, path: Path, is_dir: bool = False):
        """Read the remote file in another thread and add the model in the main."""
        worker = self._read_remote_path_worker(path, is_dir)
        worker.returned.connect(self._ui.add_data_model)
        worker.started.connect(lambda: self._set_busy(True))
        worker.finished.connect(lambda: self._set_busy(False))
        if self._force_sync:
            worker.run()
        else:
            worker.start()
        set_status_tip(f"Reading file: {path}", duration=2.0)

    def _set_busy(self, busy: bool):
        pass  # This method can be overridden to set a busy state in the UI

    #############################################
    #### Need to be overridden in subclasses ####
    #############################################
    def _make_reader_method(self, path: Path, is_dir: bool) -> PathReaderMethod:
        raise NotImplementedError

    def _make_reader_method_from_str(self, line: str, is_dir: bool) -> PathReaderMethod:
        raise NotImplementedError

    def _iter_file_items(self, path: str) -> list[QtW.QTreeWidgetItem]:
        raise NotImplementedError

    def _get_file_type(self, path: str) -> Literal["d", "f"]:
        raise NotImplementedError

    def _move_files(self, old_name: str, new_name: str) -> None:
        raise NotImplementedError

    def _trash_files(self, paths: list[str]):
        raise NotImplementedError

    def _send_file(self, src: Path, dst_remote: str, is_dir: bool = False):
        raise NotImplementedError

    def _make_get_type_args(self, path: str) -> list[str]:
        raise NotImplementedError

    #############################################
    #############################################

    def readers_from_mime(self, mime: QtCore.QMimeData) -> list[PathReaderMethod]:
        """Construct readers from the mime data."""
        out: list[PathReaderMethod] = []
        for line in mime.html().split("<br>"):
            if not line:
                continue
            if m := re.compile(r"<span ftype=\"(d|f)\">(.+)</span>").match(line):
                is_dir = m.group(1) == "d"
                line = m.group(2)
            else:
                continue
            meth = self._make_reader_method_from_str(line, is_dir)
            out.append(meth)
        return out

    @thread_worker
    def _run_ls_command(self, path: Path) -> list[QtW.QTreeWidgetItem]:
        items: list[QtW.QTreeWidgetItem] = []
        for item in self._iter_file_items(path.as_posix()):
            item.setToolTip(0, item.text(0))
            items.append(item)

        # sort directories first
        items = sorted(
            items,
            key=lambda x: (not x.text(0).endswith("/"), x.text(0)),
        )
        if path != self._pwd:
            self._last_dir = self._pwd
        self._pwd = path
        return items

    def _read_item_to_gui(self, item: QtW.QTreeWidgetItem):
        typ = item_type(item)
        if typ == "d":
            self._set_current_path(self._pwd / item.text(0))
        elif typ == "l":
            _, real_path = item.text(0).split(" -> ")
            # solve relative path
            if real_path.startswith("../"):
                real_path_abs = self._pwd.parent.joinpath(real_path[3:])
            elif real_path.startswith("./"):
                real_path_abs = self._pwd.joinpath(real_path[2:])
            elif real_path.startswith(("/", "~")):
                real_path_abs = Path(real_path)
            else:
                real_path_abs = self._pwd / real_path
            args_check_type = self._make_get_type_args(real_path_abs.as_posix())
            result = subprocess.run(args_check_type, capture_output=True)
            if result.returncode != 0:
                raise ValueError(f"Failed to get type: {result.stderr.decode()}")

            link_type = self._get_file_type(real_path_abs.as_posix())
            if link_type == "d":
                self._set_current_path(real_path_abs)
            else:
                self._read_and_add_model(real_path_abs)
        else:
            self._read_and_add_model(self._pwd / item.text(0))

    def _send_model(self, model: DragDataModel):
        data_model = model.data_model()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            src_pathobj = data_model.write_to_directory(tmpdir)
            self._send_file_to_remote(src_pathobj)

    def _send_file_to_remote(self, src: Path, is_dir: bool = False):
        """Send local file to the remote host."""
        if src.name in self._file_list_widget.existing_names():
            raise ValueError(
                f"File {src.name!r} already exists in the remote directory."
            )
        if src.name in [".", ".."] or "/" in src.name:
            raise ValueError(f"Invalid file name: {src.name!r}")
        dst_remote = self._pwd / src.name
        self._send_file(src, dst_remote.as_posix(), is_dir=is_dir)
        notify(f"Sent {src.as_posix()} to {dst_remote.as_posix()}", duration=2.8)

    def dragEnterEvent(self, a0):
        mime = a0.mimeData()
        if (
            _drag.get_dragging_model() is not None
            or mime.urls()
            or isinstance(mime.parent(), QBaseRemoteExplorerWidget)
        ):
            a0.accept()
        else:
            a0.ignore()

    def dragMoveEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragMoveEvent(a0)

    def dropEvent(self, a0: QtGui.QDropEvent):
        if model := _drag.drop():
            self._ui.submit_async_task(self._send_model, model)
            set_status_tip("Start sending file ...")
        elif urls := a0.mimeData().urls():
            for url in urls:
                path = Path(url.toLocalFile())
                self._ui.submit_async_task(
                    self._send_file_to_remote, path, path.is_dir()
                )
                set_status_tip(f"Sent to {path.name}", duration=2.8)
        elif type((mime := a0.mimeData()).parent()) is type(self):
            # this is a drag from another remote explorer widget
            item_under_cursor = self._file_list_widget.itemAt(
                self._file_list_widget.viewport().mapFromGlobal(QtGui.QCursor.pos())
            )
            if item_under_cursor is None:
                return
            if item_type(item_under_cursor) == "d":
                dst_dir = self._pwd / item_under_cursor.text(0)
                methods = self.readers_from_mime(mime)
                paths: list[Path] = []
                for meth in methods:
                    if isinstance(meth.path, Path):
                        paths.append(meth.path)
                    else:
                        paths.extend(meth.path)

                for path in paths:
                    self._move_files(
                        path.as_posix(), dst_dir.joinpath(path.name).as_posix()
                    )
                if paths:
                    self._refresh_pwd()

    def _refresh_pwd(self):
        """Refresh the current path."""
        self._set_current_path(self._pwd)

    def _copy_item_paths(self, items: list[QtW.QTreeWidgetItem]):
        mime = self._make_mimedata_for_items(items)
        clipboard = QtGui.QGuiApplication.clipboard()
        clipboard.setMimeData(mime)

    def _send_files(self, paths: list[Path]):
        """Send files from the local system to the remote host."""
        for path in paths:
            self._ui.submit_async_task(self._send_file_to_remote, path, path.is_dir())

    def _rename_item(self, item: QtW.QTreeWidgetItem, old_name: str, new_name: str):
        """Rename the item in the remote directory."""
        if old_name == new_name:
            return
        old_path = self._pwd / old_name
        new_path = self._pwd / new_name
        self._move_files(old_path.as_posix(), new_path.as_posix())
        if item_type(item) == "f":
            item.setText(0, new_name)
        else:
            self._refresh_pwd()

    def _trash_items(self, items: list[QtW.QTreeWidgetItem]):
        """Move the selected items to the trash."""
        paths = [self._pwd.joinpath(item.text(0)).as_posix() for item in items]
        self._trash_files(paths)
        item_str = "\n- ".join(item.text(0) for item in items)
        notify(f"Moved items to trash:\n- {item_str}", duration=2.8)
        self._refresh_pwd()

    @validate_protocol
    def theme_changed_callback(self, theme: Theme) -> None:
        self._light_background = theme.is_light_background()
        count = self._file_list_widget.topLevelItemCount()
        self._on_ls_done([self._file_list_widget.topLevelItem(i) for i in range(count)])
        self.themeChanged.emit(theme)

    def _set_current_path(self, path: Path):
        if path != self._pwd:
            self._last_dir = self._pwd
        self._pwd_widget.setText(path.as_posix())
        if self._worker is not None:
            self._worker.quit()
            self._worker = None
        self._worker = worker = self._run_ls_command(path)
        worker.returned.connect(self._on_ls_done)
        worker.started.connect(lambda: self._set_busy(True))
        worker.finished.connect(self._on_worker_finished)
        if self._force_sync:
            worker.run()
        else:
            worker.start()
        set_status_tip("Obtaining the file content ...", duration=3.0)

    def _on_worker_finished(self):
        self._set_busy(False)
        self._worker = None

    def _on_ls_done(self, items: list[QtW.QTreeWidgetItem]):
        for item in items:
            icon = icon_for_file_type(item_type(item), self._light_background)
            item.setIcon(0, icon)
        self._file_list_widget.clear()
        self._file_list_widget.addTopLevelItems(items)
        for i in range(1, self._file_list_widget.columnCount()):
            self._file_list_widget.resizeColumnToContents(i)
        set_status_tip(f"Currently under {self._pwd.name}", duration=1.0)

    def _on_pwd_edited(self):
        pwd_text = self._pwd_widget.text()
        if "*" in pwd_text or "?" in pwd_text:
            self._pwd_widget.setSelection(0, len(pwd_text))
            raise ValueError("Wildcards are not supported.")
        if self._pwd != Path(pwd_text):
            self._set_current_path(Path(pwd_text))

    def keyPressEvent(self, a0):
        if (
            a0.key() == QtCore.Qt.Key.Key_F
            and a0.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
        ):
            self._filter_widget.toggle()
            return
        return super().keyPressEvent(a0)


class QRemoteTreeWidget(QtW.QTreeWidget):
    item_copied = QtCore.Signal(list)
    item_pasted = QtCore.Signal(list)  # list of local Path objects
    item_renamed = QtCore.Signal(
        QtW.QTreeWidgetItem, str, str
    )  # item, old_name, new_name
    item_deleted = QtCore.Signal(list)  # list of QtW.QTreeWidgetItem

    def __init__(self, parent: QBaseRemoteExplorerWidget):
        super().__init__(parent)
        self.setIndentation(0)
        self.setColumnWidth(0, 180)
        self.setHeaderLabels(
            ["Name", "Datetime", "Size", "Group", "Owner", "Link", "Permission"]
        )
        self.setSelectionMode(QtW.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.header().setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.header().setFixedHeight(20)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._line_edit = QEditFileNameLineEdit(self)
        self._line_edit.text_edited.connect(self._line_edit_editing_finished)
        self._line_edit.setHidden(True)

    def existing_names(self) -> list[str]:
        """Get the names of existing items in the tree."""
        existing_names: list[str] = []
        for i in range(self.topLevelItemCount()):
            if item := self.topLevelItem(i):
                existing_names.append(item.text(0))
        return existing_names

    def _line_edit_editing_finished(self, new_name: str):
        """Handle the editing finished event of the line edit."""
        if item := self.currentItem():
            if new_name and new_name != item.text(0):
                if new_name in self.existing_names():
                    raise ValueError(f"File name {new_name!r} already exists.")
                self.item_renamed.emit(item, item.text(0), new_name)
            self.setFocus()

    def _make_context_menu(self):
        menu = QtW.QMenu(self)
        sels = self.selectedItems()
        open_action = menu.addAction("Open")
        open_action.setToolTip("Open this file to the main window")
        open_action.triggered.connect(
            lambda: self.itemActivated.emit(self.currentItem(), 0)
        )
        copy_action = menu.addAction("Copy Path")
        copy_action.setToolTip("Copy the paths of the selected items")
        copy_action.triggered.connect(lambda: self.item_copied.emit(sels))
        paste_action = menu.addAction("Paste")
        paste_action.setToolTip(
            "Paste local files to the remote file system from the clipboard"
        )
        paste_action.triggered.connect(self._paste_from_clipboard)

        menu.addSeparator()
        download_action = menu.addAction("Download")
        download_action.setToolTip("Download the selected items to ~/Downloads")
        download_action.triggered.connect(
            lambda: self._download_items(sels, Path.home() / "Downloads"),
        )
        download_to_action = menu.addAction("Download To ...")
        download_to_action.setToolTip(
            "Download the selected items to a specified directory"
        )
        download_to_action.triggered.connect(lambda: self._download_items(sels))
        menu.addSeparator()
        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: self._edit_item(self.currentItem()))
        delete_action = menu.addAction("Move to Trash")
        delete_action.triggered.connect(lambda: self.item_deleted.emit(sels))
        if len(sels) == 0:
            open_action.setEnabled(False)
            copy_action.setEnabled(False)
            download_action.setEnabled(False)
            download_to_action.setEnabled(False)
            rename_action.setEnabled(False)
            delete_action.setEnabled(False)
        return menu

    def _show_context_menu(self, pos: QtCore.QPoint):
        self._make_context_menu().exec(self.viewport().mapToGlobal(pos))

    def keyPressEvent(self, event):
        _mod = event.modifiers()
        _key = event.key()
        _ctrl = _mod & QtCore.Qt.KeyboardModifier.ControlModifier
        _shift = _mod & QtCore.Qt.KeyboardModifier.ShiftModifier
        _alt = _mod & QtCore.Qt.KeyboardModifier.AltModifier
        _no_mod = not (_ctrl or _shift or _alt)
        if _no_mod:
            if _key == QtCore.Qt.Key.Key_Delete:
                items = self.selectedItems()
                if items:
                    self.item_deleted.emit(items)
                    return None
            elif _key == QtCore.Qt.Key.Key_F2:
                if item := self.currentItem():
                    self._edit_item(item)
            elif _key == QtCore.Qt.Key.Key_F5:
                self.parent()._refresh_pwd()

        elif _ctrl and not _shift and not _alt:
            if _key == QtCore.Qt.Key.Key_C:
                items = self.selectedItems()
                self.item_copied.emit(items)
                return None
            elif _key == QtCore.Qt.Key.Key_V:
                return self._paste_from_clipboard()
        return super().keyPressEvent(event)

    def _edit_item(self, item: QtW.QTreeWidgetItem | None):
        if item is None:
            return
        text = item.text(0)
        if text.endswith("/"):
            text = text[:-1]
        self._line_edit.setText(text)
        width = self.header().sectionSize(0)
        rect = self.visualItemRect(item)
        rect.translate(rect.height() + 2, self.header().height())
        rect.setWidth(width)
        self._line_edit.setGeometry(rect)
        self._line_edit.setFocus()
        self._line_edit.setVisible(True)
        self._line_edit.setSelection(0, len(text))

    def _paste_from_clipboard(self):
        clipboard = QtGui.QGuiApplication.clipboard()
        mime = clipboard.mimeData()
        if mime.hasUrls():
            urls = mime.urls()
            paths = [Path(url.toLocalFile()) for url in urls]
            self.item_pasted.emit(paths)
        else:
            notify("No valid file paths in the clipboard.")

    # drag-and-drop
    def mouseMoveEvent(self, e: QtGui.QMouseEvent):
        if e.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self._start_drag(e.pos())
            return None
        return super().mouseMoveEvent(e)

    def _start_drag(self, pos: QtCore.QPoint):
        items = self.selectedItems()
        mime = self.parent()._make_mimedata_for_items(items)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime)
        drag.exec(QtCore.Qt.DropAction.CopyAction)

    def _download_items(
        self,
        items: list[QtW.QTreeWidgetItem],
        download_dir: Path | None = None,
    ):
        """Save the selected items to local files."""
        if download_dir is None:
            download_dir = self.parent()._ui.exec_file_dialog(
                "d", caption="Select the directory to download files to"
            )
        src_paths: list[Path] = []
        for item in items:
            typ = item_type(item)
            if typ == "l":
                _, real_path = item.text(0).split(" -> ")
                remote_path = self.parent()._pwd / real_path
            else:
                remote_path = self.parent()._pwd / item.text(0)
            src_paths.append(remote_path)

        readers = self.parent()._make_reader_methods_for_items(items)
        worker = make_paste_remote_files_worker(readers, download_dir)
        qui = self.parent()._ui._backend_main_window
        qui._job_stack.add_worker(worker, "Downloading files", total=len(src_paths))
        if self.parent()._force_sync:
            worker.run()
        else:
            worker.start()

    def _apply_filter(self, text: str):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            ok = all(part in item.text(0).lower() for part in text.lower().split(" "))
            item.setHidden(not ok)

    if TYPE_CHECKING:

        def parent(self) -> QBaseRemoteExplorerWidget: ...


class QFilterLineEdit(QtW.QLineEdit):
    """Line edit for filtering items in the remote explorer."""

    def __init__(self, parent: QBaseRemoteExplorerWidget):
        super().__init__(parent)
        self.setPlaceholderText("Filter files...")

    def keyPressEvent(self, a0):
        if a0.key() == QtCore.Qt.Key.Key_Escape:
            self.clear()
            self.setVisible(False)
            return
        return super().keyPressEvent(a0)

    def toggle(self):
        visible = self.isVisible()
        self.setVisible(not visible)
        if not visible:
            self.setFocus()


class QEditFileNameLineEdit(QtW.QLineEdit):
    """Line edit for editing file names in the remote explorer."""

    text_edited = QtCore.Signal(str)

    def __init__(self, parent: QBaseRemoteExplorerWidget):
        super().__init__(parent)
        self.setPlaceholderText("Enter new file name...")
        self.setFont(QtGui.QFont(MonospaceFontFamily))
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, a0):
        if a0.key() == QtCore.Qt.Key.Key_Escape:
            self.reset()
            return
        if a0.key() == QtCore.Qt.Key.Key_Return:
            new_name = self.text()
            if new_name:
                self.text_edited.emit(new_name)
            else:
                raise ValueError("File name cannot be empty.")
            self.reset()
            return
        if a0.key() in (QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down):
            self.reset()
            return
        return super().keyPressEvent(a0)

    def focusOutEvent(self, a0: QtGui.QFocusEvent):
        """Handle focus out event to hide the line edit."""
        self.setVisible(False)
        self.clear()
        super().focusOutEvent(a0)
        self.parentWidget().setFocus()

    def reset(self):
        """Reset the line edit to its initial state."""
        self.clear()
        self.setVisible(False)

    if TYPE_CHECKING:

        def parent(self) -> QRemoteTreeWidget: ...


def item_type(item: QtW.QTreeWidgetItem) -> Literal["d", "l", "f"]:
    """First character of the permission string."""
    return item.text(6)[0]


@lru_cache(maxsize=10)
def icon_for_file_type(file_type: str, light_background: bool) -> QColoredSVGIcon:
    color = "#222222" if light_background else "#eeeeee"
    if file_type == "d":
        svg_path = ICON_PATH / "explorer_folder.svg"
    elif file_type == "l":
        svg_path = ICON_PATH / "explorer_symlink.svg"
    else:
        svg_path = ICON_PATH / "explorer_file.svg"
    return QColoredSVGIcon.fromfile(svg_path, color=color)


@thread_worker
def make_paste_remote_files_worker(
    readers: list[PathReaderMethod],
    dirpath: Path,
):
    for reader in readers:
        if isinstance(reader.path, Path):
            paths = [reader.path]
        else:
            paths = reader.path
        for path in paths:
            stem = path.stem
            ext = path.suffix
            suffix = 0
            dst = dirpath / f"{stem}{ext}"
            while dst.exists():
                dst = dirpath / f"{stem}_{suffix}{ext}"
                suffix += 1
            reader.run_command(dst)
            if dst.exists():
                dst.touch()
            yield


def ls_args_to_items(args: list[str]) -> Iterator[QtW.QTreeWidgetItem]:
    result = subprocess.run(args, capture_output=True)
    if result.returncode != 0:
        raise ValueError(f"Failed to list directory: {result.stderr.decode()}")
    rows = result.stdout.decode().splitlines()

    # format of `ls -l` is:
    # <permission> <link> <owner> <group> <size> <month> <day> <time> <name>
    for row in rows[1:]:  # the first line is total size
        *others, month, day, time, name = row.split(maxsplit=8)
        datetime = f"{month} {day} {time}"
        if name.endswith("*"):
            name = name[:-1]  # executable
        item = QtW.QTreeWidgetItem([name, datetime] + others[::-1])
        yield item


def stat_args_to_type(args: list[str]) -> Literal["d", "f"]:
    result = subprocess.run(args, capture_output=True)
    if result.returncode != 0:
        raise ValueError(f"Failed to get type: {result.stderr.decode()}")
    typ = result.stdout.decode().strip()
    if typ == "directory":
        return "d"
    else:
        return "f"


def exec_command(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True)
    if result.returncode != 0:
        cmd = " ".join(args)
        raise ValueError(f"Failed to execute command {cmd}: {result.stderr.decode()}")
