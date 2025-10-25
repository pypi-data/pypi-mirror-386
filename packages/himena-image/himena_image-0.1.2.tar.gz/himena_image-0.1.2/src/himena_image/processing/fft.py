from himena import WidgetDataModel, Parametric, StandardType
from himena.plugins import register_function, configure_gui, configure_submenu
from himena_image.utils import (
    make_dims_annotation,
    image_to_model,
    model_to_image,
    norm_dims,
)

MENUS = ["tools/image/process/fft", "/model_menu/process/fft"]

configure_submenu(MENUS, title="Fourier transform")


@register_function(
    title="FFT ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    run_async=True,
    command_id="himena-image:fft",
)
def fft(model: WidgetDataModel) -> Parametric:
    """Fast Fourier transformation of an image."""

    @configure_gui(dimension={"choices": make_dims_annotation(model)}, preview=True)
    def run_fft(
        origin_in_center: bool = True,
        double_precision: bool = False,
        dimension=2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.fft(
            shift=origin_in_center,
            double_precision=double_precision,
            dims=norm_dims(dimension, img.axes),
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing).astype(
            StandardType.IMAGE_FOURIER
        )

    return run_fft


@register_function(
    title="IFFT ...",
    menus=MENUS,
    types=[StandardType.IMAGE, StandardType.IMAGE_FOURIER],
    run_async=True,
    command_id="himena-image:ifft",
)
def ifft(model: WidgetDataModel) -> Parametric:
    """Inverse fast Fourier transformation of a frequency image."""

    @configure_gui(
        dimension={"choices": make_dims_annotation(model)},
        preview=True,
    )
    def run_ifft(
        return_real: bool = True,
        origin_in_center: bool = True,
        double_precision: bool = False,
        dimension=2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model, is_previewing)
        out = img.ifft(
            real=return_real,
            shift=origin_in_center,
            double_precision=double_precision,
            dims=norm_dims(dimension, img.axes),
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_ifft


@register_function(
    title="Power spectrum ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    run_async=True,
    command_id="himena-image:power-spectrum",
)
def power_spectrum(model: WidgetDataModel) -> Parametric:
    """Compute the power spectrum of an image."""

    @configure_gui(
        dimension={"choices": make_dims_annotation(model)},
        norm={"label": "normalize maximum to 1"},
        zero_norm={"label": "normalize zero frequency to 0"},
        preview=True,
    )
    def run_power_spectrum(
        origin_in_center: bool = True,
        norm: bool = False,
        zero_norm: bool = False,
        double_precision: bool = False,
        dimension=2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        """Run the power spectrum calculation.

        Parameters
        ----------
        origin_in_center : bool, optional
            If True, the zero frequency is in the center of the image. Otherwise, it is
            in the A[0, 0] position.
        norm : bool, optional
            If True, the maximum value of the power spectrum is normalized to 1.
        zero_norm : bool, optional
            If True, the zero frequency is normalized to 0.
        double_precision : bool, optional
            If True, the calculation is done in double precision (float64). Otherwise,
            it is done in single precision (float32).
        """
        img = model_to_image(model, is_previewing)
        out = img.power_spectra(
            shift=origin_in_center,
            double_precision=double_precision,
            norm=norm,
            zero_norm=zero_norm,
            dims=norm_dims(dimension, img.axes),
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing).astype(
            StandardType.IMAGE_FOURIER
        )

    return run_power_spectrum


@register_function(
    title="Low-pass Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    run_async=True,
    command_id="himena-image:lowpass-filter",
    group="fft-filter",
)
def lowpass_filter(model: WidgetDataModel) -> Parametric:
    """Apply a low-pass filter to an image."""

    @configure_gui(
        dimension={"choices": make_dims_annotation(model)},
        cutoff={"min": 0.0, "max": 1.0},
        order={"min": 1},
        preview=True,
    )
    def run_lowpass_filter(
        cutoff: float = 0.2,
        order: int = 2,
        dimension=2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.lowpass_filter(
            cutoff=cutoff, order=order, dims=norm_dims(dimension, img.axes)
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_lowpass_filter


@register_function(
    title="High-pass Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    run_async=True,
    command_id="himena-image:highpass-filter",
    group="fft-filter",
)
def highpass_filter(model: WidgetDataModel) -> Parametric:
    """Apply a high-pass filter to an image."""

    @configure_gui(
        dimension={"choices": make_dims_annotation(model)},
        cutoff={"min": 0.0, "max": 1.0},
        order={"min": 1},
        preview=True,
    )
    def run_highpass_filter(
        cutoff: float = 0.2,
        order: int = 2,
        dimension=2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.highpass_filter(
            cutoff=cutoff,
            order=order,
            dims=norm_dims(dimension, img.axes),
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_highpass_filter


@register_function(
    title="Band-pass Filter ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    run_async=True,
    command_id="himena-image:bandpass-filter",
    group="fft-filter",
)
def bandpass_filter(model: WidgetDataModel) -> Parametric:
    """Apply a band-pass filter to an image."""

    @configure_gui(
        dimension={"choices": make_dims_annotation(model)},
        cutoff={"min": 0.0, "max": 1.0},
        cuton={"min": 0.0, "max": 1.0},
        preview=True,
    )
    def run_bandpass_filter(
        cuton: float = 0.2,
        cutoff: float = 0.5,
        order: int = 2,
        dimension=2,
        is_previewing: bool = False,
    ) -> WidgetDataModel:
        img = model_to_image(model)
        out = img.bandpass_filter(
            cuton=cuton,
            cutoff=cutoff,
            order=order,
            dims=norm_dims(dimension, img.axes),
        )
        return image_to_model(out, orig=model, is_previewing=is_previewing)

    return run_bandpass_filter
