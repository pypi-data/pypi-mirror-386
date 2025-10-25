from dataclasses import dataclass
from pathlib import Path
from subprocess import Popen
from himena import StandardType, WidgetDataModel
from himena.plugins import register_config, config_field, register_function, get_config


@dataclass
class HimenaImageConfig:
    imagej_path: str = config_field(
        default="",
        tooltip="Path to the ImageJ executable",
    )


register_config("himena-image", "himena-image", HimenaImageConfig())


@register_function(
    menus=["tools/image"],
    types=[StandardType.IMAGE],
    title="Open in ImageJ",
    command_id="himena-image.open-in-imagej",
)
def open_in_imagej(model: WidgetDataModel) -> None:
    ij_cfg = get_config(HimenaImageConfig) or HimenaImageConfig()
    if ij_cfg.imagej_path.strip() == "":
        raise ValueError("ImageJ path is not configured.")
    ij_path = Path(ij_cfg.imagej_path).expanduser().resolve()
    if not ij_path.exists():
        raise FileNotFoundError(f"ImageJ executable not found at {ij_path}")
    if not isinstance(model.source, Path):
        raise ValueError("Image is not saved to a file.")
    Popen([str(ij_path), str(model.source)], start_new_session=True)
