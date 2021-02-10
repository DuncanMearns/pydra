ports = [
    ("tcp://*:5555", "tcp://localhost:5555"),
    ("tcp://*:5556", "tcp://localhost:5556"),
    ("tcp://*:5557", "tcp://localhost:5557"),
    ("tcp://*:5558", "tcp://localhost:5558"),
    ("tcp://*:5559", "tcp://localhost:5559")
]


config = {

    "connections": {

        "pydra": {
            "publisher": "tcp://*:6000",
            "receiver": "tcp://localhost:6001",
            "port": "tcp://localhost:6000"
        },

        "saver": {
            "sender": "tcp://*:6001",
            "subscriptions": []
        },

    },

    "modules": [],

    "trigger": None

}
