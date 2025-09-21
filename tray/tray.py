import asyncio

import pystray
from PIL import Image
from threading import Thread

from cropper.cropper_main import sendy_cropper
from config import config
from handlers import stop_sendy

def stop_sendy_from_tray():
    asyncio.run_coroutine_threadsafe(stop_sendy(), config.bot_loop)


icon_path = "sendy.ico"

menu = pystray.Menu(
    pystray.MenuItem('Cropper', lambda: Thread(target=sendy_cropper).start()),
    pystray.MenuItem('Stop', stop_sendy_from_tray)
)

sendy_tray = pystray.Icon(name='Sendy', icon=Image.open(icon_path), menu=menu)