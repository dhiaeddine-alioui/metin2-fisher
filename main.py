import time
import threading
import cv2
import numpy as np
from typing import List
from PIL import Image
from mouse_controller import SerialMouseController
from video_capture import VideoCapture
from utils import Region, Point
from fishing_bot import FishingBot

resolution_x = 1920
resolution_y = 1080


def find_template_matches(
    large_image: Image.Image, template_image_path: str, threshold: float = 0.8
) -> List[Point]:
    template = cv2.imread(template_image_path)
    if template is None:
        raise FileNotFoundError(
            "The template image path is incorrect or the image cannot be loaded."
        )
    large_image = cv2.cvtColor(np.array(large_image), cv2.COLOR_RGB2BGR)

    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    large_image_gray = cv2.cvtColor(large_image, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(
        large_image_gray, template_gray, cv2.TM_CCOEFF_NORMED
    )
    locations = np.where(result >= threshold)
    coordinates = list(zip(*locations[::-1]))

    return [Point(x, y) for x, y in coordinates]


if __name__ == "__main__":
    try:
        video_capturer = VideoCapture(device_index=0)
        video_capturer.start()
        time.sleep(0.5)

        mouse_controller = SerialMouseController(
            port="COM7",
            baudrate=115200,
            res_x=resolution_x,
            res_y=resolution_y,
        )
        mouse_controller.initialize_position()

        full_screen_region = Region(
            left=0, width=resolution_x, top=0, height=resolution_y
        )

        img = video_capturer.capture_screenshot()

        yellow_fishs_coordinates: List[Point] = find_template_matches(
            large_image=img,
            template_image_path="resources/yellow_fish.png",
        )
        fishing_bots: List[FishingBot] = []

        if yellow_fishs_coordinates:
            print(
                f"Creating {len(yellow_fishs_coordinates)} Finshing bots : {[str(item) for item in yellow_fishs_coordinates]}"
            )
            for idx, coordinates in enumerate(yellow_fishs_coordinates):
                fishing_bots.append(
                    FishingBot(
                        bot_number=idx,
                        mouse_controller=mouse_controller,
                        video_capturer=video_capturer,
                        ref_point=coordinates,
                    )
                )
        else:
            print("No fishing bot to create !")
            video_capturer.stop()
            exit()

        for fishing_bot in fishing_bots:
            fishing_bot.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        video_capturer.stop()
        for fishing_bot in fishing_bots:
            fishing_bot.stop()

        video_capturer.join()
        for fishing_bot in fishing_bots:
            fishing_bot.join()
