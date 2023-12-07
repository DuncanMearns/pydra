from simple_pyspin import Camera

cam = Camera() # Acquire Camera
cam.init() # Initialize camera

cam.start() # Start recording
imgs = [cam.get_array() for n in range(10)] # Get 10 frames
cam.stop() # Stop recording

cam.close() # You should explicitly clean up

print(imgs[0].shape, imgs[0].dtype) # Each image is a numpy array!
