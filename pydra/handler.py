from .core import *
# from .saving import NoSaver
from multiprocessing import Event, Queue, Pipe
import queue


class Handler:
    """Handles multiprocessing of frame acquisition, tracking, saving and protocol."""

    def __init__(self, acquisition: tuple, tracking: tuple, saving: tuple, protocol: tuple):

        self.acquisition_name, acquisition_type, acquisition_kwargs = acquisition
        self.tracking_name, tracking_type, tracking_kwargs = tracking
        self.saving_name, saving_type, saving_kwargs = saving
        self.protocol_name, protocol_type, protocol_kwargs = protocol

        # Flags
        self.exitFlag = Event()  # top-level exit signal for process
        self.startAcquisitionFlag = Event()  # enter event loop of acquisition, tracking and saving processes
        self.endAcquisitionFlag = Event()  # end the acquisition event loop
        self.endTrackingFlag = Event()  # end the tracking event loop
        self.endSavingFlag = Event()  # end the saving event loop
        self.acquisitionFinishedFlag = Event()  # set when saving process has ended
        self.startProtocolFlag = Event()  # enter the protocol event loop
        self.endProtocolFlag = Event()  # end the protocol event loop
        self.protocolFinishedFlag = Event()  # set when the protocol event loop has ended

        # Queues
        self.frameQueue = Queue()  # queue filled by acquisition process and emptied by tracking process
        self.trackingQueue = Queue()  # queue filled by tracking process and emptied by saving process
        self.protocolQueue = Queue()  # queue filled by protocol process and emptied by saving process

        # Process connections
        self.acquisitionProcessReceiver, self.acquisitionProcessSender = Pipe(duplex=True)
        self.trackingProcessReceiver, self.trackingProcessSender = Pipe(duplex=True)
        self.savingProcessReceiver, self.savingProcessSender = Pipe(duplex=True)
        self.protocolProcessReceiver, self.protocolProcessSender = Pipe(duplex=True)

        # Process handles
        self.process_handles = {}
        self.process_handles[self.acquisition_name] = self.acquisitionProcessSender
        self.process_handles[self.tracking_name] = self.trackingProcessSender
        self.process_handles[self.saving_name] = self.savingProcessSender
        self.process_handles[self.protocol_name] = self.protocolProcessSender

        # Event handles
        self.event_handles = {}
        # Acquisition
        self.acquisitionEventReceiver, self.acquisitionEventSender = Pipe(duplex=False)
        self.queueEventsAcquisition = Queue()
        self.event_handles[self.acquisition_name] = dict(send=self.acquisitionEventSender,
                                                         receive=self.queueEventsAcquisition)
        # Tracking
        self.trackingEventReceiver, self.trackingEventSender = Pipe(duplex=False)
        self.queueEventsTracking = Queue()
        self.event_handles[self.tracking_name] = dict(send=self.trackingEventSender,
                                                      receive=self.queueEventsTracking)
        # Saving
        self.savingEventReceiver, self.savingEventSender = Pipe(duplex=False)
        self.queueEventsSaving = Queue()
        self.event_handles[self.saving_name] = dict(send=self.savingEventSender,
                                                    receive=self.queueEventsSaving)
        # Protocol
        self.protocolEventReceiver, self.protocolEventSender = Pipe(duplex=False)
        self.queueEventsProtocol = Queue()
        self.event_handles[self.protocol_name] = dict(send=self.protocolEventSender,
                                                      receive=self.queueEventsProtocol)

        # Handling kwargs
        self.acquisitionHandlingKwargs = dict(q=self.frameQueue,
                                              receiver=self.acquisitionEventReceiver,
                                              sender=self.queueEventsAcquisition)
        self.trackingHandlingKwargs = dict(input_q=self.frameQueue,
                                           output_q=self.trackingQueue,
                                           receiver=self.trackingEventReceiver,
                                           sender=self.queueEventsTracking)
        self.savingHandlingKwargs = dict(tracking_q=self.trackingQueue,
                                         protocol_q=self.protocolQueue,
                                         receiver=self.savingEventReceiver,
                                         sender=self.queueEventsSaving)
        self.protocolHandlingKwargs = dict(q=self.protocolQueue,
                                           receiver=self.protocolEventReceiver,
                                           sender=self.queueEventsProtocol)
        acquisition_kwargs.update(self.acquisitionHandlingKwargs)
        tracking_kwargs.update(self.trackingHandlingKwargs)
        saving_kwargs.update(self.savingHandlingKwargs)
        protocol_kwargs.update(self.protocolHandlingKwargs)

        # Constructors
        self.AcquisitionConstructor = acquisition_type.make(**acquisition_kwargs)
        self.TrackingConstructor = tracking_type.make(**tracking_kwargs)
        self.SavingConstructor = saving_type.make(**saving_kwargs)
        self.ProtocolConstructor = protocol_type.make(**protocol_kwargs)

    def set_saving(self, val: bool):
        return self.set_param(self.saving_name, (('saving_on', val),))

    def set_param(self, target, args):
        if not self.exitFlag.is_set():  # check that processes have not already ended
            self.process_handles[target].send(args)
            ret = self.process_handles[target].recv()
            return ret

    def send_event(self, target, event, args):
        self.event_handles[target]['send'].send((event, args))

    def receive_event(self, target, wait=0.01, block=False):
        if block:
            out = self.event_handles[target]['receive'].get(block=block)
            ret = True
        else:
            try:
                out = self.event_handles[target]['receive'].get(timeout=wait)
                ret = True
            except queue.Empty:
                out = None
                ret = False
        return ret, out

    def flush_events(self, target):
        while True:
            ret, out = self.receive_event(target)
            if not ret:
                break

    def start(self):
        # Initialize the acquisition process
        self._AcquisitionProcess = PydraProcess(self.AcquisitionConstructor,
                                                self.exitFlag,
                                                self.startAcquisitionFlag,
                                                self.endAcquisitionFlag,
                                                self.endTrackingFlag,
                                                self.acquisitionProcessReceiver,
                                                name=self.acquisition_name)
        # Initialize the tracking process
        self._TrackingProcess = PydraProcess(self.TrackingConstructor,
                                             self.exitFlag,
                                             self.startAcquisitionFlag,
                                             self.endTrackingFlag,
                                             self.endSavingFlag,
                                             self.trackingProcessReceiver,
                                             name=self.tracking_name)
        # Initialize the saving process
        self._SavingProcess = PydraProcess(self.SavingConstructor,
                                           self.exitFlag,
                                           self.startAcquisitionFlag,
                                           self.endSavingFlag,
                                           self.acquisitionFinishedFlag,
                                           self.savingProcessReceiver,
                                           name=self.saving_name)

        self._ProtocolProcess = PydraProcess(self.ProtocolConstructor,
                                             self.exitFlag,
                                             self.startProtocolFlag,
                                             self.endProtocolFlag,
                                             self.protocolFinishedFlag,
                                             self.protocolProcessReceiver,
                                             name=self.protocol_name)

        self._AcquisitionProcess.start()
        self._TrackingProcess.start()
        self._SavingProcess.start()
        self._ProtocolProcess.start()
        print('All processes started.\n')

    def start_event_loop(self):
        # Reset all flags
        self.acquisitionFinishedFlag.clear()
        self.endSavingFlag.clear()
        self.endTrackingFlag.clear()
        self.endAcquisitionFlag.clear()
        # Start event loop
        self.startAcquisitionFlag.set()
        # print('Event loop started.')

    def stop_event_loop(self):
        # Clear the start acquisition flag to prevent immediate re-entry into event loop
        self.startAcquisitionFlag.clear()
        # End the acquisition and wait for processes to exit their event loops
        self.endAcquisitionFlag.set()
        self.endTrackingFlag.wait()
        # print('Acquisition ended.')
        self.endSavingFlag.wait()
        # print('Tracking ended.')
        self.acquisitionFinishedFlag.wait()
        # print('Event loop finished.')
        # Flush events from queue
        for target in (self.acquisition_name, self.tracking_name, self.saving_name):
            self.flush_events(target)

    def start_protocol_event_loop(self):
        # Reset flags
        self.protocolFinishedFlag.clear()
        self.endProtocolFlag.clear()
        # Start event loop
        self.startProtocolFlag.set()
        # print('Protocol event loop started.')

    def stop_protocol_event_loop(self):
        self.startProtocolFlag.clear()
        self.endProtocolFlag.set()
        self.protocolFinishedFlag.wait()
        # print('Protocol event loop finished')
        self.flush_events(self.protocol_name)

    def exit(self):
        # Make sure processes exit the worker event loop
        if self.startProtocolFlag.is_set():
            self.stop_protocol_event_loop()
        if self.startAcquisitionFlag.is_set():
            self.stop_event_loop()
        # Set the top-level exit signal telling all processes to end
        self.exitFlag.set()
        # Join all processes
        self._ProtocolProcess.join()
        print('Protocol process ended.')
        self._AcquisitionProcess.join()
        print('Acquisition process ended.')
        self._TrackingProcess.join()
        print('Tracking process ended.')
        self._SavingProcess.join()
        print('All processes joined.')
