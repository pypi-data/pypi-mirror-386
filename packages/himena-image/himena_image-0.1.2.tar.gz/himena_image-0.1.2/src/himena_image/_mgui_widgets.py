from __future__ import annotations

from magicgui.widgets.bases import ValuedContainerWidget
from magicgui.widgets import PushButton
from magicgui.types import Undefined
from himena.qt.magicgui import FloatEdit


class PointEdit(ValuedContainerWidget[tuple[float, float]]):
    def __init__(self, point=Undefined, **kwargs):
        kwargs.setdefault("layout", "horizontal")
        getter = kwargs.pop("getter", lambda *_: None)
        if point is Undefined:
            point = (0.0, 0.0)
        self._x_value = FloatEdit(value=point[0], label="x")
        self._y_value = FloatEdit(value=point[1], label="y")
        self._read_btn = PushButton(text="Read")
        self._read_btn.clicked.connect(self._read_point_coords)
        self._getter = getter
        widgets = [self._x_value, self._y_value, self._read_btn]
        super().__init__(value=point, widgets=widgets, **kwargs)
        self.margins = (0, 0, 0, 0)
        self._x_value.changed.connect(self._value_changed)
        self._y_value.changed.connect(self._value_changed)

    def _read_point_coords(self):
        points = self._getter(self)
        if points is not None:
            self.value = points

    def _value_changed(self):
        self.changed.emit(self.value)

    def get_value(self):
        return (self._x_value.value, self._y_value.value)

    def set_value(self, value):
        x, y = value
        self._x_value.value = x
        self._y_value.value = y
