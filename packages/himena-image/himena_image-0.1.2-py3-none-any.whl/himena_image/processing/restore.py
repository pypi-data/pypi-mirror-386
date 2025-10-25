from himena import WidgetDataModel, Parametric
from himena.consts import StandardType
from himena.plugins import register_function, configure_gui
from himena_image.consts import PaddingMode, InterpolationOrder
from himena_image.utils import (
    make_dims_annotation,
    image_to_model,
    model_to_image,
    norm_dims,
)

MENUS = ["tools/image/process/restore", "/model_menu/process/restore"]


@register_function(
    title="Track drift ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:track-drift",
    group="00-drift",
    run_async=True,
)
def track_drift(model: WidgetDataModel) -> Parametric:
    """Track drift in the image."""
    img = model_to_image(model)
    along_default, along_choices = _along_default_and_choices(img.axes)

    @configure_gui(
        along={"choices": along_choices, "value": along_default},
        dimension={"choices": make_dims_annotation(model)},
    )
    def run_track_drift(
        along: str,
        max_shift: float | None = None,
        upsample_factor: int = 10,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.track_drift(
            along=along,
            upsample_factor=upsample_factor,
            max_shift=max_shift,
        )

        return WidgetDataModel(
            value=out,
            type=StandardType.DATAFRAME,
        )

    return run_track_drift


@register_function(
    title="Drift correction ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:drift-correction",
    group="00-drift",
    run_async=True,
)
def drift_correction(model: WidgetDataModel) -> Parametric:
    """Correct drift in the image."""
    img = model_to_image(model)
    along_default, along_choices = _along_default_and_choices(img.axes)

    @configure_gui(
        along={"choices": along_choices, "value": along_default},
        dimension={"choices": make_dims_annotation(model)},
    )
    def run_drift_correction(
        along: str,
        reference: str = "",
        zero_ave: bool = True,
        max_shift: float | None = None,
        order: InterpolationOrder = 1,
        mode: PaddingMode = "constant",
        cval: float = 0.0,
        dimension: int = 2,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.drift_correction(
            ref=reference or None,
            zero_ave=zero_ave,
            along=along,
            max_shift=max_shift,
            mode=mode,
            cval=cval,
            order=order,
            dims=norm_dims(dimension, img.axes),
        )
        return image_to_model(out, orig=model)

    return run_drift_correction


def _along_default_and_choices(axes) -> tuple[str, list[str]]:
    along_choices = [str(a) for a in axes]
    if "t" in along_choices:
        along_default = "t"
    elif "z" in along_choices:
        along_default = "z"
    else:
        along_default = along_choices[0]
    return along_default, along_choices


@register_function(
    title="Richardson-Lucy deconvolution ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:lucy-deconv",
    group="20-deconvolution",
    run_async=True,
)
def lucy(model: WidgetDataModel) -> Parametric:
    """Restore image using poin spread function by Richardson-Lucy's method"""

    @configure_gui(
        psf={"types": [StandardType.IMAGE]},
        dimension={"choices": make_dims_annotation(model)},
    )
    def run_lucy(
        psf: WidgetDataModel,
        niter: int = 50,
        dimension: int = 2,
        eps: float = 1e-5,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.lucy(psf, niter=niter, eps=eps, dims=norm_dims(dimension, img.axes))
        return image_to_model(out, orig=model)

    return run_lucy


@register_function(
    title="Richardson-Lucy TV deconvolution ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:lucy-tv-deconv",
    group="20-deconvolution",
    run_async=True,
)
def lucy_tv(model: WidgetDataModel) -> Parametric:
    """Restore image using poin spread function by Richardson-Lucy's method with total
    variance regularization."""

    @configure_gui(
        psf={"types": [StandardType.IMAGE]},
        dimension={"choices": make_dims_annotation(model)},
    )
    def run_lucy_tv(
        psf: WidgetDataModel,
        niter: int = 50,
        dimension: int = 2,
        lmd: float = 1.0,
        tol: float = 1e-3,
        eps: float = 1e-5,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.lucy_tv(
            psf,
            niter=niter,
            lmd=lmd,
            tol=tol,
            eps=eps,
            dims=norm_dims(dimension, img.axes),
        )
        return image_to_model(out, orig=model)

    return run_lucy_tv
