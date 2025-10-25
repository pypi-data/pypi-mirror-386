from ndv import DataWrapper
from typing import Any, Hashable, Mapping, Sequence
import numpy as np
from himena.types import WidgetDataModel
from himena.standards.model_meta import ImageMeta
from enum import Enum, auto


class ModelDataWrapper(DataWrapper):
    def __init__(self, model: WidgetDataModel):
        super().__init__(model.value)
        if not isinstance(meta := model.metadata, ImageMeta):
            raise ValueError("Invalid metadata")
        self._meta = meta
        self._type = model.type
        self._complex_conversion = ComplexConversionRule.ABS

    @classmethod
    def supports(cls, obj: Any) -> bool:
        return isinstance(obj, WidgetDataModel)

    @property
    def dims(self) -> tuple[str, ...]:
        if axes := self._meta.axes:
            return tuple(a.name for a in axes)
        return tuple(f"axis_{i}" for i in range(len(self._data.shape)))

    @property
    def coords(self) -> Mapping[Hashable, Sequence]:
        """Return the coordinates for the data."""
        return {d: range(s) for d, s in zip(self.dims, self.data.shape)}

    def isel(self, indexers: Mapping[int, int | slice]) -> np.ndarray:
        """Select a slice from a data store using (possibly) named indices."""
        import dask.array as da

        sl = [slice(None)] * len(self._data.shape)
        for k, v in indexers.items():
            sl[k] = v
        out = self._data[tuple(sl)]
        if isinstance(out, da.Array):
            out = out.compute()
        assert isinstance(out, np.ndarray)
        if out.dtype.kind == "b":
            return out.astype(np.uint8)
        elif out.dtype.kind == "c":
            return self._complex_conversion.apply(out)
        return out

    def sizes(self):
        if axes := self._meta.axes:
            names = [a.name for a in axes]
        else:
            names = list(range(len(self._data.shape)))
        return dict(zip(names, self._data.shape))


class ComplexConversionRule(Enum):
    ABS = auto()
    REAL = auto()
    IMAG = auto()
    PHASE = auto()
    LOG_ABS = auto()

    def apply(self, data: np.ndarray) -> np.ndarray:
        if self == ComplexConversionRule.ABS:
            return np.abs(data)
        elif self == ComplexConversionRule.REAL:
            return data.real
        elif self == ComplexConversionRule.IMAG:
            return data.imag
        elif self == ComplexConversionRule.PHASE:
            return np.angle(data)
        elif self == ComplexConversionRule.LOG_ABS:
            return np.log(np.abs(data) + 1e-10)
        raise ValueError(f"Unknown complex conversion rule: {self}")
