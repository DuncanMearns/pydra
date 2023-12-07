from pydra import *
from pydra_modules.cameras.flir_camera import FlirModule


FLIR = FlirModule.new("flir",
                      camera_params=dict(camera_id=0,
                                         frame_size=(1200, 1600),
                                         frame_rate=40,
                                         exposure=2000))

# Add modules to config
config = Configuration(modules=[FLIR])

if __name__ == "__main__":
    PydraApp.run(config)
