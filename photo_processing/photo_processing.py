import os
import logging
import asyncio

from PIL import Image, ImageDraw, ImageFont

from data import data
from config import config
from keyboards.keyboards import keyboard_inline_open_photo

logger = logging.getLogger(__name__)


class PhotoProc:
    def __init__(self):
        self.img = None
        self.FONT_PATH: str = "arial.ttf"
        self.number: str = ''
        self.width_cm: float = 0
        self.height_cm: float = 0
        self.material: str = 'ХОЛСТ'
        self.message = None
        self.flag: bool = True
        self.coordinates: tuple[int, int, int, int] = (0, 0, 0, 0)
        self.WRAP_CM: float = data.photo_processing_wrap_cm
        self.WHITE_CM: float = data.photo_processing_white_cm
        self.black_px: int = data.photo_processing_black_px
        self.text_px: int = data.photo_processing_font_size_px
        self.DPI: int = data.photo_processing_dpi
        self.CM_TO_INCH: float = 2.54
        self.CM_TO_PX = lambda cm: int((cm * self.DPI) / self.CM_TO_INCH)
        self.filepath = ''
        self.filename = ''

    def add_image(self, img):
        self.img = img

    def set_presets(self, number='', width_cm=0, height_cm=0, material=0, message=None, flag=True,
                    coordinates=(0, 0, 0, 0)):
        self.number = number
        self.width_cm = width_cm
        self.height_cm = height_cm
        self.material = material
        self.message = message
        self.flag = flag
        self.coordinates = coordinates

    def stretch_edges(self):
        w, h = self.img.size
        zav_px = self.CM_TO_PX(self.WRAP_CM)
        source_px = 20

        def get_stretched_strip(crop_box, final_size):
            strip = self.img.crop(crop_box)
            return strip.resize(final_size, Image.LANCZOS)

        left_strip = get_stretched_strip((0, 0, source_px, h), (zav_px, h))
        right_strip = get_stretched_strip((w - source_px, 0, w, h), (zav_px, h))
        top_strip = get_stretched_strip((0, 0, w, source_px), (w, zav_px))
        bottom_strip = get_stretched_strip((0, h - source_px, w, h), (w, zav_px))

        left_zav = left_strip.crop((zav_px - zav_px, 0, zav_px, h))
        right_zav = right_strip.crop((0, 0, zav_px, h))
        top_zav = top_strip.crop((0, zav_px - zav_px, w, zav_px))
        bottom_zav = bottom_strip.crop((0, 0, w, zav_px))

        new_img = Image.new("RGB", (w + 2 * zav_px, h + 2 * zav_px))

        left_zav = left_zav.transpose(Image.FLIP_LEFT_RIGHT)
        right_zav = right_zav.transpose(Image.FLIP_LEFT_RIGHT)
        top_zav = top_zav.transpose(Image.FLIP_TOP_BOTTOM)
        bottom_zav = bottom_zav.transpose(Image.FLIP_TOP_BOTTOM)

        new_img.paste(self.img, (zav_px, zav_px))
        new_img.paste(left_zav, (0, zav_px))
        new_img.paste(right_zav, (w + zav_px, zav_px))
        new_img.paste(top_zav, (zav_px, 0))
        new_img.paste(bottom_zav, (zav_px, h + zav_px))

        # Обработка углов изображения
        corner_crop_px = 20
        corner_orig_tl = self.img.crop((20, 20, 40, 40))
        corner_orig_tr = self.img.crop((w - 40, 20, w - 20, 40))
        corner_orig_bl = self.img.crop((20, h - 40, 40, h - 20))
        corner_orig_br = self.img.crop((w - 40, h - 40, w - 20, h - 20))

        corner_tl = corner_orig_tl.resize((zav_px, zav_px)).crop((0, 0, zav_px, zav_px))
        corner_tr = corner_orig_tr.resize((zav_px, zav_px)).crop((zav_px - zav_px, 0, zav_px, zav_px))
        corner_bl = corner_orig_bl.resize((zav_px, zav_px)).crop((0, zav_px - zav_px, zav_px, zav_px))
        corner_br = corner_orig_br.resize((zav_px, zav_px)).crop((zav_px - zav_px, zav_px - zav_px, zav_px, zav_px))

        new_img.paste(corner_tl, (0, 0))
        new_img.paste(corner_tr, (w + zav_px, 0))
        new_img.paste(corner_bl, (0, h + zav_px))
        new_img.paste(corner_br, (w + zav_px, h + zav_px))

        self.img = new_img

    def photo_proc(self):
        WRAP_CM = self.WRAP_CM
        WHITE_CM = self.WHITE_CM
        white_px = self.CM_TO_PX(WHITE_CM)
        black_px = self.black_px
        text_px = self.text_px
        DPI = self.DPI

        # Растягивание краёв изображения
        w, h = self.img.size

        # Желаемый финальный размер:

        target_w = round((self.width_cm + 2 * WRAP_CM + 2 * WHITE_CM) * DPI / self.CM_TO_INCH)
        target_h = round((self.height_cm + 2 * WRAP_CM + 2 * WHITE_CM) * DPI / self.CM_TO_INCH)

        # Коррекция white_px
        actual_w = w + 2 * white_px
        actual_h = h + 2 * white_px
        delta_w = actual_w - target_w
        delta_h = actual_h - target_h

        # Распределим отступы по сторонам
        white_left = white_px
        white_right = white_px
        white_top = white_px
        white_bottom = white_px

        if delta_w != 0:
            white_left = white_px - ((delta_w // 2) + delta_w % 2)
            white_right = white_px - (delta_w // 2)
        if delta_h != 0:
            white_top = white_px - ((delta_h // 2) + delta_h % 2)
            white_bottom = white_px - (delta_h // 2)

        # Создание белой рамки
        canvas_width = w + white_left + white_right
        canvas_height = h + white_top + white_bottom
        canvas = Image.new("RGB", (canvas_width, canvas_height), color="white")

        # Вставка изображения внутрь белой рамки
        canvas.paste(self.img, (white_left, white_top))

        # Добавление текста (номера)
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype(self.FONT_PATH, text_px)
        except:
            font = ImageFont.load_default()

        if self.number:
            bbox = draw.textbbox((0, 0), self.number, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # номер сверху
            x = (canvas.width - text_width) // 2
            y = (white_px + black_px) // 2 - text_height // 2 - 10
            draw.text((x, y), self.number, font=font, fill="red", stroke_width=5, stroke_fill="white")

            # номер снизу
            x = (canvas.width - text_width) // 2
            y = canvas.height - black_px - text_height * 2 + 10
            draw.text((x, y), self.number, font=font, fill="red", stroke_width=5, stroke_fill="white")

        # Добавление чёрной рамки поверх всей композиции
        draw = ImageDraw.Draw(canvas)
        draw.rectangle(
            [(0, 0), (canvas.width - 1, canvas.height - 1)],
            outline="black",
            width=black_px)

        # Сохранение
        os.makedirs(data.photo_processing_path, exist_ok=True)
        product_dir = os.path.join(data.photo_processing_path, self.material)
        os.makedirs(product_dir, exist_ok=True)

        filename = f"{self.width_cm}х{self.height_cm}"
        if self.material == 'Баннер':
            filename = '_' + filename
        elif self.material == 'Матовый':
            filename = '@' + filename

        if self.number:
            filename += f" {self.number}"
        filename += f" {self.material}"
        filename += ".jpg"

        def unique_filename(directory, base_filename):
            base, ext = os.path.splitext(base_filename)
            counter = 2
            new_filename = base_filename

            while os.path.exists(os.path.join(directory, new_filename)):
                new_filename = f"{base}_{counter}{ext}"
                counter += 1

            return new_filename

        filename = unique_filename(product_dir, filename)
        self.filename = filename
        self.filepath = os.path.join(product_dir, filename)

        with open(r"C:\Windows\System32\spool\drivers\color\sRGB Color Space Profile.icm", "rb") as f:
            icc_bytes = f.read()

        canvas.save(self.filepath, "JPEG", quality=100, dpi=(DPI, DPI), icc_profile=icc_bytes)
        logger.info(f"Файл сохранён: {self.filepath}")

    def process_image(self):
        if self.img:
            crop_px = data.photo_processing_crop_px
            w, h = self.img.size

            if self.flag:  # обработка БЕЗ sendy_cropper
                self.img = self.img.crop((crop_px, crop_px, w - crop_px, h - crop_px))
                self.img = self.img.resize((self.CM_TO_PX(self.width_cm), self.CM_TO_PX(self.height_cm)))
            else:  # обработка ЧЕРЕЗ sendy_cropper
                self.img = self.img.crop(self.coordinates)
                self.img = self.img.resize((self.CM_TO_PX(self.width_cm), self.CM_TO_PX(self.height_cm)))

            self.stretch_edges()
            self.photo_proc()

            asyncio.run_coroutine_threadsafe(self.send_via_bot(), config.bot_loop)

    async def send_via_bot(self):
        try:
            await self.message.answer(f"✅ <b>Изображение сохранено</b>\n\n🏷 <code>{self.filename}</code>",
                                      reply_markup=keyboard_inline_open_photo(self.filepath),
                                      reply_to_message_id=self.message.message_id)
        except Exception as e:
            await self.message.answer(f"💀 Ошибка: {str(e)}"
                                      f"\n\n✅ <b>Изображение успешно сохранено: </b>\n<code>{self.filepath}</code>")
