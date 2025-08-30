from collections import Counter
import re
from data import data
import os
from aiogram.types import Message

async def Alex_podschot(folder, message: Message): #функция подсчёта
    exceptions = data['Alex_exceptions']
    all_text_to_message = []

    async def Alex_podschot_in(folder_in):
        text = ''
        holst = []
        banner = []
        hlopok = []
        matovi = []
        # считает и добавляет данные в соответствующие списки холст/баннер/хлопок
        for file in os.listdir(folder_in):
            if file.lower().endswith('.jpg') and 'х' in file:  # кириллица
                name_of_file = file
                file = re.search(r"(\d+)х(\d+)", file.lower())
                if file:
                    width, height = file.groups()
                    a = width + '×' + height
                    if 'матовый' in name_of_file.lower():
                        matovi.append(a)
                    elif 'холст' in name_of_file.lower():
                        holst.append(a)
                    elif 'баннер' in name_of_file.lower():
                        banner.append(a)
                    elif 'хлопок' in name_of_file.lower():
                        hlopok.append(a)
            elif os.path.isdir(folder_in + '\\' + file) and (file not in exceptions):
                await Alex_podschot_in(folder_in + '\\' + file)

        # считает элементы в списке присваивая им ключи в виде размеров и значения в виде количества размеров в списке (прим: Counter({'50×50': 9}) )
        banner_summ = Counter(banner)
        holst_summ = Counter(holst)
        hlopok_summ = Counter(hlopok)
        matovi_summ = Counter(matovi)

        # если длина списка отлична от нуля, то добавляет ключ и значение от counter в переменную text
        if len(banner) > 0:
            text += '\n<b>БАННЕР</b> ' + str(len(banner)) + 'шт.\n'
            for i in range(len(banner_summ)):
                text += str(list(banner_summ.keys())[i]) + ' = ' + str(list(banner_summ.values())[i]) + 'шт.\n'

        if len(holst) > 0:
            text += '\n<b>ХОЛСТ</b> ' + str(len(holst)) + 'шт.\n'
            for i in range(len(holst_summ)):
                text += str(list(holst_summ.keys())[i]) + ' = ' + str(list(holst_summ.values())[i]) + 'шт.\n'

        if len(hlopok) > 0:
            text += '\n<b>ХЛОПОК</b> ' + str(len(hlopok)) + 'шт.\n'
            for i in range(len(hlopok_summ)):
                text += str(list(hlopok_summ.keys())[i]) + ' = ' + str(list(hlopok_summ.values())[i]) + 'шт.\n'

        if len(matovi) > 0:
            text += '\n<b>МАТОВЫЙ</b> ' + str(len(matovi)) + 'шт.\n'
            for i in range(len(matovi_summ)):
                text += str(list(matovi_summ.keys())[i]) + ' = ' + str(list(matovi_summ.values())[i]) + 'шт.\n'

        # считает итого в папке, выводит текст в начало строки
        text = '📁 ' + folder_in.split('\\')[-2] + '\n └─ <b>' + folder_in.split('\\')[-1] + '</b>: ' + str(
            len(holst) + len(banner) + len(hlopok) + len(matovi)) + 'шт.\n' + text

        all_text_to_message.append(text) #собирает весь вывод в один список

    for element in os.listdir(folder):
        folder_in = folder + '\\' + element
        if os.path.isdir(folder_in) and (element not in exceptions): # проверка является ли folder_in папкой и нет ли её в списке исключений
            await Alex_podschot_in(folder_in)

    for i in all_text_to_message[::-1]: #переворачивает список и выводит его в виде сообщений
        await message.answer(text=i, parse_mode="HTML")