from pydra import Pydra, ports, config
from pydra.modules.visual_stimulation import VisualStimulationWorker, VisualStimulationWidget, Stimulus
from psychopy import visual


class MovingDot(Stimulus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xpos = 0
        self.ypos = 0
        self.dot = visual.Circle(win=self.window,
                                 radius=0.1,
                                 pos=(self.xpos, self.ypos),
                                 units="cm",
                                 fillColor=(1, 1, 1),
                                 fillColorSpace=u'rgb',
                                 lineColor=(1, 1, 1),
                                 lineColorSpace=u'rgb')
        self.dot.setAutoDraw(False)

    def start(self):
        self.xpos = 0
        self.ypos = 0
        self.dot.setPos((self.xpos, self.ypos))
        self.dot.draw()
        self.window.flip()

    def update(self):
        self.xpos += 0.1
        self.dot.setPos((self.xpos, self.ypos))
        self.dot.draw()
        self.window.flip()

    def stop(self):
        self.xpos = 0
        self.ypos = 0
        self.dot.setPos((self.xpos, self.ypos))
        self.window.flip()


VisualStimulationWorker.window_params = dict(size=(400, 400),
                                             allowGUI=False,
                                             monitor="test_monitor",
                                             units="cm",
                                             color=(-1, -1, -1))


PSYCHOPY = {
    "worker": VisualStimulationWorker,
    "widget": VisualStimulationWidget,
    "params": dict(stimulus=MovingDot)
}

config["modules"] = [PSYCHOPY]


if __name__ == "__main__":
    config = Pydra.configure(config, ports)
    pydra = Pydra.run(working_dir="D:\pydra_tests", **config)
