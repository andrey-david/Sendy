"""
Sendy Updater Script
--------------------
This script is used to update the "Sendy.exe" application.
It performs the following steps:
    1. Waits for "Sendy.exe" to be closed (if it is running).
    2. Locking for update by requests and getting version and URL to download "update.zip"
    3. Downloads the latest update package from a given URL.
    4. Extracts the update archive into the current directory.
    5. Restarts "Sendy.exe".

Usage:
    Place this script (compiled as `update.exe`) in the same directory as "Sendy.exe".
    The update process will start automatically when executed (usually executed by inline button in Sendy bot).

Notes:
    - use pyinstaller command <pyinstaller --onefile --icon=updater.ico updater.py>
    - The script assumes the update is provided as a `.zip` archive.
"""

import zipfile
import os
import sys
import time
import subprocess

import psutil
import requests
import gdown
from tqdm import tqdm
import colorama

application = "Sendy.exe"
file = 'update.zip'
directory = os.getcwd()
url_get_update = 'https://drive.usercontent.google.com/u/0/uc?id=1vjf8McN-gm7pc3Gfl4sYyOpOcXph5nXz&export=download'


def waiting_for_app_to_close(app: str) -> None:
    print(f'{colorama.Back.WHITE}{colorama.Fore.CYAN}ОБНОВЛЕНИЕ SENDY\n')
    spinner = ['♦----', '-♦---', '--♦--', '---♦-', '----♦', '---♦-', '--♦--', '-♦---']
    counter = 0
    while any(p.name() == app for p in psutil.process_iter()):  # пока app не завершён
        sys.stdout.write(
            f'\r{colorama.Back.YELLOW}{colorama.Fore.CYAN}{spinner[counter % len(spinner)]} НЕВОЗМОЖНО ОБНОВИТЬ, ЗАВЕРШИТЕ {app}')
        sys.stdout.flush()
        counter += 1
        time.sleep(0.1)
    print(
        f'\r{colorama.Back.GREEN}{colorama.Fore.WHITE}[+] НАЧАЛО ОБНОВЛЕНИЯ{colorama.Back.RESET}{colorama.Fore.RESET}{' ' * 25}')


def download_update_file(url: str, update_file: str) -> None:
    response = requests.get(url, stream=True, timeout=10)
    if response.status_code == 200:
        latest_version, update_link = response.text.split('|')
        print(f'{colorama.Back.CYAN}{colorama.Fore.WHITE}\n[i] ОБНОВЛЕНИЕ ДО {latest_version}\n')
        print(
            f'{colorama.Back.GREEN}{colorama.Fore.WHITE}[+] ПОДГТОТОВКА К СКАЧИВАНИЮ\n{colorama.Back.RESET}{colorama.Fore.CYAN}')
        gdown.download(update_link, update_file, quiet=False)
        print(f'{colorama.Back.GREEN}{colorama.Fore.WHITE}\n[+] СКАЧИВАНИЕ ЗАВЕРШЕНО\n')
    else:
        print(f'{colorama.Back.RED}{colorama.Fore.WHITE}\n[!] СЕРВЕР ДЛЯ ОБНОВЛЕНИЯ НЕДОСТУПЕН')
        raise Exception(f'Status code: {response.status_code}')


def unzip_update_file(update_file: str, update_dir: str) -> None:
    print(f'{colorama.Back.CYAN}{colorama.Fore.WHITE}[+] ИДЁТ ОБНОВЛЕНИЕ{colorama.Back.RESET}{colorama.Fore.CYAN}\n')
    with zipfile.ZipFile(update_file, 'r') as archive:
        for file in tqdm(archive.namelist(), unit=" file"):
            archive.extract(file, update_dir)

    os.remove(update_file)
    os.system("color 2F")
    print('\n[DONE] ОБНОВЛЕНИЕ УСПЕШНО ЗАВЕРШЕНО')


if __name__ == '__main__':
    colorama.init()
    try:
        waiting_for_app_to_close(application)
        download_update_file(url_get_update, file)
        unzip_update_file(file, directory)
        subprocess.Popen(application)
    except Exception as e:
        print(f'{colorama.Back.RED}{colorama.Fore.WHITE}\n[!] ОБНОВЛЕНИЕ ЗАВЕРШЕНО С ОШИБКОЙ\n'
              f'[ERROR] {e}{colorama.Back.RESET}{colorama.Fore.RESET}')
    print('\n\n\n            ', end='')
    input(f'{colorama.Back.CYAN}{colorama.Fore.YELLOW}ENTER{colorama.Fore.WHITE} ЧТОБЫ ЗАВЕРШИТЬ')
