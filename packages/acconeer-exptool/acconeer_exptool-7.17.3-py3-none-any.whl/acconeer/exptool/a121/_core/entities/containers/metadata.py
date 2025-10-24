# Copyright (c) Acconeer AB, 2022-2024
# All rights reserved

from __future__ import annotations

import json
from typing import Any, Optional, Tuple

import attrs
import numpy as np
import numpy.typing as npt

from acconeer.exptool._core.class_creation.attrs import attrs_ndarray_eq


@attrs.frozen(kw_only=True)
class Metadata:
    """Metadata

    Represents a super set of the RSS ``processing_metadata``.
    """

    _frame_data_length: int = attrs.field()
    _sweep_data_length: int = attrs.field()
    _subsweep_data_offset: npt.NDArray[np.int_] = attrs.field(eq=attrs_ndarray_eq)
    _subsweep_data_length: npt.NDArray[np.int_] = attrs.field(eq=attrs_ndarray_eq)
    _calibration_temperature: int = attrs.field()
    _tick_period: int = attrs.field()
    _base_step_length_m: float = attrs.field()
    _max_sweep_rate: float = attrs.field()
    _high_speed_mode: Optional[bool] = attrs.field(default=None)

    @property
    def frame_data_length(self) -> int:
        """Number of elements in the frame"""
        return self._frame_data_length

    @property
    def sweep_data_length(self) -> int:
        """Number of elements in the sweep"""
        return self._sweep_data_length

    @property
    def subsweep_data_offset(self) -> npt.NDArray[np.int_]:
        """Offset to the subsweeps data"""
        return self._subsweep_data_offset

    @property
    def subsweep_data_length(self) -> npt.NDArray[np.int_]:
        """Number of elements in the subsweeps"""
        return self._subsweep_data_length

    @property
    def calibration_temperature(self) -> int:
        """Temperature during calibration"""
        return self._calibration_temperature

    @property
    def tick_period(self) -> int:
        """Target tick period if update rate is set, otherwise 0"""
        return self._tick_period

    @property
    def base_step_length_m(self) -> float:
        """Base step length in meter"""
        return self._base_step_length_m

    @property
    def max_sweep_rate(self) -> float:
        """Maximum sweep rate that the sensor can provide for the given configuration"""
        return self._max_sweep_rate

    @property
    def high_speed_mode(self) -> Optional[bool]:
        """Flag indicating if high speed mode is used.
        If true, it means that the sensor has been configured in a way where it
        can optimize its measurements and obtain a high max sweep rate.

        Configuration limitations to enable high speed mode:
        - Continuous sweep mode: off
        - Inter sweep idle state: Ready
        - Subsweeps: 1
        - Profile 3-5

        Note: Available in RSS version > 0.8.0
        """
        return self._high_speed_mode

    @property
    def frame_shape(self) -> Tuple[int, int]:
        """The frame shape this Metadata defines"""

        num_sweeps = self.frame_data_length // self.sweep_data_length
        return (num_sweeps, self.sweep_data_length)

    def to_dict(self) -> dict[str, Any]:
        raw_dict = attrs.asdict(self)
        if self.high_speed_mode is None:
            raw_dict.pop("_high_speed_mode")
        # Remove preceding underscores to be able to recreate the class in from_dict
        return {k[1:] if k.startswith("_") else k: v for k, v in raw_dict.items()}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Metadata:
        return cls(**d)

    def to_json(self) -> str:
        return json.dumps(self, cls=MetadataEncoder)

    @classmethod
    def from_json(cls, json_str: str) -> Metadata:
        return cls.from_dict(json.loads(json_str, cls=MetadataDecoder))


class MetadataEncoder(json.JSONEncoder):
    """Encoder that transforms a Metadata instance to a serializable
    dict before any json transformation
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Metadata):
            metadata_dict = obj.to_dict()

            # numpy arrays are not serializable.
            # Since they are integer arrays, no precision will be lost
            metadata_dict["subsweep_data_length"] = metadata_dict["subsweep_data_length"].tolist()
            metadata_dict["subsweep_data_offset"] = metadata_dict["subsweep_data_offset"].tolist()
            return metadata_dict

        return super().default(obj)


class MetadataDecoder(json.JSONDecoder):
    """Decoder that post-processes the dict (parsed from json) to better fit Metadata.from_dict"""

    def decode(self, s: str) -> Any:  # type: ignore[override]
        metadata_dict = super().decode(s)

        # post process the parsed dict to have numpy-arrays instead of plain lists
        metadata_dict["subsweep_data_length"] = np.array(metadata_dict["subsweep_data_length"])
        metadata_dict["subsweep_data_offset"] = np.array(metadata_dict["subsweep_data_offset"])

        return metadata_dict
