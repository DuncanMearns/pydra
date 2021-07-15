from pydra.modules.visual_stimulation import Stimulus, Wait
from psychopy import visual


class MovingDot(Stimulus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xpos = 0
        self.ypos = 0

    def on_start(self):
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

    def update(self):
        self.xpos += 0.1
        self.dot.setPos((self.xpos, self.ypos))
        self.dot.draw()
        if self.xpos > 10.:
            self.finished = True

    def on_stop(self):
        self.xpos = 0
        self.ypos = 0
        self.dot.setPos((self.xpos, self.ypos))


dot1 = MovingDot()
dot2 = MovingDot()
wait1 = Wait(2.)
dot3 = MovingDot()

stimulus_list = [dot1, dot2, wait1, dot3]
