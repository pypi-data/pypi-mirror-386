from __future__ import annotations

from functools import reduce, singledispatch
from typing import Callable, TypeVar
import warnings
import numpy as np
from numpy.typing import NDArray
from scipy import ndimage as ndi

from himena import WidgetDataModel, Parametric, StandardType, create_model
from himena.widgets import append_result
from himena.plugins import register_function, configure_gui
from himena.standards import roi, model_meta
from himena.data_wrappers import wrap_array, ArrayWrapper
from himena.widgets import SubWindow
from himena_builtins.qt.image import QImageView
from himena_builtins.qt.basic import QDictView

MENUS = ["tools/image/analyze", "/model_menu/analyze"]


@register_function(
    title="Measure At Current ROI",
    types=StandardType.IMAGE,
    menus=MENUS,
    keybindings="M",
    command_id="himena-image:roi-measure-current",
)
def roi_measure_current(model: WidgetDataModel):
    if not isinstance(meta := model.metadata, model_meta.ImageMeta):
        raise ValueError("Image must have an ImageMeta.")
    roi = meta.current_roi
    if roi is None:
        raise ValueError("No ROI selected.")
    output = _measure(model, meta, roi)
    append_result(output)
    return None


@register_function(
    title="Measure At Current ROI (Live)",
    types=StandardType.IMAGE,
    menus=MENUS,
    command_id="himena-image:roi-measure-current-live",
)
def roi_measure_current_live(win: SubWindow[QImageView]):
    """Live-measure the ROI features."""
    dict_view = QDictView()

    def _callback():
        model = win.widget.to_model()
        if not isinstance(meta := model.metadata, model_meta.ImageMeta):
            raise ValueError("Image must have an ImageMeta.")
        if roi := meta.current_roi:
            output = _measure(model, meta, roi)
        else:
            output = {}
        dict_view.update_model(create_model(output, type=StandardType.DICT))

    win.widget.current_roi_updated.connect(_callback)
    win.widget.dims_slider.valueChanged.connect(_callback)
    dict_view.set_editable(False)
    child = win.add_child(dict_view, title="Measure (Live)")
    child.closed.connect(lambda: win.widget.current_roi_updated.disconnect(_callback))
    _callback()


def _measure(
    model: WidgetDataModel,
    meta: model_meta.ImageMeta,
    roi: roi.RoiModel,
) -> dict[str, float]:
    arr = wrap_array(model.value)
    current_indices = meta.current_indices
    if current_indices is None:
        raise ValueError("`current_indices` is not set.")
    current_slice = tuple(slice(None) if i is None else i for i in current_indices)
    arr_slice = arr.get_slice(current_slice)
    if arr_slice.dtype == np.float16:
        # scipy ndimage does not support float16
        arr_slice = arr_slice.astype(np.float32)
    target = slice_array(roi, arr_slice)
    metrics = METRICS_SHARED | METRICS_ADDITIONAL.get(type(roi), {})
    output: dict[str, float] = {}
    for metric_name, func in metrics.items():
        result = func(roi, target)
        if isinstance(result, np.integer):
            output[metric_name] = int(result)
        elif isinstance(result, np.floating):
            output[metric_name] = float(result)
        else:
            output[metric_name] = result
    return output


@register_function(
    title="Measure ROIs ...",
    types=StandardType.IMAGE,
    menus=MENUS,
    run_async=True,
    command_id="himena-image:roi-measure",
)
def roi_measure(model: WidgetDataModel) -> Parametric:
    """Measure features for each ROI."""
    metrics_choices = list(METRICS_SHARED.keys())
    arr = wrap_array(model.value)
    if not isinstance(meta := model.metadata, model_meta.ImageMeta):
        raise ValueError("Image must have an ImageMeta.")
    if axes := meta.axes:
        axis_names = [axis.name for axis in axes[:-2]]
    else:
        axis_names = [f"axis_{i}" for i in range(arr.ndim - 2)]
    axes_choices = [(axis_name, i) for i, axis_name in enumerate(axis_names)]

    @configure_gui(
        metrics={"choices": metrics_choices, "widget_type": "Select"},
        along={"choices": axes_choices, "widget_type": "Select"},
        pivot={"value": len(axes_choices) > 0},  # only enable for nD images
        additional={"text": "Also measure additional common metrics"},
    )
    def run_measure(
        metrics: list[str],
        along: list[int],
        pivot: bool,
        additional: bool = True,
    ) -> WidgetDataModel:
        rois = meta.unwrap_rois()
        if len(rois) == 0:
            raise ValueError("No ROIs to measure.")

        ndindex_shape = tuple(arr.shape[i] for i in along)
        funcs = [METRICS_SHARED[metric] for metric in metrics]

        if additional:
            # if all the rois are the same type with additional metrics, add them to funcs
            _more = reduce(
                _dict_intersection,
                [METRICS_ADDITIONAL.get(type(each_roi), {}) for each_roi in rois],
            )
            if _more:
                _more_metrics = list(_more.keys())
                metrics = metrics + _more_metrics
                funcs = funcs + [_more[metric] for metric in _more_metrics]

        # check name collision between axis names and metrics names
        for metric in metrics:
            if metric in axis_names:
                warnings.warn(
                    f"Name collision between axis names and metrics: {metric!r}",
                    UserWarning,
                    stacklevel=2,
                )
        out: dict[str, list] = {}
        for along_i in along:
            axis_name = axis_names[along_i]
            out[axis_name] = []
        if pivot:
            # initialize result dict
            for metric in metrics:
                for each_roi in rois:
                    out[f"{metric}_{each_roi.name}"] = []
            for sl in np.ndindex(ndindex_shape):
                for sl_i, axis_name in zip(sl, axis_names):
                    out[axis_name].append(sl_i)
                for indices, each_roi in rois.iter_with_indices():
                    target = _prep_sliced_array(arr, each_roi, sl, along, indices)
                    for func, metric in zip(funcs, metrics):
                        out[f"{metric}_{each_roi.name}"].append(func(each_roi, target))
        else:
            out["name"] = []
            for metric in metrics:
                out[metric] = []
            for sl in np.ndindex(ndindex_shape):
                for indices, each_roi in rois.iter_with_indices():
                    target = _prep_sliced_array(arr, each_roi, sl, along, indices)
                    out["name"].append(each_roi.name)
                    for sl_i, axis_name in zip(sl, axis_names):
                        out[axis_name].append(sl_i)
                    for func, metric in zip(funcs, metrics):
                        out[metric].append(func(each_roi, target))
        return WidgetDataModel(
            value=out,
            type=StandardType.DATAFRAME,
            title=f"Results of {model.title}",
        )

    return run_measure


def _prep_sliced_array(
    arr: ArrayWrapper,
    each_roi: roi.RoiModel,
    sl: tuple[int, ...],
    along: list[int],
    indices: list[int],
):
    sl_placeholder = list(indices)
    for i, along_i in enumerate(along):
        sl_placeholder[along_i] = sl[i]
    arr_slice = arr.get_slice(tuple(sl_placeholder))
    return slice_array(each_roi, arr_slice)


@singledispatch
def slice_array(r: roi.RoiModel, arr_nd: np.ndarray):
    """Transfrom array from (N, ..., Y, X) to (N, ..., S)

    S is the number of pixels in the ROI."""
    mask = r.to_mask(arr_nd.shape)
    return arr_nd[..., mask]


@slice_array.register
def _(r: roi.RectangleRoi, arr_nd: np.ndarray):
    bb = r.bbox().adjust_to_int("inner")
    arr = arr_nd[..., bb.top : bb.bottom, bb.left : bb.right]
    return arr.reshape(*arr.shape[:-2], arr.shape[-2] * arr.shape[-1])


@slice_array.register
def _(r: roi.EllipseRoi, arr_nd: np.ndarray):
    _yy, _xx = np.indices(arr_nd.shape[-2:])
    mask = (_yy - r.y) ** 2 / r.height**2 + (_xx - r.x) ** 2 / r.width**2 <= 1
    return arr_nd[..., mask]


@slice_array.register
def _(r: roi.PointRoi2D, arr_nd: np.ndarray):
    out = ndi.map_coordinates(arr_nd, [[r.y], [r.x]], order=1, mode="nearest")
    return out


@slice_array.register
def _(r: roi.PointsRoi2D, arr_nd: np.ndarray):
    coords = np.stack([r.ys, r.xs], axis=0)
    out = ndi.map_coordinates(arr_nd, coords, order=1, mode="nearest")
    return out


@slice_array.register
def _(r: roi.LineRoi, arr_nd: np.ndarray):
    xs, ys = r.arange()
    return _slice_array_along_line(arr_nd, xs, ys)


@slice_array.register
def _(r: roi.SegmentedLineRoi, arr_nd: np.ndarray):
    xs, ys = r.arange()
    return _slice_array_along_line(arr_nd, xs, ys)


def _slice_array_along_line(arr_nd: NDArray[np.number], xs, ys):
    coords = np.stack([ys, xs], axis=0)
    out = np.empty(arr_nd.shape[:-2] + (coords.shape[1],), dtype=np.float32)
    for sl in np.ndindex(arr_nd.shape[:-2]):
        arr_2d = arr_nd[sl]
        out[sl] = ndi.map_coordinates(arr_2d, coords, order=1, mode="nearest")
    return out


def _dict_intersection(
    dict1: dict[str, _MetricsType[roi.RoiModel]],
    dict2: dict[str, _MetricsType[roi.RoiModel]],
) -> dict[str, _MetricsType[roi.RoiModel]]:
    return {k: v for k, v in dict1.items() if k in dict2}


_Roi = TypeVar("_Roi", bound=roi.RoiModel)
# _MetricsType takes a Roi and 1D array slice and returns a float
_MetricsType = Callable[[_Roi, NDArray[np.number], NDArray[np.number]], float]
# Supported additional metrics for each ROI type
METRICS_SHARED: dict[str, _MetricsType[roi.RoiModel]] = {
    "mean": lambda roi, ar_sl: np.mean(ar_sl) if ar_sl.size > 0 else np.nan,
    "std": lambda roi, ar_sl: np.std(ar_sl) if ar_sl.size > 0 else np.nan,
    "min": lambda roi, ar_sl: np.min(ar_sl) if ar_sl.size > 0 else np.nan,
    "max": lambda roi, ar_sl: np.max(ar_sl) if ar_sl.size > 0 else np.nan,
    "sum": lambda roi, ar_sl: np.sum(ar_sl) if ar_sl.size > 0 else np.nan,
    "median": lambda roi, ar_sl: np.median(ar_sl) if ar_sl.size > 0 else np.nan,
    "area": lambda roi, ar_sl: ar_sl.size,
}
_METRICS_LINE: dict[str, _MetricsType[roi.LineRoi]] = {
    "length": lambda roi, ar_sl: roi.length(),
    "angle": lambda roi, ar_sl: roi.angle() if roi.length() > 0 else np.nan,
}
_METRICS_SEGMENTED_LINE: dict[str, _MetricsType[roi.SegmentedLineRoi]] = {
    "length": lambda roi, ar_sl: roi.length(),
}
_METRICS_RECTANGLE: dict[str, _MetricsType[roi.RectangleRoi]] = {
    "area": lambda roi, ar_sl: roi.area(),
    "width": lambda roi, ar_sl: roi.width,
    "height": lambda roi, ar_sl: roi.height,
}
_METRICS_ELLIPSE: dict[str, _MetricsType[roi.EllipseRoi]] = {
    "area": lambda roi, ar_sl: roi.area(),
    "width": lambda roi, ar_sl: roi.width,
    "height": lambda roi, ar_sl: roi.height,
    "eccentricity": lambda roi, ar_sl: roi.eccentricity() if roi.area() > 0 else np.nan,
}
_METRICS_ROTATED_RECTANGLE: dict[str, _MetricsType[roi.RotatedRectangleRoi]] = {
    "area": lambda roi, ar_sl: roi.area(),
    "width": lambda roi, ar_sl: roi.width,
    "lenght": lambda roi, ar_sl: roi.length(),
    "angle": lambda roi, ar_sl: roi.angle() if roi.length() > 0 else np.nan,
}
_METRICS_ROTATED_ELLIPSE: dict[str, _MetricsType[roi.RotatedEllipseRoi]] = {
    "area": lambda roi, ar_sl: roi.area(),
    "width": lambda roi, ar_sl: roi.width,
    "lenght": lambda roi, ar_sl: roi.length(),
    "angle": lambda roi, ar_sl: roi.angle() if roi.length() > 0 else np.nan,
}
_METRICS_CIRCLE: dict[str, _MetricsType[roi.CircleRoi]] = {
    "radius": lambda roi, ar_sl: roi.radius,
}
_METRICS_POINT: dict[str, _MetricsType[roi.PointRoi2D]] = {
    "x": lambda roi, ar_sl: roi.x,
    "y": lambda roi, ar_sl: roi.y,
}

METRICS_ADDITIONAL: dict[type[roi.RoiModel], dict[str, _MetricsType[roi.Roi2D]]] = {
    roi.PointRoi2D: _METRICS_POINT,
    roi.LineRoi: _METRICS_LINE,
    roi.SegmentedLineRoi: _METRICS_SEGMENTED_LINE,
    roi.RectangleRoi: _METRICS_RECTANGLE,
    roi.EllipseRoi: _METRICS_ELLIPSE,
    roi.RotatedRectangleRoi: _METRICS_ROTATED_RECTANGLE,
    roi.RotatedEllipseRoi: _METRICS_ROTATED_ELLIPSE,
    roi.CircleRoi: _METRICS_CIRCLE,
}
