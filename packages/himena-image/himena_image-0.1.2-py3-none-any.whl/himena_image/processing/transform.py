from typing import Annotated, Literal

from himena import WidgetDataModel, Parametric
from himena.consts import StandardType
from himena.plugins import register_function, configure_gui
from himena.standards.model_meta import ImageMeta
from himena.standards.roi import PointRoi2D
import numpy as np
from himena_image.consts import PaddingMode, InterpolationOrder
from himena_image.utils import (
    make_dims_annotation,
    image_to_model,
    model_to_image,
    norm_dims,
)
from himena_image._mgui_widgets import PointEdit

MENUS = ["tools/image/process/transform", "/model_menu/process/transform"]


@register_function(
    title="Shift ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:shift",
    run_async=True,
)
def shift(model: WidgetDataModel) -> Parametric:
    shape = model.value.shape
    if len(shape) < 2:
        raise ValueError("The image must have at least 2 dimensions.")
    max_size = max(shape)

    @configure_gui(
        preview=True,
        shift={
            "options": {
                "widget_type": "FloatSpinBox",
                "min": -max_size,
                "max": max_size,
            }
        },
    )
    def run_shift(
        shift: tuple[float, float],
        mode: PaddingMode = "constant",
        cval: float = 0.0,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.shift(shift, mode=mode, cval=cval, dims=norm_dims(2, img.axes))
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_shift


@register_function(
    title="Rotate ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:rotate",
    run_async=True,
)
def rotate(model: WidgetDataModel) -> Parametric:
    @configure_gui(preview=True)
    def run_rotate(
        degree: Annotated[float, {"min": -90, "max": 90, "widget_type": "FloatSlider"}],
        order: InterpolationOrder = 3,
        mode: PaddingMode = "constant",
        cval: float = 0.0,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        if abs(degree) < 1e-4:
            return model
        img = model_to_image(model, is_previewing)
        out = img.rotate(degree, mode=mode, cval=cval, order=order)
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_rotate


@register_function(
    title="Flip ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:flip",
    run_async=True,
)
def flip(model: WidgetDataModel) -> Parametric:
    @configure_gui(preview=True)
    def run_flip(
        axis: str,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        idx = img.axes.index(axis)
        slices = [slice(None)] * img.ndim
        slices[idx] = slice(None, None, -1)
        out = img[tuple(slices)]
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_flip


@register_function(
    title="Zoom ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:zoom",
    run_async=True,
)
def zoom(model: WidgetDataModel) -> Parametric:
    @configure_gui(preview=True, dimension={"choices": make_dims_annotation(model)})
    def run_zoom(
        factor: float,
        order: InterpolationOrder = 3,
        mode: PaddingMode = "constant",
        cval: float = 0.0,
        same_shape: bool = False,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.zoom(
            factor,
            order=order,
            mode=mode,
            cval=cval,
            same_shape=same_shape,
            dims=norm_dims(dimension, img.axes),
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_zoom


@register_function(
    title="Bin ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:bin",
    run_async=True,
)
def bin(model: WidgetDataModel) -> Parametric:
    @configure_gui(preview=True, dimension={"choices": make_dims_annotation(model)})
    def run_bin(
        bin_size: Literal[2, 3, 4, 5, 6, 7, 8],
        method: str = "mean",
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.binning(
            bin_size,
            method=method,
            check_edges=False,
            dims=norm_dims(dimension, img.axes),
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_bin


@register_function(
    title="Radial profile ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:radial-profile",
    run_async=True,
)
def radial_profile(model: WidgetDataModel) -> Parametric:
    def _point_getter(widget):
        if not isinstance(meta := model.metadata, ImageMeta):
            return None
        if not isinstance(roi := meta.current_roi, PointRoi2D):
            return None
        return roi.x, roi.y

    @configure_gui(
        center={"widget_type": PointEdit, "getter": _point_getter},
        dimension={"choices": make_dims_annotation(model)},
    )
    def run_radial_profile(
        center: tuple[float, float] | None = None,
        method: Literal["mean", "min", "std", "max"] = "mean",
        dimension: int = 2,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.radial_profile(
            center=center, method=method, dims=norm_dims(dimension, img.axes)
        )
        return image_to_model(out, orig=model)

    return run_radial_profile


@register_function(
    title="Unmix multi-channel image ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:unmix",
    group="transform-color",
)
def unmix(model: WidgetDataModel):
    """Run unmixing of fluorescence leakage between channels."""

    @configure_gui(
        matrix={"types": [StandardType.ARRAY, StandardType.TABLE]},
        dimension={"choices": make_dims_annotation(model)},
    )
    def run_unmix(
        matrix: WidgetDataModel,
        background: list[float] | None = None,
    ) -> WidgetDataModel:
        if matrix.type == StandardType.ARRAY:
            matrix = matrix.value
        else:
            matrix = np.asarray(matrix.value).astype(np.float64)
        img = model_to_image(model)
        out = img.unmix(matrix, bg=background)
        return image_to_model(out, orig=model)

    return run_unmix
