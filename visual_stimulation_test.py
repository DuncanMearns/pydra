from pydra.visual_stimulation import VisualStimulation
from pydra.visual_stimulation.stimuli import GratingsStimulus
from pydra.core import PydraProcess
from multiprocessing import Queue, Pipe, Event
import time


if __name__ == "__main__":

    stimuli = [(GratingsStimulus, dict(spatial=3, temporal=5, duration=3)),
               (GratingsStimulus, dict(spatial=1.5, temporal=5, duration=3)),
               (GratingsStimulus, dict(spatial=0.7, temporal=5, duration=3))]
    window_params= dict(size=[800,600], monitor="testMonitor", units="deg", color=(-1, -1, -1))

    q = Queue()
    conn1, conn2 = Pipe()
    sender = Queue()

    worker = VisualStimulation.make(q=q, receiver=conn1, sender=sender, stimuli=stimuli, window_params=window_params)
    exit_flag = Event()
    start_flag = Event()
    stop_flag = Event()
    finished_flag = Event()
    p_conn1, p_conn2 = Pipe()

    process = PydraProcess(worker, exit_flag, start_flag, stop_flag, finished_flag, p_conn1)
    process.start()
    time.sleep(5.0)

    print("Starting stimulus")
    start_flag.set()
    result = sender.get(timeout=10.)
    if result:
        print("Stimulus finished")
    else:
        print("Flag not received")
    start_flag.clear()
    stop_flag.set()
    finished_flag.wait()
    print(f"Event loop finished")

    print("Exiting...", end=' ')
    exit_flag.set()
    process.join()
    print("done!")
