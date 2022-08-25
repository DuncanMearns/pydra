import time
import zmq
from threading import Thread


def server_thread():
    context = zmq.Context.instance()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b"")
    socket.connect("tcp://localhost:5555")
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    count = 0
    while count < 10:
        events = dict(poller.poll())
        for sock in events:
            while sock.poll(0):
                message = sock.recv()
                print(message)
                count += 1
        time.sleep(1.)


def client_thread():
    context = zmq.Context.instance()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")
    for i in range(10):
        socket.send_string(str(i))
        time.sleep(0.01)


def main():
    context = zmq.Context.instance()
    s_thread = Thread(target=server_thread)
    c_thread = Thread(target=client_thread)
    s_thread.start()
    c_thread.start()
    c_thread.join()
    s_thread.join()
    context.destroy()


if __name__ == "__main__":
    main()
