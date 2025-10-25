from typing import Literal, NamedTuple
from himena import WidgetDataModel, Parametric
from himena.plugins import register_function, configure_submenu
from himena_image.utils import image_to_model
import impy as ip

MENU = "file/new/skimage samples"
configure_submenu(MENU, title="scikit-image")


class SampleImage(NamedTuple):
    filename: str
    is_rgb: bool
    axes: str | None = None
    title: str | None = None


SKIMAGE_SAMPLES = [
    SampleImage("astronaut", True, "yxc"),
    SampleImage("brain", False, "zyx"),
    SampleImage("brick", False),
    SampleImage("camera", False),
    SampleImage("cat", True, "yxc"),
    SampleImage("cell", False),
    SampleImage("cells3d", False, "zcyx"),
    SampleImage("checkerboard", False),
    SampleImage("chelsea", True, "yxc"),
    SampleImage("clock", False),
    SampleImage("coffee", True, "yxc"),
    SampleImage("coins", False),
    SampleImage("colorwheel", True, "yxc"),
    SampleImage("eagle", False),
    SampleImage("grass", False),
    SampleImage("gravel", False),
    SampleImage("horse", False),
    SampleImage("hubble_deep_field", True, "yxc"),
    SampleImage("human_mitosis", False),
    SampleImage("immunohistochemistry", True, "yxc"),
    SampleImage("kidney", False, "zyxc"),
    SampleImage("lily", False, "yxc"),
    SampleImage("logo", True, "yxc"),
    SampleImage("microaneurysms", False),
    SampleImage("moon", False),
    SampleImage("nickel_solidification", False, "tyx"),
    SampleImage("page", False),
    SampleImage("palisades_of_vogt", False, "zyx"),
    SampleImage("protein_transport", False, "tcyx"),
    SampleImage("retina", True, "yxc"),
    SampleImage("rocket", True, "yxc"),
    SampleImage("shepp_logan_phantom", False),
    SampleImage("skin", True, "yxc"),
    SampleImage("stereo_motorcycle", True, "yxc"),
    SampleImage("text", False),
    SampleImage("vortex", False),
]


@register_function(title="binary blobs", menus=MENU)
def binary_blobs() -> Parametric:
    from skimage import data

    def make_binary_blobs(
        length: int = 512,
        seed: int = 1,
        blob_size_fraction: float = 0.1,
        volume_fraction: float = 0.5,
        n_dim: Literal[2, 3, 4, 5, 6] = 2,
    ) -> WidgetDataModel[ip.ImgArray]:
        img = data.binary_blobs(
            length=length,
            blob_size_fraction=blob_size_fraction,
            n_dim=n_dim,
            volume_fraction=volume_fraction,
            rng=seed,
        )
        return image_to_model(ip.asarray(img), title="binary blobs")

    return make_binary_blobs


@register_function(title="stereo motorcycle", menus=MENU)
def stereo_motorcycle() -> list[WidgetDataModel[ip.ImgArray]]:
    from skimage import data

    img_left, img_right, disp = data.stereo_motorcycle()
    img_left = ip.asarray(img_left, axes="yxc")
    img_right = ip.asarray(img_right, axes="yxc")
    disp = ip.asarray(disp, axes="yx")
    return [
        image_to_model(img_left, title="Left (stereo_motorcycle)", is_rgb=True),
        image_to_model(img_right, title="Right (stereo_motorcycle)", is_rgb=True),
        image_to_model(disp, title="Disparity (stereo_motorcycle)"),
    ]


def _make_provider(sample: SampleImage):
    def make_sample_image() -> WidgetDataModel[ip.ImgArray]:
        from skimage import data

        img = getattr(data, sample.filename)()
        if sample.title is None:
            title = sample.filename.replace("_", " ").title()
        else:
            title = sample.title
        img = ip.asarray(img, axes=sample.axes)
        if not sample.is_rgb:
            img = img.sort_axes()
        return image_to_model(img, title=title, is_rgb=sample.is_rgb)

    make_sample_image.__name__ = sample.filename
    return make_sample_image


for sample in SKIMAGE_SAMPLES:
    register_function(
        _make_provider(sample),
        title=sample.filename,
        menus=MENU,
        run_async=True,
        command_id=f"himena-image:skimage-sample:{sample.filename.replace('_', '-')}",
    )
