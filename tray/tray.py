"""System tray

Provides a tray icon with menu items:
    • Cropper - to start the Sendy Cropper
    • Stop - to stop Sendy app

Note:
    Uses pystray and runs actions in separate threads.
"""

import asyncio
import logging
import os

import pystray
import threading
from PIL import Image

from cropper.cropper_main import sendy_cropper
from config import config
from handlers import stop_sendy

logger = logging.getLogger(__name__)
icon_path = os.path.join(config.app_dir, "sendy.ico")


def run_cropper() -> None:
    """Start the Sendy Cropper application in a new thread."""
    threading.Thread(target=sendy_cropper).start()


def stop_sendy_from_tray() -> None:
    """Schedules the asynchronous `stop_sendy` coroutine in the bot's event loop."""
    asyncio.run_coroutine_threadsafe(stop_sendy(), config.bot_loop)


menu = pystray.Menu(
    pystray.MenuItem('Cropper', run_cropper),
    pystray.MenuItem('Stop', stop_sendy_from_tray)
)

sendy_tray = pystray.Icon(name='Sendy', icon=Image.open(icon_path), menu=menu)


async def tray() -> None:
    """Runs the pystray icon in a separate daemon thread. Includes a short delay
    to allow other coroutines to initialize before starting the tray.
    """
    await asyncio.sleep(1)  # give time to other coroutines to start
    threading.Thread(target=sendy_tray.run, daemon=True).start()
