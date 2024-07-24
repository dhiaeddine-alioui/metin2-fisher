from utils import UserImage
from utils import Color, Point, Region, Offset
import cv2
import numpy as np
import time


class FishDetector:
    def __init__(
        self,
        ref_point: Point,
    ):
        self.yellow_fish_color = Color(R=239, G=165, B=95)
        self.yellow_fish_point = ref_point + Offset(10, 8)
        self.circle_region = Region(
            left=ref_point.x - 134,
            width=128,
            top=ref_point.y + 39,
            height=128,
        )

    def yellow_fish_exist(self, image: UserImage, tolerance: int = 10) -> bool:
        pixel_color = image.get_pixel_color(self.yellow_fish_point)

        return pixel_color.is_close_to(
            self.yellow_fish_color, percentage=tolerance
        )

    def red_circle_exist(self, image: UserImage) -> bool:
        image.region_crop(region=self.circle_region).save_image()
        points_to_check = [
            self.circle_region.top_middle,
            self.circle_region.left_middle,
            self.circle_region.bottom_middle,
            self.circle_region.right_middle,
        ]

        count = 0
        for ptoc in points_to_check:
            color = image.get_pixel_color(ptoc)
            if color.R > 140 and color.G < 120 and color.B < 120:
                count += 1

        return count >= 2

    def get_fish_coordinates(self, image: UserImage) -> Point:
        start = time.monotonic()
        cropped_region = image.region_crop(self.circle_region)
        _, _, b = cv2.split(np.array(cropped_region))
        _, thresholded_blue = cv2.threshold(b, 100, 255, cv2.THRESH_BINARY)
        mask = np.zeros(
            (self.circle_region.height, self.circle_region.width),
            dtype=np.uint8,
        )
        center = (
            self.circle_region.width // 2,
            self.circle_region.height // 2,
        )
        radius = 57
        color = 255  # White color
        thickness = -1  # Fill the circle
        cv2.circle(mask, center, radius, color, thickness)
        mask = cv2.bitwise_not(mask)
        result = cv2.bitwise_or(thresholded_blue, mask)
        contours, _ = cv2.findContours(
            result, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = sorted(contours, key=lambda x: len(x), reverse=True)
        if len(contours) > 1:
            M = cv2.moments(contours[0])
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                print(
                    f"Fish corrdinate compute time = {time.monotonic()-start}s"
                )
                return self.circle_region.top_left_pixel + Offset(cx, cy)
        return None

    # def is_inside_circle(self, point: Point) -> bool:
    #     distance_squared = (x - self.left - (self.width / 2)) ** 2 + (
    #         y - self.top - (self.height / 2)
    #     ) ** 2
    #     return distance_squared <= r**2
