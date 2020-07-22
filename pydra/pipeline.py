from .core import *
from multiprocessing import Event, Queue


class Pipeline:

    def __init__(self, acquisition: type, acquisition_kwargs: dict,
                 tracking: type, tracking_kwargs: dict,
                 saving: type, saving_kwargs: dict,
                 protocol: type):
        """Handles multiprocessing of frame acquisition, tracking and saving."""
        # Flags
        self.exit_flag = Event()  # top-level exit signal for process
        self.start_pipeline = Event()
        self.end_acquisition = Event()
        self.end_tracking = Event()
        self.end_saving = Event()
        self.pipeline_finished = Event()
        # Queues
        self.frame_queue = Queue()  # queue filled by acquisition core and emptied by tracking core
        self.tracking_queue = Queue()  # queue filled by tracking core and emptied by saving core
        # Acquisition
        self.send_acquisition, self.acquisition_conn = pipe()
        acquisition_kwargs.update(q=self.frame_queue)
        self.acquisition_constructor = acquisition.make(**acquisition_kwargs)
        # Tracking
        self.send_tracking, self.tracking_conn = pipe()
        tracking_kwargs.update(input_q=self.frame_queue, output_queue=self.tracking_queue)
        self.tracking_constructor = tracking.make(**tracking_kwargs)
        # Saving
        self.send_saving, self.saving_conn = pipe()
        saving_kwargs.update(q=self.tracking_queue)
        self.saving_constructor = saving.make(**saving_kwargs)

        # Protocol
        self.protocol_constructor = protocol.make()
        self.start_protcol = Event()
        self.stop_protocol = Event()
        self.protocol_finished = Event()
        self.send_protcol, self.protocol_conn = pipe()

    def run(self):
        # Initialize the acquisition process
        self.acquisition_process = PydraProcess(self.acquisition_constructor,
                                                self.exit_flag,
                                                self.start_pipeline,
                                                self.end_acquisition,
                                                self.end_tracking,
                                                self.acquisition_conn)
        # Initialize the tracking process
        self.tracking_process = PydraProcess(self.tracking_constructor,
                                             self.exit_flag,
                                             self.start_pipeline,
                                             self.end_tracking,
                                             self.end_saving,
                                             self.tracking_conn)
        # Initialize the saving process
        self.saving_process = PydraProcess(self.saving_constructor,
                                           self.exit_flag,
                                           self.start_pipeline,
                                           self.end_saving,
                                           self.pipeline_finished,
                                           self.saving_conn)

        self.protocol_process = PydraProcess(self.protocol_constructor,
                                             self.exit_flag,
                                             self.start_protcol,
                                             self.stop_protocol,
                                             self.protocol_finished, self.protocol_conn)
        # Start all processes
        self.protocol_process.start()

        self.acquisition_process.start()
        self.tracking_process.start()
        self.saving_process.start()
        print('All processes started.')

    def start(self):
        # Reset all flags
        self.pipeline_finished.clear()
        self.end_saving.clear()
        self.end_tracking.clear()
        self.end_acquisition.clear()
        # Start pipeline
        self.start_pipeline.set()
        print('Pipeline started.')

    def stop(self):
        self.start_pipeline.clear()
        self.end_acquisition.set()
        self.end_tracking.wait()
        print('Acquisition ended.')
        self.end_saving.wait()
        print('Tracking ended.')
        self.pipeline_finished.wait()
        print('Pipeline finished.')

    def exit(self):
        # Make sure processes exit the worker event loop
        if self.start_pipeline.is_set():
            self.stop()
        # Set the top-level exit signal telling all processes to end
        self.exit_flag.set()
        # Join all processes
        self.acquisition_process.join()
        print('Acquisition process ended.')
        # print(self.gui_queue.queue.qsize())
        self.tracking_process.join()
        print('Tracking process ended.')
        self.saving_process.join()
        print('Saving process ended.')

        self.protocol_process.join()
