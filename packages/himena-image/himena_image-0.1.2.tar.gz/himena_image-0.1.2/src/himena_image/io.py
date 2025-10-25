from functools import partial
from pathlib import Path
import struct
from typing import Any, Sequence
import zipfile
import impy as ip
from impy.arrays.bases import MetaArray
import numpy as np
from roifile import ROI_OPTIONS, ROI_SUBTYPE, ImagejRoi, roiread, roiwrite, ROI_TYPE

from himena import MainWindow, Parametric, StandardType, WidgetDataModel
from himena.consts import MenuId
from himena.standards.model_meta import ImageMeta, DimAxis
from himena.standards import roi as _roi
from himena.plugins import (
    register_reader_plugin,
    register_writer_plugin,
    register_function,
    configure_gui,
)
from himena_image.utils import image_to_model


_SUPPORTED_EXT = frozenset(
    [".tif", ".tiff", ".lsm", ".mrc", ".rec", ".st", ".map", ".nd2", ".czi"]
)  # fmt: skip
_SUPPORTED_MULTI_EXT = frozenset([".mrc.gz", ".map.gz"])


def _is_image_file(path: Path) -> bool:
    return (
        path.suffix in _SUPPORTED_EXT or "".join(path.suffixes) in _SUPPORTED_MULTI_EXT
    )


def on_himena_startup(ui: MainWindow):
    @ui.object_type_map.register
    def ip_image_array(value: Any):
        if isinstance(value, (MetaArray, ip.LazyImgArray)):
            axes = []
            for axis in value.axes:
                dimaxis = DimAxis(name=str(axis), scale=axis.scale, unit=axis.unit)
                axes.append(dimaxis)
            channel_axis_index = None
            if "c" in value.axes:
                channel_axis_index = value.axes.index("c")
            if isinstance(value, ip.Label):
                typ = StandardType.IMAGE_LABELS
            else:
                typ = StandardType.IMAGE
            return (
                typ,
                value.value,
                ImageMeta(axes=axes, channel_axis=channel_axis_index),
            )


@register_reader_plugin
def read_image(path: Path):
    """Read as a image model."""
    img = ip.imread(path)
    if path.suffix in [".png", ".jpg", ".jpeg"]:
        is_rgb = "c" in img.axes
    elif path.suffix in [".tif", ".tiff"]:
        is_rgb = "s" in img.axes
    else:
        is_rgb = False
    model = image_to_model(img, is_rgb=is_rgb)
    if path.suffix == ".nd2":
        model.extension_default = ".tif"  # ND2 writer not supported yet
    else:
        model.extension_default = path.suffix
    return model


@read_image.define_matcher
def _(path: Path):
    if _is_image_file(path):
        return StandardType.IMAGE
    return None


@register_writer_plugin
def write_image(model: WidgetDataModel, path: Path):
    """Write image model to a file."""
    img = model.value
    _axes = None
    _scales = {}
    _units = {}
    if isinstance(meta := model.metadata, ImageMeta):
        if axes := meta.axes:
            _axes = [a.name for a in axes]
            _scales = {a.name: a.scale for a in axes}
            _units = {a.name: a.unit for a in axes}
    img = ip.asarray(img, axes=_axes)

    for a in img.axes:
        a.scale = _scales.get(str(a))
        a.unit = _units.get(str(a))
    return img.imsave(path)


@write_image.define_matcher
def _(model: WidgetDataModel, path: Path):
    return model.is_subtype_of(StandardType.ARRAY) and _is_image_file(path)


@register_reader_plugin(priority=-10)
def read_image_as_labels(path: Path):
    """Read as a image model."""
    img = ip.imread(path)
    model = image_to_model(img, is_rgb=False)
    model.extension_default = path.suffix
    model.type = StandardType.IMAGE_LABELS
    return model


@read_image_as_labels.define_matcher
def _(path: Path):
    if _is_image_file(path):
        return StandardType.IMAGE_LABELS
    return None


@register_reader_plugin
def read_roi(path: Path):
    out = roiread(path)
    if isinstance(out, ImagejRoi):
        ijrois = [out]
    else:
        ijrois = out
    indices: list[Sequence[int]] = []
    rois = []
    for ijroi in ijrois:
        ind, sroi = _to_standard_roi(ijroi)
        indices.append(ind)
        rois.append(sroi)
    axis_names = ["p", "t", "z", "c"]
    indices = np.array(indices, dtype=np.int32)
    val = _roi.RoiListModel(rois, indices=indices, axis_names=axis_names).simplified()
    return WidgetDataModel(value=val, type=StandardType.ROIS, title=path.name)


@read_roi.define_matcher
def _(path: Path):
    ext = "".join(path.suffixes)
    if ext == ".roi":
        return StandardType.ROIS
    elif ext == ".zip":
        with zipfile.ZipFile(path) as z:
            if names := z.namelist():
                if names[0].endswith(".roi"):
                    return StandardType.ROIS
    return None


@register_writer_plugin
def write_roi(model: WidgetDataModel, path: Path):
    if not isinstance(rlist := model.value, _roi.RoiListModel):
        raise ValueError(f"Must be a RoiListModel, got {type(rlist)}")
    _ij_position_getter = partial(
        _to_ij_position, rlist.indices, axis_names=rlist.axis_names
    )
    p_s = _ij_position_getter(["p", "position"])
    t_s = _ij_position_getter(["t", "time"])
    z_s = _ij_position_getter(["z", "slice"])
    c_s = _ij_position_getter(["c", "channel"])
    ijrois: list[ImagejRoi] = []
    for p, t, z, c, roi in zip(p_s, t_s, z_s, c_s, rlist.items):
        multi_dims = {
            "position": p,
            "t_position": t,
            "z_position": z,
            "c_position": c,
        }
        ijrois.append(_from_standard_roi(roi, multi_dims))
    if path.exists():
        path.unlink()
    roiwrite(path, ijrois)
    return None


@write_roi.define_matcher
def _(model: WidgetDataModel, path: Path):
    return model.is_subtype_of(StandardType.ROIS) and path.suffix == ".zip"


@register_function(
    menus=MenuId.FILE,
    title="Open image in lazy mode ...",
    command_id="himena-image:io:lazy-imread",
)
def lazy_imread() -> Parametric:
    @configure_gui
    def run_lazy_imread(path: Path, chunks: list[int]) -> WidgetDataModel:
        img = ip.lazy.imread(path, chunks=chunks)
        model = image_to_model(img)
        model.extension_default = path.suffix
        return model

    return run_lazy_imread


def _get_coords(ijroi: ImagejRoi) -> np.ndarray:
    if ijroi.subpixelresolution:
        return ijroi.subpixel_coordinates - 1
    return ijroi.integer_coordinates - 1 + [ijroi.left, ijroi.top]


def _to_standard_roi(ijroi: ImagejRoi) -> tuple[tuple[int, ...], _roi.RoiModel]:
    p = ijroi.position
    c = ijroi.c_position
    t = ijroi.t_position
    z = ijroi.z_position
    name = ijroi.name

    if ijroi.subtype == ROI_SUBTYPE.UNDEFINED:
        if ijroi.roitype == ROI_TYPE.RECT:
            if ijroi.options == ROI_OPTIONS.SUB_PIXEL_RESOLUTION:
                out = _roi.RectangleRoi(
                    x=ijroi.xd,
                    y=ijroi.yd,
                    width=ijroi.widthd,
                    height=ijroi.heightd,
                    name=name,
                )
            else:
                out = _roi.RectangleRoi(
                    x=ijroi.left,
                    y=ijroi.top,
                    width=ijroi.right - ijroi.left,
                    height=ijroi.bottom - ijroi.top,
                    name=name,
                )
        elif ijroi.roitype == ROI_TYPE.LINE:
            out = _roi.LineRoi(
                start=(ijroi.x1 - 1, ijroi.y1 - 1),
                end=(ijroi.x2 - 1, ijroi.y2 - 1),
                name=name,
            )
        elif ijroi.roitype == ROI_TYPE.POINT:
            coords = _get_coords(ijroi)
            if coords.shape[0] == 1:
                out = _roi.PointRoi2D(x=coords[0, 0], y=coords[0, 1], name=name)
            else:
                out = _roi.PointsRoi2D(xs=coords[:, 0], ys=coords[:, 1], name=name)
        elif ijroi.roitype in (ROI_TYPE.POLYGON, ROI_TYPE.FREEHAND):
            coords = _get_coords(ijroi)
            out = _roi.PolygonRoi(xs=coords[:, 0], ys=coords[:, 1], name=name)
        elif ijroi.roitype in (ROI_TYPE.POLYLINE, ROI_TYPE.FREELINE):
            coords = _get_coords(ijroi)
            out = _roi.SegmentedLineRoi(xs=coords[:, 0], ys=coords[:, 1], name=name)
        elif ijroi.roitype == ROI_TYPE.OVAL:
            if ijroi.options == ROI_OPTIONS.SUB_PIXEL_RESOLUTION:
                out = _roi.EllipseRoi(
                    x=ijroi.xd,
                    y=ijroi.yd,
                    width=ijroi.widthd,
                    height=ijroi.heightd,
                    name=name,
                )
            else:
                out = _roi.EllipseRoi(
                    x=ijroi.left,
                    y=ijroi.top,
                    width=ijroi.right - ijroi.left,
                    height=ijroi.bottom - ijroi.top,
                    name=name,
                )
        else:
            raise ValueError(f"Unsupported ROI type: {ijroi.roitype!r}")
    elif ijroi.subtype == ROI_SUBTYPE.ROTATED_RECT:
        width = _decode_rotated_roi_width(
            (
                ijroi.arrow_style_or_aspect_ratio,
                ijroi.arrow_head_size,
                ijroi.rounded_rect_arc_size,
            ),
            byteorder=ijroi.byteorder,
        )
        out = _roi.RotatedRectangleRoi(
            start=(ijroi.x1 - 1, ijroi.y1 - 1),
            end=(ijroi.x2 - 1, ijroi.y2 - 1),
            width=width,
            name=name,
        )
    elif ijroi.subtype == ROI_SUBTYPE.ELLIPSE:
        ellipse_ratio = _decode_rotated_roi_width(
            (
                ijroi.arrow_style_or_aspect_ratio,
                ijroi.arrow_head_size,
                ijroi.rounded_rect_arc_size,
            ),
            byteorder=ijroi.byteorder,
        )
        length = np.sqrt((ijroi.x1 - ijroi.x2) ** 2 + (ijroi.y1 - ijroi.y2) ** 2)
        out = _roi.RotatedEllipseRoi(
            start=(ijroi.x1 - 1, ijroi.y1 - 1),
            end=(ijroi.x2 - 1, ijroi.y2 - 1),
            width=length * ellipse_ratio,
            name=name,
        )
    else:
        raise ValueError(f"Unsupported ROI subtype: {ijroi.subtype}")
    return (p, t, z, c), out


def _from_standard_roi(
    roi: _roi.RoiModel,
    multi_dims: dict[str, int],
) -> ImagejRoi:
    if isinstance(roi, _roi.RectangleRoi):
        y1, y2 = roi.y, roi.y + roi.height
        x1, x2 = roi.x, roi.x + roi.width
        return ImagejRoi(
            roitype=ROI_TYPE.RECT,
            name=roi.name,
            x1=x1,
            x2=x2,
            xd=x1,
            widthd=roi.width,
            y1=y1,
            y2=y2,
            yd=y1,
            heightd=roi.height,
            **_to_ij_kwargs(np.array([[x1, y1], [x1, y2], [x2, y2], [x2, y1]])),
            **multi_dims,
        )
    elif isinstance(roi, _roi.EllipseRoi):
        y1, y2 = roi.y, roi.y + roi.height
        x1, x2 = roi.x, roi.x + roi.width
        return ImagejRoi(
            roitype=ROI_TYPE.OVAL,
            name=roi.name,
            x1=x1,
            x2=x2,
            xd=x1,
            widthd=roi.width,
            y1=y1,
            y2=y2,
            yd=y1,
            heightd=roi.height,
            **_to_ij_kwargs(np.array([[x1, y1], [x1, y2], [x2, y2], [x2, y1]])),
            **multi_dims,
        )
    elif isinstance(roi, _roi.LineRoi):
        x1, y1 = np.ones(2) + roi.start
        x2, y2 = np.ones(2) + roi.end
        return ImagejRoi(
            roitype=ROI_TYPE.LINE,
            name=roi.name,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            **_to_ij_kwargs(np.array([[x1, y1], [x2, y2]])),
            **multi_dims,
        )
    elif isinstance(roi, _roi.PointRoi2D):
        return ImagejRoi(
            roitype=ROI_TYPE.POINT,
            name=roi.name,
            **_to_ij_kwargs(np.array([[roi.x + 1, roi.y + 1]])),
            **multi_dims,
        )
    elif isinstance(roi, _roi.PolygonRoi):
        return ImagejRoi(
            roitype=ROI_TYPE.POLYGON,
            name=roi.name,
            **_to_ij_kwargs(np.stack([roi.xs + 1, roi.ys + 1], axis=1)),
            **multi_dims,
        )
    elif isinstance(roi, _roi.SegmentedLineRoi):
        return ImagejRoi(
            roitype=ROI_TYPE.POLYLINE,
            name=roi.name,
            **_to_ij_kwargs(np.stack([roi.xs + 1, roi.ys + 1], axis=1)),
            **multi_dims,
        )
    elif isinstance(roi, _roi.RotatedRectangleRoi):
        enc = _encode_rotated_roi_width(roi.width)
        x1, y1 = np.ones(2) + roi.start
        x2, y2 = np.ones(2) + roi.end
        return ImagejRoi(
            roitype=ROI_TYPE.FREEHAND,
            subtype=ROI_SUBTYPE.ROTATED_RECT,
            name=roi.name,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            arrow_style_or_aspect_ratio=enc[0],
            arrow_head_size=enc[1],
            rounded_rect_arc_size=enc[2],
            **_to_ij_kwargs(np.array([[x1, y1], [x2, y2]])),
            **multi_dims,
        )
    elif isinstance(roi, _roi.RotatedEllipseRoi):
        enc = _encode_rotated_roi_width(roi.width / roi.length())
        a = roi.length() / 2
        b = roi.width / 2
        phi = roi.angle_radian()
        ts = np.linspace(0, 2 * np.pi, 72, endpoint=False)
        start = np.array(roi.start) + 1
        end = np.array(roi.end) + 1
        center = (start + end) / 2
        xs = a * np.cos(ts) * np.cos(phi) - b * np.sin(ts) * np.sin(phi) + center[0]
        ys = a * np.cos(ts) * np.sin(phi) + b * np.sin(ts) * np.cos(phi) + center[1]
        return ImagejRoi(
            roitype=ROI_TYPE.FREEHAND,
            subtype=ROI_SUBTYPE.ELLIPSE,
            name=roi.name,
            x1=start[0],
            y1=start[1],
            x2=end[0],
            y2=end[1],
            arrow_style_or_aspect_ratio=enc[0],
            arrow_head_size=enc[1],
            rounded_rect_arc_size=enc[2],
            **_to_ij_kwargs(np.stack([xs, ys], axis=1)),
            **multi_dims,
        )
    elif isinstance(roi, _roi.PointsRoi2D):
        return ImagejRoi(
            roitype=ROI_TYPE.POINT,
            name=roi.name,
            **_to_ij_kwargs(np.stack([roi.xs + 1, roi.ys + 1], axis=1)),
            **multi_dims,
        )

    raise ValueError(f"Unsupported ROI type: {type(roi)}")


def _to_ij_position(
    indices: np.ndarray,
    candidates: list[str],
    axis_names: list[str],
) -> np.ndarray:
    for cand in candidates:
        if cand in axis_names:
            return indices[:, axis_names.index(cand)] + 1
    return np.full(indices.shape[0], 0, dtype=np.int32)


def _encode_rotated_roi_width(
    width: float, byteorder: str = ">"
) -> tuple[int, int, int]:
    s = struct.pack(byteorder + "f", width)
    return struct.unpack(byteorder + "BBh", s)


def _decode_rotated_roi_width(
    ints: tuple[int, int, int], byteorder: str = ">"
) -> float:
    s = struct.pack(byteorder + "BBh", *ints)
    return struct.unpack(byteorder + "f", s)[0]


def _to_ij_kwargs(coords: np.ndarray) -> dict[str, Any]:
    float_part = np.modf(coords)[0]
    if float_part.max() > 1e-6:
        int_coords = coords.round().astype(np.int32)
        left_top = int_coords.min(axis=0)
        return {
            "integer_coordinates": int_coords - left_top,
            "subpixel_coordinates": np.asarray(coords, dtype=np.float32),
            "n_coordinates": coords.shape[0],
            "options": ROI_OPTIONS.SUB_PIXEL_RESOLUTION,
            "top": int(int_coords[:, 1].min()),
            "left": int(int_coords[:, 0].min()),
            "bottom": int(int_coords[:, 1].max() + 1),
            "right": int(int_coords[:, 0].max() + 1),
        }
    else:
        int_coords = coords.astype(np.int32)
        left_top = int_coords.min(axis=0)
        return {
            "integer_coordinates": int_coords - left_top,
            "n_coordinates": coords.shape[0],
            "top": int(int_coords[:, 1].min()),
            "left": int(int_coords[:, 0].min()),
            "bottom": int(int_coords[:, 1].max() + 1),
            "right": int(int_coords[:, 0].max() + 1),
        }
