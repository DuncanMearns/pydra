from pydra import Pydra, ports, config
from pydra.modules.cameras.video import VIDEO
from pydra.modules.tracking.tail_tracker import TAIL_TRACKER, TailOverlay


VIDEO["params"]["filepath"] = r"D:\DATA\embedded_prey_capture\raw_data\2021_05_21\fish01_red_centre_10%_001.avi"
VIDEO["params"]["frame_rate"] = 50.
VIDEO["plotter"] = TailOverlay

TAIL_TRACKER["params"]["acquisition_worker"] = "video"
TAIL_TRACKER["params"]["cachesize"] = 5000
TAIL_TRACKER["worker"].subscriptions = ("video",)

config["modules"] = [VIDEO, TAIL_TRACKER]


if __name__ == "__main__":
    config = Pydra.configure(config, ports)
    pydra = Pydra.run(working_dir="D:\pydra_tests", **config)
