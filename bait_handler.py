from utils import Point, Offset
from typing import List


class BaitHandler:
    bait_offsets = [
        Offset(1, 375),
        Offset(34, 375),
        Offset(65, 375),
        Offset(98, 375),
        Offset(-76, 375),
        Offset(-108, 375),
    ]
    shrimp_offset = Offset(-140, 375)

    def __init__(self, ref_point: Point):
        self.ref_point = ref_point
        self.used_bait = 0

    def get_bait_points(self) -> List[Point]:
        output = []
        selected_bait = min(self.used_bait // 500, len(self.bait_offsets) - 1)
        output.append(self.ref_point + self.bait_offsets[selected_bait])

        if self.used_bait % 20 == 0:
            output.append(self.ref_point + self.shrimp_offset)

        self.used_bait += 1
        return output
