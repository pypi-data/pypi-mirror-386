from typing import Annotated, Literal
import impy as ip

from himena import WidgetDataModel, Parametric
from himena.consts import StandardType
from himena.plugins import register_function, configure_gui
from himena.standards.model_meta import ImageMeta
from himena_image.consts import PaddingMode
from himena_image.utils import (
    make_dims_annotation,
    model_to_image,
    image_to_model,
    norm_dims,
)

MENUS = ["tools/image/process/filter", "/model_menu/process/filter"]


@register_function(
    title="Gaussian Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:gaussian-filter",
    group="00-filter-basic",
    run_async=True,
)
def gaussian_filter(model: WidgetDataModel) -> Parametric:
    """Apply a Gaussian filter to the image."""

    @configure_gui(
        dimension={"choices": make_dims_annotation(model)},
        preview=True,
    )
    def run_gaussian_filter(
        sigma: Annotated[float, {"min": 0.0}] = 1.0,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.gaussian_filter(sigma=sigma, dims=norm_dims(dimension, img.axes))
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_gaussian_filter


@register_function(
    title="Median Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:median-filter",
    group="00-filter-basic",
    run_async=True,
)
def median_filter(model: WidgetDataModel) -> Parametric:
    """Apply a median filter to the image."""

    @configure_gui(
        dimension={"choices": make_dims_annotation(model)},
        preview=True,
    )
    def run_median_filter(
        radius: Annotated[float, {"min": 0.0}] = 1.0,
        mode: PaddingMode = "reflect",
        cval: float = 0,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.median_filter(
            radius, mode=mode, cval=cval, dims=norm_dims(dimension, img.axes)
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_median_filter


@register_function(
    title="Mean Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:mean-filter",
    group="00-filter-basic",
    run_async=True,
)
def mean_filter(model: WidgetDataModel) -> Parametric:
    """Apply a mean filter to the image."""

    @configure_gui(dimension={"choices": make_dims_annotation(model)}, preview=True)
    def run_mean_filter(
        radius: Annotated[float, {"min": 0.0}] = 1.0,
        mode: PaddingMode = "reflect",
        cval: float = 0,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.mean_filter(
            radius, mode=mode, cval=cval, dims=norm_dims(dimension, img.axes)
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_mean_filter


@register_function(
    title="Min Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:min-filter",
    group="00-filter-basic",
    run_async=True,
)
def min_filter(model: WidgetDataModel) -> Parametric:
    """Apply a minimum filter to the image."""

    @configure_gui(dimension={"choices": make_dims_annotation(model)}, preview=True)
    def run_min_filter(
        radius: Annotated[float, {"min": 0.0}] = 1.0,
        mode: PaddingMode = "reflect",
        cval: float = 0,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.min_filter(
            radius, mode=mode, cval=cval, dims=norm_dims(dimension, img.axes)
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_min_filter


@register_function(
    title="Max Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:max-filter",
    group="00-filter-basic",
    run_async=True,
)
def max_filter(model: WidgetDataModel) -> Parametric:
    """Apply a maximum filter to the image."""

    @configure_gui(dimension={"choices": make_dims_annotation(model)}, preview=True)
    def run_max_filter(
        radius: Annotated[float, {"min": 0.0}] = 1.0,
        mode: PaddingMode = "reflect",
        cval: float = 0,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.max_filter(
            radius, mode=mode, cval=cval, dims=norm_dims(dimension, img.axes)
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_max_filter


@register_function(
    title="STD Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:std-filter",
    group="01-filter-variance",
    run_async=True,
)
def std_filter(model: WidgetDataModel) -> Parametric:
    """Standard deviation filter."""

    @configure_gui(dimension={"choices": make_dims_annotation(model)}, preview=True)
    def run_std_filter(
        radius: Annotated[float, {"min": 0.0}] = 1.0,
        mode: PaddingMode = "reflect",
        cval: float = 0,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.std_filter(
            radius, mode=mode, cval=cval, dims=norm_dims(dimension, img.axes)
        )
        return image_to_model(
            out, orig=model, is_previewing=is_previewing, reset_clim=True
        )

    return run_std_filter


@register_function(
    title="Coef Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:coef-filter",
    group="01-filter-variance",
    run_async=True,
)
def coef_filter(model: WidgetDataModel) -> Parametric:
    """Coefficient of variation filter."""

    @configure_gui(dimension={"choices": make_dims_annotation(model)}, preview=True)
    def run_coef_filter(
        radius: Annotated[float, {"min": 0.0}] = 1.0,
        mode: PaddingMode = "reflect",
        cval: float = 0,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.coef_filter(
            radius, mode=mode, cval=cval, dims=norm_dims(dimension, img.axes)
        )
        return image_to_model(
            out, orig=model, is_previewing=is_previewing, reset_clim=True
        )

    return run_coef_filter


@register_function(
    title="Difference of Gaussian (DoG) Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:dog-filter",
    group="02-filter-composit",
    run_async=True,
)
def dog_filter(model: WidgetDataModel) -> Parametric:
    @configure_gui(dimension={"choices": make_dims_annotation(model)}, preview=True)
    def run_dog_filter(
        sigma_low: Annotated[float, {"min": 0.0}] = 1.0,
        sigma_high: Annotated[float, {"min": 0.0}] = 1.6,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.dog_filter(sigma_low, sigma_high, dims=norm_dims(dimension, img.axes))
        return image_to_model(
            out, orig=model, is_previewing=is_previewing, reset_clim=True
        )

    return run_dog_filter


@register_function(
    title="Laplacian Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:laplacian-filter",
    group="02-filter-composit",
    run_async=True,
)
def laplacian_filter(model: WidgetDataModel) -> Parametric:
    @configure_gui(dimension={"choices": make_dims_annotation(model)}, preview=True)
    def run_laplacian_filter(
        radius: Annotated[int, {"min": 1}] = 1,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.laplacian_filter(radius=radius, dims=norm_dims(dimension, img.axes))
        return image_to_model(
            out, orig=model, is_previewing=is_previewing, reset_clim=True
        )

    return run_laplacian_filter


@register_function(
    title="Difference of Hessian (DoH) Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:doh-filter",
    group="02-filter-composit",
    run_async=True,
)
def doh_filter(model: WidgetDataModel) -> Parametric:
    @configure_gui(dimension={"choices": make_dims_annotation(model)}, preview=True)
    def run_doh_filter(
        sigma: Annotated[float, {"min": 0.0}] = 1.0,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.doh_filter(sigma, dims=norm_dims(dimension, img.axes))
        return image_to_model(
            out, orig=model, is_previewing=is_previewing, reset_clim=True
        )

    return run_doh_filter


@register_function(
    title="Laplacian of Gaussian (LoG) Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:log-filter",
    group="02-filter-composit",
    run_async=True,
)
def log_filter(model: WidgetDataModel) -> Parametric:
    """Apply a Laplacian of Gaussian filter to the image."""

    @configure_gui(dimension={"choices": make_dims_annotation(model)}, preview=True)
    def run_log_filter(
        sigma: Annotated[float, {"min": 0.0}] = 1.0,
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.log_filter(sigma, dims=norm_dims(dimension, img.axes))
        return image_to_model(
            out, orig=model, is_previewing=is_previewing, reset_clim=True
        )

    return run_log_filter


@register_function(
    title="Rolling ball ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:rolling-ball",
    group="90-filter-others",
    run_async=True,
)
def rolling_ball(model: WidgetDataModel) -> Parametric:
    """Remove or create a background using the rolling-ball algorithm."""

    @configure_gui(dimension={"choices": make_dims_annotation(model)})
    def run_rolling_ball(
        radius: Annotated[float, {"min": 0.0}] = 30.0,
        prefilter: Literal["mean", "median", "none"] = "mean",
        dimension: int = 2,
        return_background: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.rolling_ball(
            radius,
            prefilter=prefilter,
            return_bg=return_background,
            dims=norm_dims(dimension, img.axes),
        )
        return image_to_model(out, orig=model, reset_clim=True)

    return run_rolling_ball


@register_function(
    title="Entropy filter ...",
    menus=MENUS,
    command_id="himena-image:entropy-filter",
    group="90-filter-others",
    run_async=True,
)
def entropy_filter(model: WidgetDataModel) -> Parametric:
    """Run entropy filter on an image."""

    @configure_gui(dimension={"choices": make_dims_annotation(model)})
    def run_entropy(
        radius: Annotated[float, {"min": 0.0}] = 5.0,
        dimension: int = 2,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.entropy_filter(radius, dims=norm_dims(dimension, img.axes))
        return image_to_model(out, orig=model, reset_clim=True)

    return run_entropy


@register_function(
    title="Enhance contrast ...",
    menus=MENUS,
    command_id="himena-image:enhance-contrast",
    group="90-filter-others",
    run_async=True,
)
def enhance_contrast(model: WidgetDataModel) -> Parametric:
    """Run enhance-contrast filter on an image."""

    @configure_gui(dimension={"choices": make_dims_annotation(model)})
    def run_enhance_contrast(
        radius: Annotated[float, {"min": 0.0}] = 1.0,
        dimension: int = 2,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.enhance_contrast(radius, dims=norm_dims(dimension, img.axes))
        return image_to_model(out, orig=model)

    return run_enhance_contrast


@register_function(
    title="Threshold ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:threshold",
    group="90-filter-others",
    run_async=True,
)
def threshold(model: WidgetDataModel) -> Parametric:
    """Binarize the image using a threshold value."""
    from skimage.filters import threshold_yen

    img = ip.asarray(model.value)
    if img.dtype.kind == "f":
        wdgt = "FloatSlider"
    elif img.dtype.kind in "ui":
        wdgt = "Slider"
    else:
        raise ValueError(f"Unsupported dtype: {img.dtype}")
    if isinstance(meta := model.metadata, ImageMeta):
        if inds := meta.current_indices:
            value = threshold_yen(img.value[inds], nbins=128)
        else:
            value = img.value.mean()

    thresh_options = {
        "min": img.min(),
        "max": img.max(),
        "value": value,
        "widget_type": wdgt,
    }

    @configure_gui(threshold=thresh_options, preview=True)
    def run_threshold(
        threshold,
        dark_background: bool = True,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.threshold(threshold)
        if not dark_background:
            out = ~out
        model_out = image_to_model(out, orig=model, is_previewing=is_previewing)
        return model_out

    return run_threshold


@register_function(
    title="Edge Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:edge-filter",
    group="00-filter-basic",
    run_async=True,
)
def edge_filter(model: WidgetDataModel) -> Parametric:
    """Filters for detecting edges in the image."""

    @configure_gui(dimension={"choices": make_dims_annotation(model)}, preview=True)
    def run_edge_filter(
        method: Literal["sobel", "prewitt", "scharr", "farid"],
        dimension: int = 2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.edge_filter(method, dims=norm_dims(dimension, img.axes))
        return image_to_model(
            out, orig=model, is_previewing=is_previewing, reset_clim=True
        )

    return run_edge_filter


@register_function(
    title="Smooth mask ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:smooth-mask",
    group="90-filter-others",
    run_async=True,
)
def smooth_mask(model: WidgetDataModel) -> Parametric:
    @configure_gui(
        title="Smooth mask",
        dimension={"choices": make_dims_annotation(model)},
        preview=True,
    )
    def run_smooth_mask(
        sigma: Annotated[float, {"min": 0.0}] = 1.0,
        dilate_radius: Annotated[float, {"min": 0.0}] = 1.0,
        dark_background: bool = True,
        dimension: int = 2,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.smooth_mask(
            sigma=sigma,
            dilate_radius=dilate_radius,
            mask_light=not dark_background,
            dims=norm_dims(dimension, img.axes),
        )
        return image_to_model(out, orig=model)

    return run_smooth_mask


@register_function(
    title="Kalman Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:kalman-filter",
    group="90-filter-others",
    run_async=True,
)
def kalman_filter(model: WidgetDataModel) -> Parametric:
    """Denoise time-series image using the Kalman filter."""
    img = model_to_image(model)
    along_choices = [str(a) for a in img.axes]
    if "t" in along_choices:
        along_default = "t"
    elif "z" in along_choices:
        along_default = "z"
    else:
        along_default = along_choices[0]

    @configure_gui(
        title="Kalman Filter",
        along={"choices": along_choices, "value": along_default},
        dimension={"choices": make_dims_annotation(model)},
        preview=True,
    )
    def run_kalman_filter(
        gain: Annotated[float, {"min": 0.0}] = 0.1,
        noise_var: Annotated[float, {"min": 0.0}] = 0.1,
        along: str = along_default,
        dimension: int = 2,
    ) -> WidgetDataModel:
        out = model_to_image(model).kalman_filter(
            gain=gain,
            noise_var=noise_var,
            dims=norm_dims(dimension, img.axes),
            along=along,
        )
        return image_to_model(out, orig=model)

    return run_kalman_filter
