import pytest
from himena.widgets import MainWindow


@pytest.mark.parametrize(
    "command",
    [
        "himena-image:gaussian-filter",
        "himena-image:median-filter",
        "himena-image:mean-filter",
        "himena-image:std-filter",
        "himena-image:coef-filter",
        "himena-image:dog-filter",
        "himena-image:doh-filter",
        "himena-image:log-filter",
        "himena-image:laplacian-filter",
    ],
)
def test_filter(make_himena_ui, image_data, command: str):
    ui: MainWindow = make_himena_ui(backend="mock")
    win = ui.add_data_model(image_data)
    ui.exec_action(
        command,
        model_context=win.to_model(),
        with_params={},
    )
