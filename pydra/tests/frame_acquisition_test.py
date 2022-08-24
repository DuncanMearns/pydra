from pydra import PydraApp


def main():
    from pydra.tests.configs.frame_acquisition import config
    PydraApp.run(config)


if __name__ == "__main__":
    main()
