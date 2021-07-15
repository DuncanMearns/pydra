from pydra import Pydra, ports, config
from pydra.modules.visual_stimulation import VisualStimulationWorker, VisualStimulationWidget
from pathlib import Path


VisualStimulationWorker.window_params = dict(size=(400, 400),
                                             allowGUI=False,
                                             monitor="test_monitor",
                                             units="cm",
                                             color=(-1, -1, -1))


PSYCHOPY = {
    "worker": VisualStimulationWorker,
    "widget": VisualStimulationWidget,
    "params": {"stimulus_file": Path.cwd().joinpath("dotstim.py")}
}

config["modules"] = [PSYCHOPY]


if __name__ == "__main__":
    config = Pydra.configure(config, ports)
    pydra = Pydra.run(working_dir="D:\pydra_tests", **config)
