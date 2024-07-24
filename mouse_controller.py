import threading
import time
import serial
from utils import Point


class SerialMouseController:
    def __init__(self, port: str, baudrate: int, res_x: int, res_y: int):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.res_x = res_x
        self.res_y = res_y
        self.init_point = Point(res_x / 2, res_y / 2)
        self.lock = threading.Lock()

    def send_command(self, command: str, wait=False):
        try:
            if wait:
                with self.lock:
                    self.ser.write((command + "\n").encode())
                    response = self.ser.readline().decode().strip()
                    print(response)  # Print response for debugging
            else:
                if not self.lock.acquire(timeout=1 / 120):
                    print("Could not acquire lock!")
                    return
                try:
                    self.ser.write((command + "\n").encode())
                    response = self.ser.readline().decode().strip()
                    print(response)  # Print response for debugging
                finally:
                    self.lock.release()
        except serial.serialutil.SerialException:
            pass

    def move_and_click(self, point: Point, lr: str = "LEFT", wait=False):
        command = f"MOVECLICK {int(point.x - self.init_point.x)} {int(point.y - self.init_point.y)} {lr}"
        self.send_command(command, wait)

    def move_and_click_return(
        self,
        point: Point,
        lr: str = "LEFT",
        delay: int = 20,
        wait=False,
        click_duration: int = 10,
    ):
        command = f"MOVECLICKMOVE {int(point.x - self.init_point.x)} {int(point.y - self.init_point.y)} {lr} {delay} {click_duration}"
        self.send_command(command, wait)

    def move(self, point: Point, wait=False):
        command = f"MOVE {int(point.x - self.init_point.x)} {int(point.y - self.init_point.y)}"
        self.send_command(command, wait)

    def click(self, lr: str = "LEFT", wait=False):
        command = f"CLICK {lr}"
        self.send_command(command, wait)

    def initialize_position(self):
        with self.lock:
            command = f"MOVE {int(-self.res_x)} {int(-self.res_y)}"
            self.ser.write((command + "\n").encode())
            response = self.ser.readline().decode().strip()
            print(response)  # Print response for debugging
            time.sleep(0.2)
            command = f"MOVE {int(self.init_point.x)} {int(self.init_point.y)}"
            self.ser.write((command + "\n").encode())
            response = self.ser.readline().decode().strip()
            print(response)  # Print response for debugging

    def close(self):
        self.ser.close()


if __name__ == "__main__":
    mouse_controller = SerialMouseController(
        port="COM7",
        baudrate=115200,
        res_x=1920,
        res_y=1080,
    )

    mouse_controller.move_and_click_return(
        Point(500, 500), lr="RIGHT", delay=500, wait=True, click_duration=10
    )
