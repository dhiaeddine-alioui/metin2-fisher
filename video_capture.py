import time
import cv2
from PIL import Image, ImageChops
from utils import Region, UserImage
import threading


class VideoCapture(threading.Thread):
    def __init__(self, device_index=1, width=1920, height=1080):
        self.device_index = device_index
        self.width = width
        self.height = height
        self.capture = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()

        if not self.capture.isOpened():
            raise Exception("Error: Could not open video capture device.")

        # Set the desired resolution
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Verify the resolution
        actual_width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Resolution set to: {int(actual_width)} x {int(actual_height)}")

        # Allow the camera to warm up and clear the buffer
        time.sleep(1)  # Wait for 2 seconds
        for _ in range(5):
            self.capture.read()

        self.last_screenshot: UserImage = None
        self.lock = threading.Lock()

    def _capture(self):
        start = time.monotonic()
        while True:
            ret, frame = self.capture.read()
            end = time.monotonic()
            if end - start > 0.010:
                break
            time.sleep(0.005)

        if ret:
            # Convert the OpenCV image (BGR) to a PIL image (RGB)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            # print(f"Screenshot captured in {time.monotonic()-start}s.")

            self.last_screenshot = UserImage.from_pil_image(pil_image)

    def capture_screenshot(
        self, region: Region = None, use_cache=False
    ) -> UserImage:
        if not self.lock.acquire(timeout=1 / 120):
            return None
        try:
            if region is not None:
                return self.last_screenshot.region_crop(region)
            return self.last_screenshot
        finally:
            self.lock.release()

    def save_last_screenshot_as_png(self, filename="last_screenshot.png"):
        if self.last_screenshot:
            self.last_screenshot.save(filename, format="PNG")
            print(f"Last screenshot saved as {filename}")
        else:
            print("Error: No screenshot captured yet.")

    def release(self):
        self.capture.release()

    def run(self):
        while not self.stop_event.is_set():
            self._capture()
            time.sleep(1 / 60)

    def stop(self):
        self.stop_event.set()
        print("Stopping the Video Capture Thread ...")
