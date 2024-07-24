from utils import Point, Offset, UserImage, Color


class GmDetector:
    GM_STATUS_PIXEL = Offset(1235 - 1094, 670 - 624)
    CONNECTED_COLOR = Color(R=121, G=171, B=25)

    def __init__(self, ref_point: Point):
        self.ref_point = ref_point
        self.gm_status_point = ref_point + GmDetector.GM_STATUS_PIXEL

    def is_gm_connected(self, image: UserImage):
        pixel_color = image.get_pixel_color(point=self.gm_status_point)
        return pixel_color.is_close_to(
            GmDetector.CONNECTED_COLOR, percentage=10
        )
