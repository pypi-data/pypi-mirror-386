# Copyright (c) Acconeer AB, 2022-2023
# All rights reserved

from acconeer.exptool import a121

from ._processor import MeasurementType, ProcessorConfig


def get_close_sensor_config() -> a121.SensorConfig:
    return a121.SensorConfig(
        sweeps_per_frame=16,
        sweep_rate=320,
        continuous_sweep_mode=True,
        double_buffering=True,
        inter_sweep_idle_state=a121.IdleState.READY,
        inter_frame_idle_state=a121.IdleState.READY,
        num_points=3,
        profile=a121.Profile.PROFILE_1,
        receiver_gain=0,
        hwaas=40,
        start_point=0,
        step_length=6,
    )


def get_close_processor_config() -> ProcessorConfig:
    return ProcessorConfig(measurement_type=MeasurementType.CLOSE_RANGE)


def get_far_sensor_config() -> a121.SensorConfig:
    return a121.SensorConfig(
        sweeps_per_frame=16,
        sweep_rate=320,
        continuous_sweep_mode=True,
        double_buffering=True,
        inter_sweep_idle_state=a121.IdleState.READY,
        inter_frame_idle_state=a121.IdleState.READY,
        start_point=0,
        num_points=3,
        step_length=24,
        profile=a121.Profile.PROFILE_3,
        hwaas=60,
        receiver_gain=5,
    )


def get_far_processor_config() -> ProcessorConfig:
    return ProcessorConfig(measurement_type=MeasurementType.FAR_RANGE)


def get_close_and_far_sensor_config() -> a121.SensorConfig:
    return a121.SensorConfig(
        sweeps_per_frame=16,
        sweep_rate=320,
        continuous_sweep_mode=True,
        double_buffering=True,
        inter_sweep_idle_state=a121.IdleState.READY,
        inter_frame_idle_state=a121.IdleState.READY,
        subsweeps=[
            a121.SubsweepConfig(
                start_point=0,
                num_points=3,
                step_length=6,
                profile=a121.Profile.PROFILE_1,
                hwaas=40,
                receiver_gain=0,
            ),
            a121.SubsweepConfig(
                start_point=0,
                num_points=3,
                step_length=24,
                profile=a121.Profile.PROFILE_3,
                hwaas=60,
                receiver_gain=5,
            ),
        ],
    )


def get_close_and_far_processor_config() -> ProcessorConfig:
    return ProcessorConfig(measurement_type=MeasurementType.CLOSE_AND_FAR_RANGE)
