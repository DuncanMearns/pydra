from pydra import Pydra, ports, config
from pydra.core import Worker
from pydra.utilities.string_formatting import format_zmq_connections
import numpy as np

# Name each worker
names = [f"worker{i}" for i in range(4)]

# Generate connectivity matrix for workers
connectivity = np.array([[0, 0, 0, 1],
                         [1, 0, 0, 0],
                         [1, 1, 0, 0],
                         [1, 1, 1, 0]])

# Create subscriptions
subscriptions = []
for subs in connectivity:
    subscriptions.append([names[i] for i in np.where(subs)[0]])

# Create workers
workers = []
for name, subs in zip(names, subscriptions):
    workers.append(type(name, (Worker,), dict(name=name, subscriptions=subs)))

# Create modules
config["modules"] = [dict(worker=worker, params={}) for worker in workers]


if __name__ == "__main__":
    config = Pydra.configure(config, ports, manual=True)
    print(format_zmq_connections(config["connections"]))
