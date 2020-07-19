from pydra.process import *
from multiprocessing import Event, Queue


class PydraPipeline:

    def __init__(self, acquisition: type, acquisition_kwargs: dict,
                 tracking: type, tracking_kwargs: dict,
                 saving: type, saving_kwargs: dict):
        """Handles multiprocessing of frame acquisition, tracking and saving."""
        # Signalling between process
        self.exit_signal = Event()  # top-level exit signal for process
        self.finished_acquisition_signal = Event()  # exit signal set when frame acquisition has ended
        self.finished_tracking_signal = Event()  # exit signal set when tracking has ended
        self.finished_saving_signal = Event()  # exit signal set when saving has ended
        # Queues
        self.frame_queue = Queue()  # queue filled by acquisition process and emptied by tracking process
        self.tracking_queue = Queue()  # queue filled by tracking process and emptied by saving process
        # Workers
        acquisition_kwargs.update(q=self.frame_queue)
        self.acquisition_constructor = WorkerConstructor(acquisition, **acquisition_kwargs)
        tracking_kwargs.update(input_q=self.frame_queue, output_queue=self.tracking_queue)
        self.tracking_constructor = WorkerConstructor(tracking, **tracking_kwargs)
        saving_kwargs.update(q=self.tracking_queue)
        self.saving_constructor = WorkerConstructor(saving, **saving_kwargs)

    def start(self):
        # Initialise the acquisition process
        self.acquisition_process = PydraProcess(self.acquisition_constructor,
                                                self.exit_signal,
                                                self.finished_acquisition_signal)
        # Initialise the tracking process
        self.tracking_process = PydraProcess(self.tracking_constructor,
                                             self.finished_acquisition_signal,
                                             self.finished_tracking_signal,)
        # Initialise the saving process
        self.saving_process = PydraProcess(self.saving_constructor,
                                           self.finished_tracking_signal,
                                           self.finished_saving_signal)
        # Start all process
        self.acquisition_process.start()
        self.tracking_process.start()
        self.saving_process.start()
        print('All processes started.')

    def stop(self):
        # Set the top-level exit signal telling the acquisition process to end
        self.exit_signal.set()
        # Join all process
        self.acquisition_process.join()
        print('acquisition ended')
        # print(self.gui_queue.queue.qsize())
        self.tracking_process.join()
        print('tracking ended')
        self.saving_process.join()
        print('All process terminated.')
