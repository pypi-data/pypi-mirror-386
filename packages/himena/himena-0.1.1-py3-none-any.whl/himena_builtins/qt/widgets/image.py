from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import math
from typing import TYPE_CHECKING, Any, Callable, NamedTuple
import warnings
import dataclasses
from qtpy import QtWidgets as QtW
from qtpy import QtGui, QtCore
from qtpy.QtCore import Qt
import numpy as np
from cmap import Colormap
from superqt import ensure_main_thread, QToggleSwitch

from himena.consts import StandardType
from himena.standards import roi, model_meta
from himena.qt._utils import drag_command, qsignal_blocker
from himena.types import DropResult, Parametric, Size, WidgetDataModel
from himena.plugins import validate_protocol, register_function
from himena.widgets import set_status_tip, current_instance, show_tooltip
from himena.data_wrappers import ArrayWrapper, wrap_array
from himena_builtins.qt.widgets._image_components import (
    QImageGraphicsView,
    QRoi,
    QRoiButtons,
    QImageViewControl,
    QImageLabelViewControl,
    QImageViewControlBase,
    QRoiCollection,
    from_standard_roi,
    MouseMode,
    ChannelMode,
)
from himena_builtins.qt.widgets._dim_sliders import QDimsSlider
from himena_builtins.qt.widgets._splitter import QSplitterHandle
from himena_builtins.qt.widgets._shared import quick_min_max

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from himena.style import Theme


class QImageViewBase(QtW.QSplitter):
    _executor = ThreadPoolExecutor(max_workers=1)
    images_changed = QtCore.Signal(list)
    current_roi_updated = QtCore.Signal(object)
    """Emit current QRoi or None if no ROI is active."""

    def __init__(self):
        super().__init__(QtCore.Qt.Orientation.Horizontal)

        widget_left = QtW.QWidget()
        self.addWidget(widget_left)
        layout = QtW.QVBoxLayout(widget_left)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self._stick_grid_switch = QToggleSwitch()
        self._stick_grid_switch.setText("Stick to Grid")
        self._stick_grid_switch.setChecked(True)
        self._stick_grid_switch.setToolTip(
            "If checked, vertices of Rectangle and Ellipse ROIs will stick to the\n"
            "grid of the image."
        )
        self._img_view = QImageGraphicsView()
        self._roi_buttons = QRoiButtons(self)
        self._img_view.set_stick_to_grid(True)
        self._img_view.hovered.connect(self._on_hovered)
        self._img_view.roi_visibility_changed.connect(self._roi_visibility_changed)
        self._stick_grid_switch.toggled.connect(self._img_view.set_stick_to_grid)
        self._dims_slider = QDimsSlider()
        self._roi_col = QRoiCollection(self)
        self._roi_col.roi_update_requested.connect(self._update_rois)
        self._roi_col.layout().insertWidget(0, self._roi_buttons)
        self._roi_col.layout().insertWidget(1, self._stick_grid_switch)
        layout.addWidget(self._img_view)
        layout.addWidget(self._dims_slider)

        self._img_view.roi_added.connect(self._on_roi_added)
        self._img_view.roi_removed.connect(self._on_roi_removed)
        self._img_view.current_roi_updated.connect(self._emit_current_roi)
        self._img_view.wheel_moved.connect(self._wheel_event)
        self._dims_slider.valueChanged.connect(self._slider_changed)

        self.addWidget(self._roi_col)
        self.setStretchFactor(0, 6)
        self.setStretchFactor(1, 1)
        self.setSizes([400, 0])
        self._control = self._make_control_widget()
        self._arr: ArrayWrapper | None = None  # the internal array data for display
        self._is_modified = False  # whether the widget is modified
        self._is_editable = True
        # cached ImageTuples for display
        self._current_image_slices: list[ImageTuple] | None = None
        self._is_rgb = False  # whether the image is RGB
        self._channel_axis: int | None = None
        self._channels: list[ChannelInfo] = [ChannelInfo(name="")]
        self._model_type: str = StandardType.IMAGE
        self._pixel_unit: str = "a.u."
        self._extension_default: str = ".png"
        self._original_title: str | None = None
        self._last_slice_future: Future | None = None
        self._cfg = ImageViewConfigs()

    def createHandle(self):
        return QSplitterHandle(self)

    @property
    def dims_slider(self) -> QDimsSlider:
        """Return the dimension slider widget."""
        return self._dims_slider

    @validate_protocol
    def update_model(self, model: WidgetDataModel):
        self._model_type = model.type
        arr = wrap_array(model.value)
        self._original_title = model.title
        is_initialized = self._arr is not None
        is_same_dimensionality = is_initialized and arr.ndim == self._arr.ndim
        is_same_array = is_initialized and (self._arr.arr is model.value)
        ndim_rem = arr.ndim - 2

        # override widget state if metadata is available
        meta0 = model_meta.ImageMeta(
            axes=arr.infer_axes(),
            channels=[model_meta.ImageChannel(colormap=self._default_colormap().name)],
            interpolation="nearest",
            is_rgb=False,
            unit="a.u.",
        )
        self._arr = arr
        if isinstance(meta := model.metadata, model_meta.ImageMeta):
            _update_meta(meta0, meta)
            if meta.is_rgb:
                ndim_rem -= 1

        self._is_rgb = meta0.is_rgb
        if is_initialized:
            sl_old = self._dims_slider.value()
        else:
            sl_old = None
        sl_0 = self._calc_current_indices(arr, meta0, is_same_dimensionality)
        is_sl_same = sl_0 == sl_old

        # update sliders
        if not is_same_array:
            self._dims_slider.set_dimensions(arr.shape, meta0.axes, is_rgb=self._is_rgb)
        elif meta0.axes:
            self._dims_slider.set_axis_names([axis.name for axis in meta0.axes])
        with qsignal_blocker(self._dims_slider):
            self._dims_slider.setValue(sl_0)
        axis_names = [meta0.axes[i].name for i in range(self._dims_slider.count())]
        self._roi_col._qroi_list = self._roi_col._qroi_list.coerce_dimensions(
            axis_names
        )

        # update scale bar
        if (axes := meta0.axes) is not None:
            xaxis = axes[-2] if self._is_rgb else axes[-1]
            self._img_view._scale_bar_widget.update_scale_bar(
                scale=xaxis.scale, unit=xaxis.unit
            )

        # update channel info
        if meta0.channel_axis is None or meta0.is_rgb:
            nchannels = 1
        else:
            nchannels = arr.shape[meta0.channel_axis]

        self._img_view.set_n_images(nchannels)
        if meta0.is_rgb:
            self._channel_axis = None  # override channel axis for RGB images
        else:
            self._channel_axis = meta0.channel_axis

        with qsignal_blocker(self._control):
            self._control.update_rgb_channel_dtype(
                is_rgb=self._is_rgb,
                nchannels=nchannels,
                dtype=arr.dtype,
            )

        self._init_channels(meta0, nchannels, arr.dtype)

        if is_same_array and is_sl_same and self._current_image_slices is not None:
            img_slices = self._current_image_slices
        else:
            img_slices = self._get_image_slices(sl_0, nchannels)
        self._update_channels(meta0, img_slices, nchannels)
        if not meta0.skip_image_rerendering:
            self._set_image_slices(img_slices)

        # ROIs
        roi_list = meta0.unwrap_rois()
        if len(roi_list) > 0:
            self._roi_col.clear()
            self._roi_col.extend_from_standard_roi_list(
                roi_list.coerce_dimensions(axis_names)
            )
            self._update_rois()
        if cur_roi := meta0.current_roi:
            self._img_view.remove_current_item(reason="update_model")
            if meta0.current_roi_index is None:
                qroi = from_standard_roi(cur_roi, self._img_view._roi_pen)
                self._img_view.set_current_roi(qroi)
            else:
                qroi = self._roi_col._qroi_list[meta0.current_roi_index]
                self._img_view.select_item(qroi, is_registered_roi=True)
            self._img_view.set_mode(MouseMode.from_roi(qroi))
            self._img_view._selection_handles.connect_roi(qroi)

        # other settings
        self._control._interp_check_box.setChecked(meta0.interpolation == "linear")
        self._pixel_unit = meta0.unit or ""
        if ext_default := model.extension_default:
            self._extension_default = ext_default
        if meta0.play_setting is not None:
            self._dims_slider.set_play_setting(meta0.play_setting)
        self.set_hover_info(self._default_hover_info())
        return None

    @validate_protocol
    def update_value(self, val):
        arr = wrap_array(val)
        if arr.shape != self._arr.shape:
            raise ValueError(
                "`QImageView.update_value` does not support updating the array shape. "
                "Please use `update_model` with `WidgetDataModel` instead."
            )
        self._arr = arr
        self._reset_image()
        self.set_hover_info(self._default_hover_info())

    def _get_image_slices(
        self,
        value: tuple[int, ...],
        nchannels: int,
    ) -> list[ImageTuple]:
        """Get numpy arrays for each channel (None mean hide the channel)."""
        return [ImageTuple(self._get_image_slice_for_channel(value))]

    def _set_image_slice(self, img: NDArray[np.number], channel: ChannelInfo):
        raise NotImplementedError

    def _set_image_slices(self, imgs: list[ImageTuple]):
        """Set image slices using the channel information.

        This method is only used for updating the entire image slices. Channels must be
        correctly set before calling this method, as it uses the channel information to
        transform the image slices.
        """
        raise NotImplementedError

    def _clim_for_ith_channel(self, img_slices: list[ImageTuple], ith: int):
        ar0, _ = img_slices[ith]
        return quick_min_max(ar0)

    def _init_channels(self, meta: model_meta.ImageMeta, nchannels: int, dtype):
        if len(meta.channels) != nchannels:
            ch0 = meta.channels[0]
            channels = [
                ch0.model_copy(update={"colormap": None, "contrast_limits": (0, 1)})
                for _ in range(nchannels)
            ]
        else:
            channels = [
                ch.model_copy(update={"contrast_limits": (0, 1)})
                for ch in meta.channels
            ]
        names = _channel_names(meta, nchannels)
        self._channels = [
            ChannelInfo.from_channel(i, names[i], c) for i, c in enumerate(channels)
        ]

    def _emit_current_roi(self):
        self.current_roi_updated.emit(self._img_view._current_roi_item)
        try:
            idx = self._img_view._roi_items.index(self._img_view._current_roi_item)
        except ValueError:
            pass
        else:
            indices = self._dims_slider.value()
            idx_total = self._roi_col.index_in_slice(indices, idx)
            self._roi_col.set_selections([idx_total])

    def _make_control_widget(self) -> QImageViewControlBase:
        raise NotImplementedError

    def _default_colormap(self) -> Colormap:
        raise NotImplementedError

    def _update_channels(
        self,
        meta: model_meta.ImageMeta,
        img_slices: list[ImageTuple],
        nchannels: int,
    ):
        # before calling ChannelInfo.from_channel, contrast_limits must be set
        if len(meta.channels) != nchannels:
            ch0 = meta.channels[0]
            ch0.contrast_limits = self._clim_for_ith_channel(img_slices, 0)
            channels = [
                ch0.model_copy(update={"colormap": None}) for _ in range(nchannels)
            ]
        else:
            channels = meta.channels
            for i, ch in enumerate(channels):
                if ch.contrast_limits is None:
                    ch.contrast_limits = self._clim_for_ith_channel(img_slices, i)
        names = _channel_names(meta, nchannels)
        self._channels = [
            ChannelInfo.from_channel(i, names[i], c) for i, c in enumerate(channels)
        ]
        if len(self._channels) == 1 and channels[0].colormap is None:
            # ChannelInfo.from_channel returns a single green colormap but it should
            # be gray for single channel images.
            self._channels[0].colormap = self._default_colormap()

    def _calc_current_indices(
        self,
        arr_new: ArrayWrapper,
        meta0: model_meta.ImageMeta,
        is_same_dimensionality: bool,
    ):
        ndim_rem = arr_new.ndim - 3 if meta0.is_rgb else arr_new.ndim - 2
        if meta0.current_indices is not None:
            sl_0 = tuple(force_int(_i) for _i in meta0.current_indices[:ndim_rem])
        elif is_same_dimensionality:
            sl_0 = self._dims_slider.value()
        else:
            if meta0.axes:
                axis_names = [axis.name for axis in meta0.axes][:ndim_rem]
                sl_0 = tuple(
                    size // 2 if aname.lower() == "z" else 0
                    for aname, size in zip(axis_names, arr_new.shape)
                )
            else:
                sl_0 = (0,) * ndim_rem
        # the indices should be in the valid range
        return tuple(
            min(max(0, s), size - 1) for s, size in zip(sl_0, arr_new.shape[:ndim_rem])
        )

    @ensure_main_thread
    def _set_image_slices_async(self, future: Future[list[ImageTuple]]):
        self._last_slice_future = None
        if future.cancelled():
            return
        imgs = future.result()
        self._set_image_slices(imgs)

    def current_roi(self) -> roi.RoiModel | None:
        """Return the current ROI as a standard ROI model."""
        if item := self._img_view._current_roi_item:
            current_roi = item.toRoi()
        else:
            current_roi = None
        return current_roi

    @validate_protocol
    def to_model(self) -> WidgetDataModel:
        assert self._arr is not None

        if self._control._interp_check_box.isChecked():
            interp = "linear"
        else:
            interp = "nearest"
        channels = [
            model_meta.ImageChannel(contrast_limits=ch.clim, colormap=ch.colormap.name)
            for ch in self._channels
        ]
        current_indices = self._dims_slider.value()
        current_slices = current_indices + (None, None)
        axes = self._dims_slider.to_dim_axes()
        if self._is_rgb:
            axes.append(model_meta.DimAxis(name="RGB"))
        current_roi = self.current_roi()
        if (
            current_roi is not None
            and not self._img_view._is_current_roi_item_not_registered
            and (sels := self._roi_col.selections())
        ):
            # is the current ROI is already registered, use the index (see the
            # ImageMeta standard)
            current_roi_index = sels[-1]
        else:
            current_roi_index = None
        return WidgetDataModel(
            value=self._arr.arr,
            type=self.model_type(),
            extension_default=self._extension_default,
            metadata=model_meta.ImageMeta(
                current_indices=current_slices,
                axes=axes,
                channels=channels,
                channel_axis=self._channel_axis,
                current_roi=current_roi,
                current_roi_index=current_roi_index,
                rois=self._roi_col.to_standard_roi_list,
                is_rgb=self._is_rgb,
                interpolation=interp,
                play_setting=self._dims_slider.to_play_setting(),
                unit=self._pixel_unit,
            ),
        )

    @validate_protocol
    def model_type(self) -> str:
        return self._model_type

    @validate_protocol
    def size_hint(self) -> tuple[int, int]:
        return 400, 400

    @validate_protocol
    def is_editable(self) -> bool:
        return self._is_editable

    @validate_protocol
    def set_editable(self, editable: bool):
        self._is_editable = editable

    @validate_protocol
    def control_widget(self) -> QImageViewControl:
        return self._control

    @validate_protocol
    def allowed_drop_types(self) -> list[str]:
        return [StandardType.ROIS, StandardType.IMAGE_LABELS]

    @validate_protocol
    def dropped_callback(self, model: WidgetDataModel):
        if model.type == StandardType.ROIS:
            # dropping ROIs to concatenate to the current ROI list
            if isinstance(roi_list := model.value, roi.RoiListModel):
                self._roi_col.extend_from_standard_roi_list(roi_list)
                self._update_rois()
            self._is_modified = True
            return DropResult(delete_input=False)
        elif model.type == StandardType.IMAGE_LABELS:
            raise NotImplementedError("Merging with labels is not implemented yet.")
        return None

    @validate_protocol
    def widget_resized_callback(self, old: Size, new: Size):
        self._img_view.resize_event(old, new)

    @validate_protocol
    def widget_added_callback(self):
        self._img_view.auto_range()
        self._img_view.update_handle_sizes()

    def setFocus(self):
        return self._img_view.setFocus()

    def leaveEvent(self, ev) -> None:
        self.set_hover_info(self._default_hover_info())

    def _roi_visibility_changed(self, show_rois: bool):
        with qsignal_blocker(self._roi_col):
            self._roi_col._roi_visible_btn.setChecked(show_rois)

    def _update_image_visibility(self, visible: list[bool]):
        slices = self._current_image_slices
        if slices is None:
            return
        for i, vis in enumerate(visible):
            if i < len(slices):
                slices[i] = ImageTuple(slices[i].arr, vis)
        self._set_image_slices(slices)

    def _get_image_slice_for_channel(
        self, value: tuple[int, ...]
    ) -> NDArray[np.number]:
        """Get numpy array for current channel."""
        return self._arr.get_slice(tuple(value))

    def _slider_changed(self, value: tuple[int, ...], *, force_sync: bool = False):
        """Callback for slider value change."""
        if self._arr is None:
            return
        if self._last_slice_future:
            self._last_slice_future.cancel()  # cancel last task
        if force_sync:
            img_slices = self._get_image_slices(value, len(self._channels))
            self._set_image_slices(img_slices)
        else:
            # set slice asynchronously
            self._last_slice_future = self._executor.submit(
                self._get_image_slices, value, len(self._channels)
            )
            self._last_slice_future.add_done_callback(self._set_image_slices_async)

    def _update_rois(self):
        cur_item = self._img_view._current_roi_item
        self._img_view.clear_rois()
        rois = self._roi_col.get_rois_on_slice(self._dims_slider.value())
        self._img_view.extend_qrois(rois, cur_item)

    def current_channel(self, slider_value: tuple[int] | None = None) -> ChannelInfo:
        """Get the current channel info.

        This method always returns a channel, as even a monochrome image is set with a
        gray colormap.
        """
        if slider_value is None:
            _slider_value = self._dims_slider.value()
        else:
            _slider_value = slider_value
        if self._channel_axis is not None:
            ith = _slider_value[self._channel_axis]
            ch = self._channels[ith]
        else:
            ch = self._channels[0]
        return ch

    def _on_roi_added(self, qroi: QRoi):
        if qroi.label() == "":
            qroi.set_label(roi.default_roi_label(len(self._roi_col)))
        indices = self._dims_slider.value()
        self._roi_col.add(indices, qroi)
        set_status_tip(f"Added a {qroi._roi_type()} ROI")

    def _on_roi_removed(self, idx: int):
        indices = self._dims_slider.value()
        qroi = self._roi_col.pop_roi_in_slice(indices, idx)
        set_status_tip(f"Removed a {qroi._roi_type()} ROI")
        self._roi_col.set_selections([])  # deselect

    def _reset_image(self):
        if self._channels is None:  # not initialized yet
            return
        imgs = self._get_image_slices(self._dims_slider.value(), len(self._channels))
        self._set_image_slices(imgs)

    def _on_hovered(self, pos: QtCore.QPointF):
        """Update hover info by the pixel position and value."""
        x, y = pos.x(), pos.y()
        if self._current_image_slices is None:
            return
        iy, ix = int(y), int(x)
        idx = self.current_channel().channel_index or 0
        cur_img = self._current_image_slices[idx]
        ny, nx, *_ = cur_img.arr.shape
        if 0 <= iy < ny and 0 <= ix < nx:
            if not cur_img.visible:
                self.set_hover_info(f"x={x:.1f}, y={y:.1f} (invisible)")
                return
            intensity = cur_img.arr[int(y), int(x)]
            # NOTE: `intensity` could be an RGBA numpy array.
            if isinstance(intensity, np.ndarray) or self._arr.dtype.kind == "b":
                _int = str(intensity)
            else:
                if self._arr.dtype.kind == "f":
                    fmt = ".3g"
                else:
                    fmt = ".0f"
                _int = format(intensity, fmt)
            if self._pixel_unit:
                _int += f" [{self._pixel_unit}]"
            yaxis, xaxis = self.dims_slider._yx_axes
            if self._model_type == StandardType.IMAGE_FOURIER:
                kx = (ix - nx // 2) / nx
                ky = (iy - ny // 2) / ny
                xinfo = _fourier_info(kx, xaxis)
                yinfo = _fourier_info(ky, yaxis)
                angle = math.degrees(math.atan2(ky, kx))
                self.set_hover_info(
                    f"kx={xinfo}, ky={yinfo}, theta={angle:.1f} value={_int}"
                )
            else:
                xinfo = _physical_info(ix, xaxis)
                yinfo = _physical_info(iy, yaxis)
                self.set_hover_info(f"x={xinfo}, y={yinfo}, value={_int}")
        else:
            self.set_hover_info(self._default_hover_info())

    def set_hover_info(self, text: str):
        """Set the hover info text to the control widget."""
        self._control._hover_info.setText(text)

    def _default_hover_info(self) -> str:
        if self._arr is None:
            return
        nbytes = self._arr.nbytes
        return f"{self._arr.shape}, {self._arr.dtype}, {_human_readable_size(nbytes)}"

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event is None:
            return None
        _mods = event.modifiers()
        _key = event.key()
        view = self._img_view
        if _mods & Qt.KeyboardModifier.ControlModifier:
            if not event.isAutoRepeat():
                if (
                    event.text().isdigit()
                    and isinstance(self._control, QImageViewControl)
                    and self._control._chn_vis.has_channels()
                    and self._control._chn_mode_combo.currentText() == ChannelMode.COMP
                ):
                    # toggle channel visibility
                    _visible = self._control._chn_vis.check_states()
                    ith = int(event.text()) - 1
                    if 0 <= ith < len(_visible):
                        _visible[ith] = not _visible[ith]
                    elif ith == -1:
                        _visible = [True] * len(_visible)
                    self._control._chn_vis.set_check_states(_visible)
                    self._update_image_visibility(_visible)
                else:
                    view.standard_ctrl_key_press(_key)
        else:
            if _key in _INCREMENT_MAP:
                ui = current_instance()
                for ith, sl in enumerate(self._dims_slider._sliders):
                    if ui.keys.contains(f"{ith + 1}"):
                        sl.increment_value(_INCREMENT_MAP[_key])
            elif event.text() == "^":
                if not event.isAutoRepeat():
                    self.handle(0).toggle()
            else:
                if not event.isAutoRepeat():
                    shift = _mods & Qt.KeyboardModifier.ShiftModifier
                    view.standard_key_press(_key, shift)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent | None) -> None:
        if event is None or event.isAutoRepeat():
            return
        if event.key() == Qt.Key.Key_Space:
            self._img_view.set_mode(self._img_view._last_mode_before_key_hold)

    def _on_drag_roi_requested(self, indices: list[int]):
        nrois = len(indices)
        _s = "" if nrois == 1 else "s"
        return drag_command(
            self,
            command_id=_COMMAND_ID,
            type=StandardType.ROIS,
            with_params={"selections": indices},
            desc=f"{nrois} ROI{_s}",
        )

    def _wheel_event(self, dy):
        ui = current_instance()

        for ith, sl in enumerate(self._dims_slider._sliders):
            if ui.keys.contains(f"{ith + 1}"):
                sl.increment_value(1 if dy > 0 else -1)
                axes = self._dims_slider.to_dim_axes()
                values = self._dims_slider.value()
                txt = "\n".join(f"{a.name} = {v}" for a, v in zip(axes, values))
                show_tooltip(txt, duration=0.4, behavior="until_move")
                break
        else:
            # zoom in/out
            factor = 1.1
            if dy > 0:
                zoom_factor = factor
            else:
                zoom_factor = 1 / factor
            self._img_view.scale_and_update_handles(zoom_factor)
            self._img_view._inform_scale()


_COMMAND_ID = "builtins:select-image-rois"


@register_function(menus=[], command_id=_COMMAND_ID)
def _select_image_rois(model: WidgetDataModel) -> Parametric:
    assert isinstance(meta := model.metadata, model_meta.ImageMeta)
    rois = meta.unwrap_rois()
    axes = meta.axes

    def run_select(selections: list[int]) -> WidgetDataModel:
        if len(selections) == 0:
            raise ValueError("No ROIs selected.")

        return WidgetDataModel(
            value=rois.filter_by_selection(selections),
            type=StandardType.ROIS,
            title=f"Subset of {model.title}",
            metadata=model_meta.ImageRoisMeta(axes=axes),
        )

    return run_select


class QImageView(QImageViewBase):
    """The built-in n-D image viewer widget.

    ## Basic Usage

    The image canvas can be interactively panned by dragging with the left mouse button,
    and zoomed by scrolling the mouse wheel. Zooming is reset by double-click. This
    widget also supports adding ROIs (Regions of Interest) to the image.

    - For multi-dimensional images, dimension sliders will be added to the bottom of the
      image canvas.
    - For multi-channel images, channel composition mode can be selected in the control
      widget. Toggle switches for each channel are available next to it.
    - The histogram of the current channel is displayed in the control widget. The
      contrast limits can be adjusted by dragging the handles on the histogram.
    - A ROI manager is in the right collapsible panel. Press the ROI buttons to switch
      between ROI modes.

    ## Keyboard Shortcuts

    #### Switch ROI Modes

    - `L`: Switch to Line ROI.
    - `Shift+L`: Switch to Segmented Line ROI.
    - `R`: Switch to Rectangle ROI.
    - `Shift+R`: Switch to Rotated Rectangle ROI.
    - `E`: Switch to Ellipse ROI.
    - `Shift+E`: Switch to Rotated Ellipse ROI.
    - `C`: Switch to Circle ROI.
    - `P`: Switch to Point ROI.
    - `Shift+P`: Switch to Multi-Point ROI.
    - `G`: Switch to Polygon ROI.
    - `Z`: Switch to Pan/Zoom Mode.
    - `Space`: Hold this key to temporarily switch to Pan/Zoom Mode.
    - `S`: Switch to Select Mode.

    #### ROI Actions

    - `T`: Add current ROI to the ROI list.
    - `V`: Toggle visibility of all the added ROIs.
    - `Delete` / `Backspace`: Remove the current ROI.
    - `Ctrl+A`: Select the entire image with a rectangle ROI.
    - `Ctrl+X`: Cut the selected ROI.
    - `Ctrl+C`: Copy the selected ROI.
    - `Ctrl+V`: Paste the copied ROI.
    - `Ctrl+D`: Duplicate the selected ROI.

    #### Dimension Sliders

    - `1+←`/`1+→`: Decrement/Increment the first dimension slider.
    - `2+←`/`2+→`: Decrement/Increment the second dimension slider.
    and so on.

    #### View

    - `Ctrl+↑`: Zoom in.
    - `Ctrl+↓`: Zoom out.

    ## Drag and Drop

    - This widget accepts dropping models with `StandardType.ROIS` ("rois").
      Dropped ROIs will be added to the ROI list.
    - ROIs can be dragged out from the ROI manager. The type of the dragged model is
      `StandardType.ROIS` ("rois"). Use the drag indicator in the corner of the ROI
      list.
    """

    __himena_widget_id__ = "builtins:QImageView"
    __himena_display_name__ = "Built-in Image Viewer"
    _control: QImageViewControl

    @validate_protocol
    def theme_changed_callback(self, theme: Theme):
        if theme.name.startswith("light"):
            color = QtGui.QColor(0, 0, 0)
        else:
            color = QtGui.QColor(255, 255, 255)
        self._roi_buttons._update_colors(color)

    @validate_protocol
    def update_configs(self, cfg: ImageViewConfigs):
        self._cfg = cfg
        self._img_view.set_stick_to_grid(cfg.default_stick_to_grid)
        self._img_view.set_show_rois(cfg.default_show_all)
        self._img_view.set_show_labels(cfg.default_show_labels)
        self._img_view._selection_handles._handle_size = cfg.roi_handle_size

    def _make_control_widget(self) -> QImageViewControl:
        return QImageViewControl(self)

    def _default_colormap(self) -> Colormap:
        return Colormap("gray")

    def _update_channels(self, meta, img_slices, nchannels):
        super()._update_channels(meta, img_slices, nchannels)
        if self._composite_state() == "Comp.":
            self._control._chn_vis.set_channels(self._channels)

    def _composite_state(self) -> str:
        return self._control._chn_mode_combo.currentText()

    def _get_image_slices(
        self,
        value: tuple[int, ...],
        nchannels: int,
    ) -> list[ImageTuple]:
        """Get numpy arrays for each channel (None mean hide the channel)."""
        if self._channel_axis is None:
            return super()._get_image_slices(value, nchannels)

        img_slices = []
        check_states = self._control._channel_visibility()
        for i in range(nchannels):
            vis = i >= len(check_states) or check_states[i]
            sl = list(value)
            sl[self._channel_axis] = i
            img_slices.append(ImageTuple(self._get_image_slice_for_channel(sl), vis))
        return img_slices

    def _set_image_slice(self, img: NDArray[np.number], channel: ChannelInfo):
        idx = channel.channel_index or 0
        with qsignal_blocker(self._control._histogram):
            self._img_view.set_array(
                idx,
                channel.transform_image(
                    img,
                    complex_transform=self._control.complex_transform,
                    is_rgb=self._is_rgb,
                    is_gray=self._composite_state() == "Gray",
                ),
            )
            self._img_view.clear_rois()
            self._control._histogram.set_hist_for_array(
                img,
                clim=channel.clim,
                is_rgb=self._is_rgb,
                color=color_for_colormap(channel.colormap),
            )
        if self._current_image_slices is not None:
            visible = self._current_image_slices[idx].visible
        else:
            visible = True
        self._current_image_slices[idx] = ImageTuple(img, visible)
        self.images_changed.emit(self._current_image_slices)

    def _set_image_slices(self, imgs: list[ImageTuple]):
        """Set image slices using the channel information.

        This method is only used for updating the entire image slices. Channels must be
        correctly set before calling this method, as it uses the channel information to
        transform the image slices.
        """
        self._current_image_slices = imgs
        if self._channels is None:
            return
        images: list[NDArray[np.number] | None] = []
        with qsignal_blocker(self._control._histogram):
            for i, (imtup, ch) in enumerate(zip(imgs, self._channels)):
                if imtup.visible:
                    img = imtup.arr
                else:
                    img = None
                images.append(img)
                self._img_view.set_array(
                    i,
                    ch.transform_image(
                        img,
                        complex_transform=self._control.complex_transform,
                        is_rgb=self._is_rgb,
                        is_gray=self._composite_state() == "Gray",
                    ),
                )
            ch_cur = self.current_channel()
            idx = ch_cur.channel_index or 0
            hist_arr_ref = imgs[idx].arr
            if hist_arr_ref.dtype.kind == "c":
                hist_arr_ref = self._control.complex_transform(hist_arr_ref)
            self._control._histogram.set_hist_for_array(
                hist_arr_ref,
                clim=ch_cur.clim,
                is_rgb=self._is_rgb,
                color=color_for_colormap(ch_cur.colormap),
            )
            self._update_rois()
            self._img_view.set_image_blending([im.visible for im in imgs])
        self.images_changed.emit(images)

    def _clim_for_ith_channel(self, img_slices: list[ImageTuple], ith: int):
        ar0, _ = img_slices[ith]
        if ar0.dtype.kind == "c":
            ar0 = self._control.complex_transform(ar0)
        return quick_min_max(ar0)


class QImageLabelView(QImageViewBase):
    """The default nD image label viewer widget.

    Unlink the image viewer, this widget displays image labels by discrete colors.

    ## Basic Usage

    The image canvas can be interactively panned by dragging with the left mouse button,
    and zoomed by scrolling the mouse wheel. Zooming is reset by double-click. This
    widget also supports adding ROIs (Regions of Interest) to the image.

    - For multi-dimensional images, dimension sliders will be added to the bottom of the
      image canvas.
    - For multi-channel images, channel composition mode can be selected in the control
      widget. Toggle switches for each channel are available next to it.
    - The histogram of the current channel is displayed in the control widget. The
      contrast limits can be adjusted by dragging the handles on the histogram.
    - A ROI manager is in the right collapsible panel. Press the ROI buttons to switch
      between ROI modes.

    ## Keyboard Shortcuts

    - `L`: Switch to Line ROI.
    - `Shift+L`: Switch to Segmented Line ROI.
    - `R`: Switch to Rectangle ROI.
    - `Shift+R`: Switch to Rotated Rectangle ROI.
    - `E`: Switch to Ellipse ROI.
    - `Shift+E`: Switch to Rotated Ellipse ROI.
    - `C`: Switch to Circle ROI.
    - `P`: Switch to Point ROI.
    - `Shift+P`: Switch to Multi-Point ROI.
    - `G`: Switch to Polygon ROI.
    - `Z`: Switch to Pan/Zoom Mode.
    - `Space`: Hold this key to temporarily switch to Pan/Zoom Mode.
    - `S`: Switch to Select Mode.
    - `T`: Add current ROI to the ROI list.
    - `V`: Toggle visibility of all the added ROIs.
    - `Delete` / `Backspace`: Remove the current ROI.
    - `Ctrl+A`: Select the entire image with a rectangle ROI.
    - `Ctrl+X`: Cut the selected ROI.
    - `Ctrl+C`: Copy the selected ROI.
    - `Ctrl+V`: Paste the copied ROI.
    - `Ctrl+D`: Duplicate the selected ROI.

    ## Drag and Drop

    - This widget accepts dropping models with `StandardType.IMAGE_ROIS` ("image-rois").
      Dropped ROIs will be added to the ROI list.
    - ROIs can be dragged out from the ROI manager. The type of the dragged model is
      `StandardType.IMAGE_ROIS` ("image-rois"). Use the drag indicator in the corner of
      the ROI list.
    """

    __himena_widget_id__ = "builtins:QImageLabelView"
    __himena_display_name__ = "Built-in Image Label Viewer"
    _control: QImageLabelViewControl

    def _default_colormap(self) -> Colormap:
        return Colormap("gnuplot:rainbow")

    def _make_control_widget(self) -> QImageLabelViewControl:
        return QImageLabelViewControl(self)

    def _get_opacity(self) -> float:
        return self._control._opacity_slider.value()

    def _set_image_slice(self, img: NDArray[np.number], channel: ChannelInfo):
        idx = channel.channel_index or 0
        self._img_view.set_array(
            idx, channel.transform_labels(img, opacity=self._get_opacity())
        )
        self._img_view.clear_rois()
        self._current_image_slices[idx] = ImageTuple(img)

    def _set_image_slices(self, imgs: list[ImageTuple]):
        """Set image slices using the channel information.

        This method is only used for updating the entire image slices. Channels must be
        correctly set before calling this method, as it uses the channel information to
        transform the image slices.
        """
        self._current_image_slices = imgs
        if self._channels is None:
            return
        for i, (imtup, ch) in enumerate(zip(imgs, self._channels)):
            self._img_view.set_array(
                i, ch.transform_labels(imtup.arr, opacity=self._get_opacity())
            )
        self._update_rois()
        self._img_view.set_image_blending([im.visible for im in imgs])


@dataclasses.dataclass
class ChannelInfo:
    name: str
    clim: tuple[float, float] = dataclasses.field(default=(0.0, 1.0))
    colormap: Colormap = dataclasses.field(default_factory=lambda: Colormap("gray"))
    channel_index: int | None = None

    def transform_image(
        self,
        arr: NDArray[np.number] | None,
        complex_transform: Callable[
            [NDArray[np.complexfloating]], NDArray[np.number]
        ] = np.abs,
        is_rgb: bool = False,
        is_gray: bool = False,
    ) -> NDArray[np.uint8] | None:
        """Convenience method to transform the array to a displayable RGBA image."""
        if is_rgb:
            return self.transform_image_rgb(arr, is_gray=is_gray)
        else:
            if is_gray:
                return self.as_gray().transform_image(arr, complex_transform)
            return self.transform_image_2d(arr, complex_transform)

    def transform_labels(
        self,
        arr: NDArray[np.uint] | None,
        opacity: float = 0.7,
        period: int = 256,
    ) -> NDArray[np.uint8] | None:
        """Transform an uint array to a displayable RGBA image."""
        if arr is None:
            return None
        mask_background = arr == 0
        if arr.dtype == np.uint8:
            # NOTE: arr % 256 raises OverflowError for arr.dtype == np.uint8.
            arr_index = arr.copy()
        else:
            arr_index = np.empty(arr.shape, dtype=np.uint8)
            np.mod(arr - 1, period, out=arr_index)
        arr_index *= 109
        arr_normed = self.colormap(arr_index, N=period, bytes=True)
        arr_normed[:, :, 3] = int(255 * opacity)
        arr_normed[mask_background] = 0
        out = np.ascontiguousarray(arr_normed)
        return out

    def transform_image_2d(
        self,
        arr: NDArray[np.number] | None,
        complex_transform: Callable[[NDArray[np.complexfloating]], NDArray[np.number]],
    ) -> NDArray[np.uint8] | None:
        """Transform the array to a displayable RGBA image."""
        if arr is None:
            return None
        if arr.ndim == 3:
            return arr  # RGB
        cmin, cmax = self.clim
        if arr.dtype.kind == "c":
            arr = complex_transform(arr)
        if arr.dtype.kind == "b":
            false_color = (np.array(self.colormap(0.0).rgba) * 255).astype(np.uint8)
            true_color = (np.array(self.colormap(1.0).rgba) * 255).astype(np.uint8)
            arr_normed = np.where(arr[..., np.newaxis], true_color, false_color)
        elif cmax > cmin:
            arr = arr.clip(cmin, cmax)
            arr_normed = (self.colormap((arr - cmin) / (cmax - cmin)) * 255).astype(
                np.uint8
            )
        else:
            color = np.array(self.colormap(0.5).rgba8, dtype=np.uint8)
            arr_normed = np.empty(arr.shape + (4,), dtype=np.uint8)
            arr_normed[:] = color[np.newaxis, np.newaxis]
        out = np.ascontiguousarray(arr_normed)
        assert out.dtype == np.uint8
        return out

    def transform_image_rgb(
        self,
        arr: NDArray[np.number] | None,
        is_gray: bool = False,
    ):
        """Transform the RGBA array to a displayable RGBA image."""
        if arr is None:
            return None
        cmin, cmax = self.clim
        if cmax == cmin:
            amp = 128
        else:
            amp = 255 / (cmax - cmin)
        if is_gray:
            # make a gray image
            arr_gray = arr[..., 0] * 0.3 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11
            arr_gray = arr_gray.astype(np.uint8)
            if arr.shape[2] == 4:
                alpha = arr[..., 3]
            else:
                alpha = np.full(arr_gray.shape, 255, dtype=np.uint8)
            arr = np.stack([arr_gray, arr_gray, arr_gray, alpha], axis=-1)
        if (cmin, cmax) == (0, 255):
            arr_normed = arr
        else:
            if arr.shape[2] == 3:
                arr_normed = ((arr - cmin) * amp).clip(0, 255).astype(np.uint8)
            else:
                arr_normed = arr.copy()
                if is_gray:
                    sl = slice(None)
                else:
                    sl = (slice(None), slice(None), slice(None, 3))
                arr_normed[sl] = ((arr[sl] - cmin) * amp).clip(0, 255).astype(np.uint8)
        return arr_normed

    def as_gray(self) -> ChannelInfo:
        return ChannelInfo(
            name=self.name,
            clim=self.clim,
            colormap=Colormap("gray"),
            channel_index=self.channel_index,
        )

    @classmethod
    def from_channel(
        cls,
        idx: int,
        name: str,
        channel: model_meta.ImageChannel,
    ) -> ChannelInfo:
        input_clim = channel.contrast_limits
        if input_clim is None:
            raise ValueError("Contrast limits are not set.")
        if channel.colormap is None:
            colormap = Colormap(f"cmap:{_DEFAULT_COLORMAPS[idx % 6]}")
        else:
            colormap = Colormap(channel.colormap)
        return cls(
            name=name,
            channel_index=idx,
            colormap=colormap,
            clim=channel.contrast_limits,
        )


class ImageTuple(NamedTuple):
    """A layer of image and its visibility."""

    arr: NDArray[np.number]
    visible: bool = True


_DEFAULT_COLORMAPS = ["green", "magenta", "cyan", "yellow", "red", "blue"]


def color_for_colormap(cmap: Colormap) -> QtGui.QColor:
    """Get the representative color for the colormap."""
    return QtGui.QColor.fromRgbF(*cmap(0.5))


def force_int(idx: Any) -> int:
    if isinstance(idx, int):
        return idx
    if hasattr(idx, "__index__"):
        return idx.__index__()
    warnings.warn(f"Cannot convert {idx} to int, using 0 instead.")
    return 0


def _update_meta(meta0: model_meta.ImageMeta, meta: model_meta.ImageMeta):
    if meta.rois:
        meta0.rois = meta.rois
    if meta.axes:
        meta0.axes = meta.axes
    if meta.is_rgb:
        meta0.is_rgb = meta.is_rgb
        meta0.interpolation = "linear"
    if meta.channel_axis is not None:
        meta0.channel_axis = meta.channel_axis
    if meta.current_indices:
        meta0.current_indices = meta.current_indices
    if meta.channels:
        meta0.channels = meta.channels
    if meta.current_roi:
        meta0.current_roi = meta.current_roi
    if meta.unit is not None:
        meta0.unit = meta.unit
    if meta.interpolation:
        meta0.interpolation = meta.interpolation
    if meta.play_setting is not None:
        meta0.play_setting = meta.play_setting
    meta0.current_roi_index = meta.current_roi_index
    meta0.skip_image_rerendering = meta.skip_image_rerendering
    return None


def _channel_names(meta: model_meta.ImageMeta, nchannels: int) -> list[str]:
    if meta.channel_axis is None:
        names = [""]
    elif meta.axes is None:
        names = [f"Ch-{i}" for i in range(nchannels)]
    else:
        names = [meta.axes[meta.channel_axis].get_label(i) for i in range(nchannels)]
    return names


def _physical_info(xpix: float, axis: model_meta.DimAxis) -> str:
    xpos = xpix * axis.scale + axis.origin
    digit = _digits_for_scale(axis.scale)
    if axis.unit:
        return f"{int(xpix)} ({xpos:.{digit}f} {axis.unit})"
    else:
        return f"{int(xpix)} ({xpos:.{digit}f})"


def _fourier_info(kx: float, axis: model_meta.DimAxis) -> str:
    if kx == 0:
        wlen = float("inf")
    else:
        wlen = axis.scale / kx
    digit = _digits_for_scale(axis.scale)
    if axis.unit:
        return f"{kx:.2f} ({wlen:.{digit}f} /c)"
    else:
        return f"{kx:.2f} ({wlen:.{digit}f} {axis.unit}/c)"


def _digits_for_scale(scale: float) -> int:
    if scale < 10:
        return -math.floor(math.log10(scale)) + 1
    else:
        return 0


# copied from `ndv`
def _human_readable_size(nbytes: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    for unit in units:
        if nbytes < 1024:
            return f"{nbytes:.2f}".rstrip("0").rstrip(".") + unit
        nbytes /= 1024.0
    return f"{nbytes:.2f}YB"  # In case nbytes is extremely large


@dataclasses.dataclass
class ImageViewConfigs:
    default_stick_to_grid: bool = dataclasses.field(default=True)
    roi_handle_size: int = dataclasses.field(default=5, metadata={"min": 1, "max": 10})
    default_show_all: bool = dataclasses.field(default=True)
    default_show_labels: bool = dataclasses.field(default=True)


_INCREMENT_MAP = {
    Qt.Key.Key_Left: -1,
    Qt.Key.Key_Right: 1,
    Qt.Key.Key_Home: -10,
    Qt.Key.Key_End: 10,
}
