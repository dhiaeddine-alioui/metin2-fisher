import threading
import time
from captcha_solver import CaptchaSolver
from utils import Point, Region, Offset
from mouse_controller import SerialMouseController
from video_capture import VideoCapture
from bait_handler import BaitHandler
from fish_detector import FishDetector
from gm_detector import GmDetector


class FishingBot(threading.Thread):
    def __init__(
        self,
        bot_number: int,
        mouse_controller: SerialMouseController,
        video_capturer: VideoCapture,
        ref_point: Point,
    ):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.bot_number = bot_number
        self.mouse_controller = mouse_controller
        self.ref_point = ref_point
        self.yellow_fish_region = Region(
            left=ref_point.x - 4, width=27, top=ref_point.y - 5, height=27
        )

        self.fishing_skill_point = self.ref_point + Offset(-50, 376)
        self.circle_region = Region(
            left=ref_point.x - 137, width=128, top=ref_point.y + 39, height=128
        )

        self.circle_radius = 64
        self.yellow_fish_color = (239, 165, 95)
        self.fish_detector = FishDetector(ref_point=ref_point)

        self.captcha_solver = CaptchaSolver(
            stop_event=self.stop_event, ref_point=ref_point
        )
        self.video_capturer = video_capturer
        self.bait_handler = BaitHandler(ref_point=ref_point)
        self.game_is_shown = False
        self.gm_detector = GmDetector(ref_point=ref_point)

    def run(self):
        while not self.stop_event.is_set():
            screen_shot = self.video_capturer.capture_screenshot()
            if not screen_shot: 
                continue
            
            if self.gm_detector.is_gm_connected(screen_shot):
                print('GM is connected ! Waiting for him to go offline ....')
                time.sleep(10)
                continue

            ########################## Chack captcha ####################
            if self.captcha_solver.is_captcha_detected(img=screen_shot):
                if captcha_attempts >= 5:
                    exit()

                captcha_attempts += 1
                points_to_click = self.captcha_solver.solve_captcha(
                    img=screen_shot
                )
                for ptoc in points_to_click:
                    self.mouse_controller.move_and_click_return(
                        point=ptoc,
                        lr="LEFT",
                        delay=500,
                        wait=True,
                        click_duration=500,
                    )
                    time.sleep(0.2)
                continue
            else:
                captcha_attempts = 0

            #################### Game is not shown #####################
            if not self.fish_detector.yellow_fish_exist(screen_shot):
                if self.game_is_shown:
                    time.sleep(2.8)
                self.game_is_shown = False
                bait_points = self.bait_handler.get_bait_points()
                for ptoc in bait_points:
                    self.mouse_controller.move_and_click_return(
                        point=ptoc,
                        lr="RIGHT",
                        delay=250,
                        wait=True,
                    )
                    time.sleep(0.3)
                self.mouse_controller.move_and_click_return(
                    point=self.fishing_skill_point,
                    lr="RIGHT",
                    delay=200,
                    wait=True,
                )
                time.sleep(1)
                continue

            #################### Game is shown #####################
            self.game_is_shown = True
            if self.fish_detector.red_circle_exist(screen_shot):
                fish_point = self.fish_detector.get_fish_coordinates(
                    screen_shot
                )
                if fish_point:
                    print(f"Fish Coordinates : {fish_point}")
                    self.mouse_controller.move_and_click_return(
                        point=fish_point, delay=40, wait=False
                    )
                    time.sleep(0.5)

            time.sleep(1 / 60)

    def stop(self):
        self.stop_event.set()
        print("Stopping the Fishing Bot Thread ...")
