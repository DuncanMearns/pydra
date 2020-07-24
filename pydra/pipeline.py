from .core import *
from multiprocessing import Event, Queue, Pipe


class Pipeline:
    """Handles multiprocessing of frame acquisition, tracking, saving and additional protocols."""

    def __init__(self,
                 acquisition: type,
                 acquisition_kwargs: dict,
                 tracking: type,
                 tracking_kwargs: dict,
                 saving: type,
                 saving_kwargs: dict,
                 protocol=None,
                 protocol_kwargs=None):

        # Flags
        self.exit_flag = Event()  # top-level exit signal for process
        self.start_acquisition = Event()  # enter event loop of acquisition, tracking and saving processes
        self.end_acquisition = Event()  # end the acquisition event loop
        self.end_tracking = Event()  # end the tracking event loop
        self.end_saving = Event()  # end the saving event loop
        self.finished = Event()  # set when saving process has ended

        # Queues
        self.frame_queue = Queue()  # queue filled by acquisition process and emptied by tracking process
        self.tracking_queue = Queue()  # queue filled by tracking porcess and emptied by saving process

        self.workers = {}

        # Acquisition
        self.acquisition_sender, self.acquisition_receiver = Pipe(duplex=True)
        acquisition_kwargs.update(q=self.frame_queue)
        if acquisition.receive_events:
            self.acquisition_event_sender, self.acquisition_event_receiver = Pipe(duplex=True)
            acquisition_kwargs.update(receiver=self.acquisition_event_receiver)
        self.acquisition_constructor = acquisition.make(**acquisition_kwargs)

        # Tracking
        self.tracking_sender, self.tracking_receiver = Pipe(duplex=True)
        tracking_kwargs.update(input_q=self.frame_queue, output_queue=self.tracking_queue)
        if tracking.receive_events:
            self.tracking_event_sender, self.tracking_event_receiver = Pipe(duplex=True)
            tracking_kwargs.update(receiver=self.tracking_event_receiver)
        if tracking.send_events:
            self.send_from_tracking, self.receive_from_tracking = Pipe(duplex=True)
            tracking_kwargs.update(sender=self.send_from_tracking)
        self.tracking_constructor = tracking.make(**tracking_kwargs)

        # Saving
        self.saving_sender, self.saving_receiver = Pipe(duplex=True)
        saving_kwargs.update(q=self.tracking_queue)
        if saving.receive_events:
            self.saving_event_sender, self.saving_event_receiver = Pipe(duplex=True)
            saving_kwargs.update(receiver=self.saving_event_receiver)
        self.saving_constructor = saving.make(**saving_kwargs)

        # Protocol
        self.protocol = False
        if protocol:
            self.protocol = True
            # Additional flags
            self.start_protocol = Event()
            self.stop_protocol = Event()
            self.protocol_finished = Event()
            # Protocol
            self.protocol_sender, self.protocol_receiver = Pipe(duplex=True)
            if protocol.send_events:
                protocol_kwargs.update(sender=self.saving_event_sender)
            if protocol.receive_events:
                self.protocol_event_sender, self.protocol_event_receiver = Pipe(duplex=True)
                protocol_kwargs.update(receiver=self.protocol_event_receiver)
            self.protocol_constructor = protocol.make(**protocol_kwargs)

    def start(self):
        # Initialize the acquisition process
        self.acquisition_process = PydraProcess(self.acquisition_constructor,
                                                self.exit_flag,
                                                self.start_acquisition,
                                                self.end_acquisition,
                                                self.end_tracking,
                                                self.acquisition_receiver)
        # Initialize the tracking process
        self.tracking_process = PydraProcess(self.tracking_constructor,
                                             self.exit_flag,
                                             self.start_acquisition,
                                             self.end_tracking,
                                             self.end_saving,
                                             self.tracking_receiver)
        # Initialize the saving process
        self.saving_process = PydraProcess(self.saving_constructor,
                                           self.exit_flag,
                                           self.start_acquisition,
                                           self.end_saving,
                                           self.finished,
                                           self.saving_receiver)

        if self.protocol:
            self.protocol_process = PydraProcess(self.protocol_constructor,
                                                 self.exit_flag,
                                                 self.start_protocol,
                                                 self.stop_protocol,
                                                 self.protocol_finished,
                                                 self.protocol_receiver)

        self.acquisition_process.start()
        self.tracking_process.start()
        self.saving_process.start()
        if self.protocol:
            self.protocol_process.start()
        print('All processes started.')

    def start_event_loop(self):
        # Reset all flags
        self.finished.clear()
        self.end_saving.clear()
        self.end_tracking.clear()
        self.end_acquisition.clear()
        # Start event loop
        self.start_acquisition.set()
        print('Event loop started.')

    def stop_event_loop(self):
        self.start_acquisition.clear()
        self.end_acquisition.set()
        self.end_tracking.wait()
        print('Acquisition ended.')
        self.end_saving.wait()
        print('Tracking ended.')
        self.finished.wait()
        print('Event loop finished.')

    def start_protocol_event_loop(self):
        if self.protocol:
            # Reset flags
            self.protocol_finished.clear()
            self.stop_protocol.clear()
            # Start event loop
            self.start_protocol.set()
            print('Protocol event loop started.')

    def stop_protocol_event_loop(self):
        if self.protocol:
            self.start_protocol.clear()
            self.stop_protocol.set()
            self.protocol_finished.wait()
            print('Protocol event loop finished')

    def exit(self):
        # End protocol
        if self.protocol:
            self.stop_protocol_event_loop()
        # Make sure processes exit the worker event loop
        if self.start_acquisition.is_set():
            self.stop_event_loop()
        # Set the top-level exit signal telling all processes to end
        self.exit_flag.set()
        # Join all processes
        if self.protocol:
            self.protocol_process.join()
            print('Protocol process ended.')
        self.acquisition_process.join()
        print('Acquisition process ended.')
        # print(self.gui_queue.queue.qsize())
        self.tracking_process.join()
        print('Tracking process ended.')
        self.saving_process.join()
        print('Saving process ended.')
