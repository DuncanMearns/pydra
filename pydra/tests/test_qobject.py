from pydra import Pydra, config, ports


if __name__ == "__main__":
    Pydra.configure(config, ports)
    Pydra.run(gui=False, **config)
