# Copyright (c) Acconeer AB, 2023
# All rights reserved

import acconeer.exptool as et
from acconeer.exptool import a121

from . import Detector, DetectorConfig


parser = a121.ExampleArgumentParser()
parser.add_argument("--sensor", type=int, default=1)
args = parser.parse_args()
et.utils.config_logging(args)

client = a121.Client.open(**a121.get_client_args(args))

detector_config = DetectorConfig(start_m=0.15, end_m=0.5)

detector = Detector(
    client=client,
    sensor_ids=[args.sensor],
    detector_config=detector_config,
)

detector.calibrate_detector()
detector.start()

interrupt_handler = et.utils.ExampleInterruptHandler()
print("Press Ctrl-C to end session")

while not interrupt_handler.got_signal:
    detector_result = detector.get_next()

    print(detector_result, "\n")

print("Disconnecting...")
detector.stop()
client.close()
