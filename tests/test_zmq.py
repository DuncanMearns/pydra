import time
import zmq
from threading import Thread


def server_thread():
    context = zmq.Context.instance()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    while True:
        message = socket.recv()
        print('Reiceived request: %s' % message)
        time.sleep(1)
        socket.send(b"World")


def client_thread():
    context = zmq.Context.instance()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")
    for request in range(10):
        socket.send(b"Hello")
        message = socket.recv()
        print('Reiceived reply: %s' % message)


def main():
    context = zmq.Context.instance()
    s_thread = Thread(target=server_thread)
    c_thread = Thread(target=client_thread)
    s_thread.start()
    c_thread.start()


if __name__ == "__main__":
    main()
