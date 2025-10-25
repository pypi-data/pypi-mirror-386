import numpy as np
from himena import WidgetDataModel, StandardType
from himena.standards.model_meta import ImageMeta, DimAxis
from himena.testing import install_plugin
import pytest

@pytest.fixture(scope="session", autouse=True)
def init_pytest(request):
    install_plugin("himena-image")

@pytest.fixture(scope="function")
def image_data():
    rng = np.random.default_rng(0)
    return WidgetDataModel(
        value=rng.normal(size=(4, 5, 2, 6, 5)),
        type=StandardType.IMAGE,
        metadata=ImageMeta(
            axes=[
                DimAxis(name="t", scale=0.2, unit="sec"),
                DimAxis(name="z", scale=1.5, unit="um"),
                DimAxis(name="c", labels=["green", "red"]),
                DimAxis(name="y", scale=0.9, unit="um"),
                DimAxis(name="x", scale=0.9, unit="um"),
            ],
            channel_axis=2,
            is_rgb=False,
        ),
    )
