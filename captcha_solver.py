from twocaptcha import TwoCaptcha
from PIL import Image
from typing import List
import requests
from datetime import datetime
from utils import Offset, Point, Region, UserImage


class CaptchaSolver:
    BUTTON_MAP = {
        0: Offset(7, 226),
        1: Offset(-38, 154),
        2: Offset(7, 154),
        3: Offset(52, 154),
        4: Offset(-38, 179),
        5: Offset(7, 179),
        6: Offset(52, 179),
        7: Offset(-38, 204),
        8: Offset(7, 204),
        9: Offset(52, 204),
        "enter": Offset(7, 250),
    }

    def __init__(self, stop_event, ref_point: Point):
        self.ref_point = ref_point
        self.solver = TwoCaptcha("c580c441b1a4562530582766ac6a1221")
        self.captcha_image_region = Region(
            left=self.ref_point.x - 58,
            width=84,
            top=self.ref_point.y + 106,
            height=33,
        )
        self.black_input_region = Region(
            left=self.ref_point.x + 33,
            width=35,
            top=self.ref_point.y + 112,
            height=13,
        )
        self.stop_event = stop_event

    def notify_solved_captcha(self, captcha_solution):
        requests.get(
            f"https://pushnotify.co.uk/send/?userid=aliouidhia&code=596422&txt=Solved captcha : {captcha_solution}"
        )

    def is_captcha_detected(self, img: UserImage) -> bool:
        cropped_region = img.region_crop(self.black_input_region)

        for pixel in cropped_region.getdata():
            if pixel != (0, 0, 0):
                return False
        print("Captcha detected !")
        return True

    def solve_captcha(self, img: Image) -> List[Point]:
        cropped_captcha_image = img.region_crop(self.captcha_image_region)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        captcha_file_name = f"captchas/captcha_image_{self.ref_point.x}_{self.ref_point.y}_{timestamp}.png"
        cropped_captcha_image.save(captcha_file_name, format="PNG")

        while not self.stop_event.is_set():
            result = self.solver.normal(
                captcha_file_name,
                numeric=1,
                minLen=3,
                maxLen=3,
                hintText="Only numbers",
            )
            print(f"Received captcha solution : {result}")
            code = result["code"]
            captcha_id = result["captchaId"]

            if not len(code) == 3 or not code.isdigit():
                self.solver.report(captcha_id, False)
                continue

            coor_to_click = [
                self.ref_point + CaptchaSolver.BUTTON_MAP[int(str_num)]
                for str_num in code
            ] + [self.ref_point +CaptchaSolver.BUTTON_MAP["enter"]]
            self.notify_solved_captcha(captcha_solution=code)
            print(
                f"Captcha points to click : {[str(p) for p in coor_to_click]}"
            )
            return coor_to_click
