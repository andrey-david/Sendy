"""
Image counter
--------------------
This script is used to count, categorize, and send all the images that have already been processed by user.
It helps the user keep track of statistics.

It performs the following steps:
    1. The `counter_outer` function receives a folder path where all `.jpg` files should be counted.
       The function looks specifically for `.jpg` files containing the Cyrillic letter 'х' in their names.
       It also processes nested subfolders recursively.
    2. It then builds a `list_of_all_sizes`.
    3. Finally, all elements from this list are sent to the user’s chat via aiogram.

Usage:
    Set the folder path in Sendy settings and press the 🧮 button.
"""

from collections import Counter
import re
import os
import logging

from aiogram.types import Message

from data.data import data

logger = logging.getLogger(__name__)


async def count_images_in_folder(folder, message: Message):
    exceptions = data['Alex_exceptions']
    all_sizes_sorted = []

    def process_subfolder(subfolder):
        materials: dict[str, list[str]] = {'ХОЛСТ': [], 'БАННЕР': [], 'ХЛОПОК': [], 'МАТОВЫЙ': []}

        # считает и добавляет данные в соответствующие списки холст/баннер/хлопок/матовый
        for file in os.listdir(subfolder):
            file = file.upper()
            if file.endswith('.JPG') and 'Х' in file:  # кириллица
                have_width_height = re.search(r"(\d+)Х(\d+)", file)
                if have_width_height:
                    width, height = have_width_height.groups()
                    width_height = f'{width}×{height}'
                    for material in materials:
                        if material in file:
                            materials[material].append(width_height)
                            break

            elif os.path.isdir(os.path.join(subfolder, file)) and (file not in exceptions):
                process_subfolder(os.path.join(subfolder, file))

        # если длина списка отлична от нуля, то добавляет ключ и значение от counter в строковую переменную
        def add_to_counter(name: str, counter: Counter[str]) -> str:
            list_of_sizes = ''
            if sum(counter.values()):
                list_of_sizes += f'\n<b>{name} {sum(counter.values())} шт.</b>\n'
                for key, value in counter.items():
                    list_of_sizes += f' {key} = {value} шт.\n'
            return list_of_sizes

        all_sizes = ''
        for material in materials:
            all_sizes += add_to_counter(material, Counter(materials[material]))

        # считает итого в папке, выводит текст в начало строки
        num_of_files_in_folder = sum(len(i) for i in materials.values())
        current_folder = os.path.basename(subfolder)
        try:
            parent_folder = os.path.basename(os.path.dirname(subfolder))
            current_folder_sizes = f'📁 {parent_folder}\n └─ <b>{current_folder}: {num_of_files_in_folder} шт.</b>\n{all_sizes}'
        except IndexError:
            logger.exception(f'There is no parent folder {subfolder}')
            current_folder_sizes = f'📁 <b>{current_folder}\n: {num_of_files_in_folder} шт.</b>\n{all_sizes}'

        all_sizes_sorted.append(current_folder_sizes)  # собирает все списки с размерами в один список

    for element in os.listdir(folder):
        folder_in = os.path.join(folder, element)
        if os.path.isdir(folder_in) and (element not in exceptions):  # folder_inner папка и не в исключениях
            process_subfolder(folder_in)

    for msg in all_sizes_sorted[::-1]:  # переворачивает список и выводит его в виде сообщений
        await message.answer(text=msg)
