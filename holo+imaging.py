from pydra import PydraApp, Configuration
from pydra_modules.cameras.ximea_camera import XimeaModule
from pydra_modules.optogenetics import OPTOGENETICS


XIMEA = XimeaModule.new("light_sheet")


config = Configuration(modules=[XIMEA, OPTOGENETICS])


if __name__ == "__main__":
    PydraApp.run(config)
