from typing import Annotated, Literal

PaddingMode = Literal["reflect", "constant", "nearest", "mirror", "wrap"]
InterpolationOrder = Annotated[
    int,
    {
        "choices": [("nearest", 0), ("linear", 1), ("cubic", 3)],
        "widget_type": "ComboBox",
    },
]
