from __future__ import annotations

from typing import TYPE_CHECKING
from cmap import Colormap
from qtpy import QtWidgets as QtW, QtCore

from ndv import ArrayViewer
from superqt import QEnumComboBox
from himena.types import WidgetDataModel
from himena.standards.model_meta import ImageMeta, DimAxis
from himena.plugins import validate_protocol
from himena_image.widgets._wrapper import ComplexConversionRule

if TYPE_CHECKING:
    from ndv.views._qt._array_view import _QArrayViewer


class NDImageViewer(ArrayViewer):
    def __init__(self):
        super().__init__()
        self._control_widget = QtW.QWidget()
        layout = QtW.QHBoxLayout(self._control_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        spacer = QtW.QWidget()
        spacer.setSizePolicy(
            QtW.QSizePolicy.Policy.Expanding, QtW.QSizePolicy.Policy.Expanding
        )
        layout.addWidget(spacer)
        container = QtW.QWidget()
        self._complex_conversion_rule_cbox = QEnumComboBox(
            enum_class=ComplexConversionRule
        )
        self._complex_conversion_rule_cbox.currentEnumChanged.connect(
            self._on_complex_conversion_rule_changed
        )
        layout.addWidget(self._complex_conversion_rule_cbox)
        layout.addWidget(container)

    @validate_protocol
    def update_model(self, model: WidgetDataModel):
        self.data = model
        is_complex = model.value.dtype.kind == "c"
        self._complex_conversion_rule_cbox.setVisible(is_complex)
        meta = model.metadata
        if isinstance(meta, ImageMeta):
            if meta.is_rgb:
                raise ValueError("RGB images are not supported yet")
            for ch, lut in zip(meta.channels, self.display_model.luts.values()):
                lut.cmap = ch.colormap or "gray"
                lut.clims = ch.contrast_limits
        if is_complex:
            self._complex_conversion_rule_cbox.setCurrentEnum(ComplexConversionRule.ABS)

    @validate_protocol
    def to_model(self) -> WidgetDataModel:
        indices = [
            None if isinstance(v, slice) else v
            for v in self.display_model.current_index.values()
        ]
        self.display_model.luts
        return WidgetDataModel(
            value=self.data,
            type=self.model_type(),
            metadata=ImageMeta(
                current_indices=indices,
                axes=[DimAxis(name=a) for a in self.data_wrapper.dims],
            ),
        )

    @validate_protocol
    def size_hint(self) -> tuple[int, int]:
        return (320, 400)

    @validate_protocol
    def model_type(self) -> str:
        return self.data_wrapper._type

    @validate_protocol
    def native_widget(self) -> _QArrayViewer:
        return self.widget()

    @validate_protocol
    def control_widget(self):
        return self._control_widget

    def _on_complex_conversion_rule_changed(self, enum_: ComplexConversionRule):
        self.data_wrapper._complex_conversion = enum_
        if enum_ is ComplexConversionRule.PHASE:
            cmap_name = "cmocean:phase"
        else:
            cmap_name = "inferno"
        # for ctrl in self._lut_ctrls.values():
        #     ctrl._cmap.setCurrentColormap(cmap.Colormap(cmap_name))
        # self.refresh()
        for val in self.display_model.luts.values():
            val.cmap = Colormap(cmap_name)
