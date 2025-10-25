from __future__ import annotations
from typing import Literal, Sequence, overload
from himena import WidgetDataModel, create_model
import impy as ip
from himena.consts import StandardType
from himena.standards.model_meta import ImageMeta, DimAxis


def image_to_model(
    img: ip.ImgArray | ip.LazyImgArray,
    title: str | None = None,
    is_rgb: bool | None = None,
    orig: WidgetDataModel | None = None,
    is_previewing: bool = False,
    reset_clim: bool = False,
    extension_default: str | None = None,
) -> WidgetDataModel:
    """Convert impy image array to WidgetDataModel."""
    # normalize is_rgb
    if is_rgb is None and orig is not None:
        meta = orig.metadata
        if isinstance(meta, ImageMeta):
            is_rgb = meta.is_rgb
    if is_rgb is None:
        is_rgb = False

    # normalize channel info
    if "c" in img.axes and not is_rgb:
        channel_axis = img.axes.index("c")
    else:
        channel_axis = None
    meta = ImageMeta(
        axes=[
            DimAxis(
                name=str(a),
                scale=a.scale,
                unit=a.unit,
                default_label_format="Ch-{:s}" if str(a) == "c" else "{:s}",
            )
            for a in img.axes
        ],
        channel_axis=channel_axis,
        is_rgb=is_rgb,
    )
    if orig:
        if isinstance(orig_meta := orig.metadata, ImageMeta):
            if channel_axis and len(meta.channels) == len(orig_meta.channels):
                meta.channels = orig_meta.channels
            if reset_clim:
                for ch in meta.channels:
                    ch.contrast_limits = None
        out = orig.with_value(img.value, title=title, metadata=meta)
        if title is None:
            out = out.with_title_numbering()
    else:
        out = create_model(
            img.value,
            type=StandardType.IMAGE,
            title=title,
            metadata=meta,
        )
    if is_previewing:
        meta.current_indices = None
        meta.contrast_limits = None
    if extension_default:
        out.extension_default = extension_default
    return out


def label_to_model(
    img: ip.ImgArray | ip.LazyImgArray,
    title: str | None = None,
    is_rgb: bool = False,
    orig: WidgetDataModel | None = None,
    is_previewing: bool = False,
) -> WidgetDataModel:
    out = image_to_model(img, title, is_rgb, orig, is_previewing)
    out.type = StandardType.IMAGE_LABELS
    out.metadata.channels = []
    return out


def make_dims_annotation(model: WidgetDataModel) -> list[tuple[str, int]]:
    if not isinstance(meta := model.metadata, ImageMeta):
        return [("2 (yx)", 2)]
    elif (axes := meta.axes) is None:
        return [("2 (yx)", 2)]
    axis_names = [a.name for a in axes]
    if "z" in axis_names and "y" in axis_names and "x" in axis_names:
        choices = [("2 (yx)", 2), ("3 (zyx)", 3)]
    elif "y" in axis_names and "x" in axis_names:
        choices = [("2 (yx)", 2)]
    elif len(axis_names) > 1:
        if len(axis_names[-1]) == len(axis_names[-2]) == 1:
            label = "".join(axis_names[-2:])
        else:
            label = ", ".join(axis_names[-2:])
        choices = [(f"2 ({label})", 2)]
    else:
        choices = [("2 (yx)", 2)]
    return choices


def norm_dims(dims: int, axes) -> Sequence[str]:
    if dims == 2:
        if "x" in axes and "y" in axes:
            return "yx"
        else:
            return [str(axes[-2]), str(axes[-1])]
    elif dims == 3:
        if "x" in axes and "y" in axes and "z" in axes:
            return "zyx"
        else:
            return [str(axes[-3]), str(axes[-2]), str(axes[-1])]


@overload
def model_to_image(
    model: WidgetDataModel,
    is_previewing: Literal[False] = False,
) -> ip.ImgArray: ...


@overload
def model_to_image(
    model: WidgetDataModel,
    is_previewing: bool = False,
) -> ip.ImgArray | ip.LazyImgArray: ...


def model_to_image(
    model: WidgetDataModel,
    is_previewing: bool = False,
):
    import dask.array as da

    img = model.value
    if not isinstance(meta := model.metadata, ImageMeta):
        raise ValueError("Model must have ImageMeta.")
    if meta.axes is not None:
        scale = {}
        unit = {}
        axes = {}
        for a in meta.axes:
            scale[a.name] = a.scale
            unit[a.name] = a.unit
        axes = list(scale.keys())
    else:
        axes = None
        scale = None
        unit = None
    if isinstance(img, da.Array):
        out = ip.lazy.asarray(img, axes=axes, chunks=img.chunksize)
    elif is_previewing:
        n_multi = img.ndim - 3 if meta.is_rgb else img.ndim - 2
        if n_multi == 0:
            out = ip.asarray(img, axes=axes)
        else:
            chunks_rest = (-1, -1, -1) if meta.is_rgb else (-1, -1)
            out = ip.lazy.asarray(img, axes=axes, chunks=(1,) * n_multi + chunks_rest)
    else:
        out = ip.asarray(img, axes=axes)
    if scale is not None and unit is not None:
        for a in out.axes:
            a.scale = scale.get(str(a))
            a.unit = unit.get(str(a))
    return out
