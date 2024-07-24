import math
from PIL import Image, ImageChops


class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Point({self.x}, {self.y})"

    def __eq__(self, other):
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y
        return False

    def distance_to(self, other):
        """Calculate the distance to another Point."""
        if isinstance(other, Point):
            return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
        raise ValueError("The other object must be a Point")

    def __add__(self, offset):
        """Add an Offset to the Point."""
        if isinstance(offset, Offset):
            return Point(self.x + offset.x, self.y + offset.y)
        raise ValueError("The offset must be an instance of Offset")


class Offset:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Offset({self.x}, {self.y})"

    def __eq__(self, other):
        if isinstance(other, Offset):
            return self.x == other.x and self.y == other.y
        return False

    def scale(self, factor: float):
        """Scale the offset by a given factor."""
        return Offset(self.x * factor, self.y * factor)


class Region:
    def __init__(self, left: int, width: int, top: int, height: int):
        self.left = left
        self.width = width
        self.right = left + width
        self.top = top
        self.height = height
        self.bottom = top + height
        # Corners
        self.top_left_pixel = Point(self.left + 1, self.top + 1)
        self.top_right_pixel = Point(self.right - 1, self.top + 1)
        self.bottom_left_pixel = Point(self.left + 1, self.bottom - 1)
        self.bottom_right_pixel = Point(self.right - 1, self.bottom - 1)
        # Middle Edges
        self.top_middle = Point((self.left + self.right) // 2, self.top)
        self.bottom_middle = Point((self.left + self.right) // 2, self.bottom)
        self.left_middle = Point(self.left, (self.top + self.bottom) // 2)
        self.right_middle = Point(self.right, (self.top + self.bottom) // 2)

    def __str__(self):
        return (
            f"Region(left: {self.left}, top: {self.top}, "
            f"width: {self.width}, height: {self.height})"
        )

    def contains_point(self, point: Point) -> bool:
        """Check if a point is within the region."""
        return (
            self.left <= point.x <= self.right
            and self.top <= point.y <= self.bottom
        )

    def overlaps_with(self, other: "Region") -> bool:
        """Check if this region overlaps with another region."""
        return not (
            self.right < other.left
            or self.left > other.right
            or self.bottom < other.top
            or self.top > other.bottom
        )

    def center(self) -> Point:
        """Get the center point of the region."""
        return Point(
            (self.left + self.right) // 2, (self.top + self.bottom) // 2
        )

    def area(self) -> int:
        """Calculate the area of the region."""
        return self.width * self.height


class Color:
    def __init__(self, R: int, G: int, B: int):
        self.R = self._validate_value(R)
        self.G = self._validate_value(G)
        self.B = self._validate_value(B)

    def _validate_value(self, value: int) -> int:
        """Ensure the RGB value is within the range 0 to 255."""
        if 0 <= value <= 255:
            return value
        raise ValueError("RGB values must be between 0 and 255")

    def __str__(self):
        return f"Color(R: {self.R}, G: {self.G}, B: {self.B})"

    def __eq__(self, other):
        if isinstance(other, Color):
            return (
                self.R == other.R and self.G == other.G and self.B == other.B
            )
        return False

    def is_close_to(self, other: "Color", percentage: float) -> bool:
        """Check if this color is close to another color within a given percentage."""
        # print(f"Comparing colors : {self} vs {other}")
        if not isinstance(other, Color):
            raise ValueError("The other color must be an instance of Color")

        diff_r = abs(self.R - other.R) / 255 * 100
        diff_g = abs(self.G - other.G) / 255 * 100
        diff_b = abs(self.B - other.B) / 255 * 100

        average_diff = (diff_r + diff_g + diff_b) / 3
        return average_diff <= percentage


class UserImage(Image.Image):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def images_are_different(image1: Image.Image, image2: Image.Image) -> bool:
        if image1.size != image2.size:
            return True

        diff = ImageChops.difference(image1, image2)
        return diff.getbbox() is not None

    @classmethod
    def from_pil_image(cls, pil_image):
        # This method allows creating a UserImage from a PIL.Image
        user_image = cls.__new__(cls)
        user_image.__dict__ = pil_image.__dict__.copy()
        return user_image

    def region_crop(self, region: Region) -> "UserImage":
        try:
            cropped_image = self.crop(
                (region.left, region.top, region.right, region.bottom)
            )
            user_image = UserImage.__new__(UserImage)
            user_image.__dict__ = cropped_image.__dict__.copy()
            return user_image
        except Exception as e:
            print(f"An error occurred while cropping: {e}")
            raise

    def get_pixel_color(self, point: Point) -> Color:
        try:
            pixel = self.getpixel((point.x, point.y))
            return Color(R=pixel[0], G=pixel[1], B=pixel[2])
        except IndexError:
            print(f"Point {point} is out of bounds.")
            raise

    def save_image(self, file_path: str = "tmp.png") -> None:
        try:
            super().save(file_path, format="PNG")
        except IOError as e:
            print(f"An error occurred while saving the image: {e}")
            raise
