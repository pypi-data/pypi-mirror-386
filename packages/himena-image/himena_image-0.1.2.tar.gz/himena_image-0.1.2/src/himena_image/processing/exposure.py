from cmap import Colormap
from himena import WidgetDataModel, Parametric, create_model
from himena.widgets import TabArea
from himena.consts import StandardType
from himena.plugins import register_function, configure_gui
from himena.standards import roi, plotting as hplt
from himena.standards.model_meta import ImageMeta
import numpy as np
from himena.widgets import SubWindow
from himena_image.utils import model_to_image

MENUS = ["tools/image/exposure", "/model_menu/exposure"]


@register_function(
    title="Histogram",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:histogram",
    run_async=True,
    group="exposure",
)
def histogram(model: WidgetDataModel) -> Parametric:
    """Show histogram of the image."""
    from skimage.exposure import histogram as skimage_histogram

    img = model_to_image(model)
    meta = _cast_meta(model)
    if meta.is_rgb:
        caxis = -1
        colors = ["red", "green", "blue"]
    elif meta.channel_axis is None:
        caxis = None
        colors = ["gray"]
    else:
        caxis = meta.channel_axis
        colors = [Colormap(chn.colormap or "gray")(0.5).hex for chn in meta.channels]

    @configure_gui(
        bins={"min": 2, "max": 2048},
        normalize={"label": "Normalize the histogram by the sum"},
        channel_axis={"bind": caxis},
        colors={"bind": colors},
    )
    def run_histogram(
        bins: int = 256,
        normalize: bool = True,
        channel_axis: int | None = None,
        colors: list[str] = (),
    ) -> WidgetDataModel:
        """Run histogram."""
        for ith, color in enumerate(colors):
            if channel_axis is not None:
                img_slice = img.value.take(ith, axis=channel_axis)
            else:
                img_slice = img.value
            hist, bin_center = skimage_histogram(
                img_slice, nbins=bins, normalize=normalize
            )
            fig = hplt.figure()
            fig.plot(bin_center, hist, color=color)
        fig.axes.x.label = "Intensity"
        fig.axes.y.label = "Frequency"
        return create_model(
            fig,
            type=StandardType.PLOT,
            title=f"Histogram of {model.title}",
        )

    return run_histogram


@register_function(
    title="Auto contrast at selection",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:auto-contrast-selection",
    group="exposure",
)
def auto_contrast_at_selection(win: SubWindow):
    """Auto contrast the image."""

    model = win.to_model()
    img = model_to_image(model)
    meta = _cast_meta(model)
    sl = tuple(slice(None) if i is None else i for i in meta.current_indices)
    img_slice = img.value[sl]
    if meta.is_rgb:
        img_slice = np.mean(img_slice, axis=-1)
    if isinstance(cur_roi := meta.current_roi, roi.Roi2D):
        mask = cur_roi.to_mask(img_slice.shape)
        hist = img_slice[mask].ravel()
        min_val = hist.min()
        max_val = hist.max()
    else:
        raise ValueError("Current ROI is not a 2D ROI.")
    if meta.channel_axis is None:
        i_channel = 0
    else:
        i_channel = meta.channel_axis
    meta.channels[i_channel].contrast_limits = (min_val, max_val)
    win.update_model(
        model.with_metadata(meta.model_copy(update={"channels": meta.channels}))
    )


@register_function(
    title="Propagate contrast ...",
    menus=MENUS,
    types=[StandardType.IMAGE],
    command_id="himena-image:propagate-contrast",
    group="exposure",
)
def propagate_contrast(model: WidgetDataModel, tab: TabArea):
    """Propagate contrast to other images in the same tab area."""

    meta = _cast_meta(model)
    clim_map = {
        channel.colormap: channel.contrast_limits
        for channel in meta.channels
        if channel.colormap is not None
    }
    for win in tab:
        if win.model_type() != StandardType.IMAGE:
            continue
        model = win.to_model()
        this_meta = _cast_meta(model)
        if this_meta.is_rgb:
            continue
        new_channels = []
        for chn in this_meta.channels:
            if new_clim := clim_map.get(chn.colormap, None):
                new_channels.append(
                    chn.model_copy(update={"contrast_limits": new_clim})
                )
            else:
                new_channels.append(chn)
        new_meta = this_meta.model_copy(update={"channels": new_channels})
        model = model.with_metadata(new_meta)
        win.update_model(model)
    return None


def _cast_meta(model: WidgetDataModel) -> ImageMeta:
    """Cast the metadata to ImageMeta."""
    if not isinstance(model.metadata, ImageMeta):
        raise TypeError("Metadata is not of type ImageMeta.")
    return model.metadata
