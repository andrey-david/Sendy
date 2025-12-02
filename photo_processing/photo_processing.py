"""Photo Processing

This module provides a complete workflow for processing photos intended for print production (canvas, matte, or banner).
It performs cropping, edge stretching, frame creation (wide white and black line), numbering,
and saving with precise DPI and ICC profile settings.

Main parts:
------------
- PhotoProc: main class that manages the full image processing pipeline.
  - presets(): initializes image parameters (size, material, coordinates, etc.).
  - stretch(): extends image edges for gallery wrap effect.
  - white_frame(): adds white margins to reach the target print size.
  - black_frame(): draws a black outline border around the final image.
  - add_number(): overlays order or print number on the top and bottom edges.
  - save_image(): saves the final image with ICC profile and unique filename.
  - process_image(): executes the complete processing pipeline and returns the saved file path.
"""

import os
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from data import data

logger = logging.getLogger(__name__)


class PhotoProc:
    def __init__(self):
        self.image = None
        self.number: str = ''
        self.width_cm: int = 0
        self.height_cm: int = 0
        self.material: str = 'Холст'
        self.coordinates: tuple[int, int, int, int] = (0, 0, 0, 0)

        self.wrap_cm: float = data.photo_processing_wrap_cm
        self.white_cm: float = data.photo_processing_white_cm
        self.black_px: int = data.photo_processing_black_px
        self.text_px: int = data.photo_processing_font_size_px
        self.crop_px: int = data.photo_processing_crop_px
        self.font_path: str = "arial.ttf"
        self.dpi: int = data.photo_processing_dpi
        self.icc: bytes | None = None

        self.CM_TO_INCH: float = 2.54
        self.cm_to_px = lambda cm: int((cm * self.dpi) / self.CM_TO_INCH)

        self.filepath = None

    def presets(
            self,
            image,
            number='',
            width_cm=0,
            height_cm=0,
            material='Холст',
            coordinates=None
    ):
        self.image = image
        self.icc = self.image.info.get("icc_profile")
        if self.icc is None:
            with open(r"C:\Windows\System32\spool\drivers\color\sRGB Color Space Profile.icm", "rb") as icc_profile:
                self.icc = icc_profile.read()
        image_width, image_height = self.image.size

        if coordinates:
            self.coordinates = coordinates
        else:
            self.coordinates: tuple[int, ...] = (self.crop_px,
                                                 self.crop_px,
                                                 image_width - self.crop_px,
                                                 image_height - self.crop_px
                                                 )

        self.number = number
        self.width_cm = width_cm
        self.height_cm = height_cm
        self.material = material

    def set_dpi(self, value):
        self.dpi = value

    def stretch(self):
        image_width, image_height = self.image.size
        wrap_px = self.cm_to_px(self.wrap_cm)
        strip_crop_px = 20
        corner_crop_px = 20

        def stretched_strip(crop_box, final_size):
            strip = self.image.crop(crop_box)
            return strip.resize(final_size, Image.LANCZOS)

        left_strip = stretched_strip((0, 0, strip_crop_px, image_height), (wrap_px, image_height))
        right_strip = stretched_strip((image_width - strip_crop_px, 0, image_width, image_height),
                                      (wrap_px, image_height))
        top_strip = stretched_strip((0, 0, image_width, strip_crop_px), (image_width, wrap_px))
        bottom_strip = stretched_strip((0, image_height - strip_crop_px, image_width, image_height),
                                       (image_width, wrap_px))

        left_wrap = left_strip.crop((wrap_px - wrap_px, 0, wrap_px, image_height)).transpose(Image.FLIP_LEFT_RIGHT)
        right_wrap = right_strip.crop((0, 0, wrap_px, image_height)).transpose(Image.FLIP_LEFT_RIGHT)
        top_wrap = top_strip.crop((0, wrap_px - wrap_px, image_width, wrap_px)).transpose(Image.FLIP_TOP_BOTTOM)
        bottom_wrap = bottom_strip.crop((0, 0, image_width, wrap_px)).transpose(Image.FLIP_TOP_BOTTOM)

        corner_top_left = self.image.crop((corner_crop_px, corner_crop_px, corner_crop_px * 2, corner_crop_px * 2))
        corner_top_right = self.image.crop(
            (image_width - corner_crop_px * 2, corner_crop_px, image_width - corner_crop_px, corner_crop_px * 2))
        corner_bottom_left = self.image.crop(
            (corner_crop_px, image_height - corner_crop_px * 2, corner_crop_px * 2, image_height - corner_crop_px))
        corner_bottom_right = self.image.crop(
            (image_width - corner_crop_px * 2, image_height - corner_crop_px * 2, image_width - corner_crop_px,
             image_height - corner_crop_px))

        corner_top_left = corner_top_left.resize((wrap_px, wrap_px)).crop((0, 0, wrap_px, wrap_px))
        corner_top_right = corner_top_right.resize((wrap_px, wrap_px)).crop((wrap_px - wrap_px, 0, wrap_px, wrap_px))
        corner_bottom_left = corner_bottom_left.resize((wrap_px, wrap_px)).crop(
            (0, wrap_px - wrap_px, wrap_px, wrap_px))
        corner_bottom_right = corner_bottom_right.resize((wrap_px, wrap_px)).crop(
            (wrap_px - wrap_px, wrap_px - wrap_px, wrap_px, wrap_px))

        new_image = Image.new("RGB", (image_width + 2 * wrap_px, image_height + 2 * wrap_px))

        new_image.paste(self.image, (wrap_px, wrap_px))
        new_image.paste(left_wrap, (0, wrap_px))
        new_image.paste(right_wrap, (image_width + wrap_px, wrap_px))
        new_image.paste(top_wrap, (wrap_px, 0))
        new_image.paste(bottom_wrap, (wrap_px, image_height + wrap_px))

        new_image.paste(corner_top_left, (0, 0))
        new_image.paste(corner_top_right, (image_width + wrap_px, 0))
        new_image.paste(corner_bottom_left, (0, image_height + wrap_px))
        new_image.paste(corner_bottom_right, (image_width + wrap_px, image_height + wrap_px))

        self.image = new_image

    def white_frame(self):
        white_px = self.cm_to_px(self.white_cm)
        image_width, image_height = self.image.size

        target_width = round((self.width_cm + 2 * self.wrap_cm + 2 * self.white_cm) * self.dpi / self.CM_TO_INCH)
        target_height = round((self.height_cm + 2 * self.wrap_cm + 2 * self.white_cm) * self.dpi / self.CM_TO_INCH)

        actual_width = image_width + 2 * white_px
        actual_height = image_height + 2 * white_px
        delta_width = actual_width - target_width
        delta_height = actual_height - target_height

        if delta_width != 0:
            white_left = white_px - ((delta_width // 2) + delta_width % 2)
            white_right = white_px - (delta_width // 2)
        else:
            white_left = white_px
            white_right = white_px

        if delta_height != 0:
            white_top = white_px - ((delta_height // 2) + delta_height % 2)
            white_bottom = white_px - (delta_height // 2)
        else:
            white_top = white_px
            white_bottom = white_px

        canvas_width = image_width + white_left + white_right
        canvas_height = image_height + white_top + white_bottom
        canvas = Image.new("RGB", (canvas_width, canvas_height), color="white")
        canvas.paste(self.image, (white_left, white_top))

        self.image = canvas

    def add_number(self):
        canvas = self.image
        white_px = self.cm_to_px(self.white_cm)

        draw = ImageDraw.Draw(canvas)

        px = (self.text_px / 72) * self.dpi

        try:
            font = ImageFont.truetype(self.font_path, px)
        except Exception:
            logger.exception('Font not found')
            font = ImageFont.load_default()

        if self.number:
            bbox = draw.textbbox((0, 0), self.number, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # top number
            x = (canvas.width - text_width) // 2
            y = (white_px + self.black_px) // 2 - text_height // 2 - 10
            draw.text((x, y), self.number, font=font, fill="red", stroke_width=5, stroke_fill="white")

            # bottom number
            y = canvas.height - self.black_px - text_height * 2 + 10
            draw.text((x, y), self.number, font=font, fill="red", stroke_width=5, stroke_fill="white")

            self.image = canvas

    def black_frame(self):
        canvas = self.image

        draw = ImageDraw.Draw(canvas)
        draw.rectangle(
            [(0, 0), (canvas.width - 1, canvas.height - 1)],
            outline="black",
            width=self.black_px)

        self.image = canvas

    def save_image(self):
        os.makedirs(data.photo_processing_path, exist_ok=True)
        material_dir = os.path.join(data.photo_processing_path, self.material)
        os.makedirs(material_dir, exist_ok=True)

        filename = f"{self.width_cm}х{self.height_cm}"
        if self.material == 'Баннер':
            filename = '_' + filename
        elif self.material == 'Матовый':
            filename = '@' + filename

        if self.number:
            filename += f" {self.number}"

        filename += f" {self.material}.jpg"

        def unique_filename(directory, base_filename):
            base, ext = os.path.splitext(base_filename)
            counter = 2
            new_filename = base_filename

            while os.path.exists(os.path.join(directory, new_filename)):
                new_filename = f"{base} ({counter}){ext}"
                counter += 1

            return new_filename

        filename = unique_filename(material_dir, filename)
        self.filepath = os.path.join(material_dir, filename)

        self.image.save(self.filepath, "JPEG", quality=100, dpi=(self.dpi, self.dpi), icc_profile=self.icc)
        logger.info(f"File saved: {self.filepath}")

    def process_image(self) -> Path:
        if self.image:
            self.image = self.image.crop(self.coordinates)
            self.image = self.image.resize((self.cm_to_px(self.width_cm), self.cm_to_px(self.height_cm)))

            self.stretch()
            self.white_frame()
            self.black_frame()
            self.add_number()
            self.save_image()

        return Path(self.filepath)
    
    def get_result_image(self) -> Image.Image:
        if self.image:
            self.image = self.image.crop(self.coordinates)
            self.image = self.image.resize((self.cm_to_px(self.width_cm), self.cm_to_px(self.height_cm)))

            self.stretch()
            self.white_frame()
            self.black_frame()
            self.add_number()
        
        return self.image
