<h1 align="center">Sendy</h1>
<p align="center">
  <img src="images/sendy_icon.png" width="350"/>
</p>

## About

The program is designed for a single user and consists of a Telegram bot and a Cropper desktop application (built with
PyQt5).
It is intended for preparing photos for canvas printing and includes the following features:

- 🖼️ Photo Processing — automatically process photos for printing.
- ✂️ Cropper — crop images with non-standard aspect ratios.
- 🧮 Image Counter — track and count already printed photos.
- 📤 Image Loader — upload images from a local PC folder to the bot chat.

The project was created to automate the routine process of preparing photos for printing and to minimize human errors
during cropping and image counting.
It provides a simple and intuitive integration between a Telegram bot and a desktop application.
No server-side database is required, all data is stored locally.
The bot does not require deployment to a remote server and can be run directly on the local machine.

---

## Use case

- ***Photo Processing:***
    - It is used to prepare images for printing. Set the dimensions, add a number, and name the file properly.
    - The user sends a photo (or a photo document) to the bot with description. Example description: `40x60 #123 Холст`.
    - If the description is missing or doesn’t contain **width** and **height** values, the bot will ask the user to
      send it with a new message in this chat.
    - If the description is valid, the bot processes the photo and saves the resulting image in a specified folder
      (the user can set the folder path in the settings). Bot sends result in bot chat.
    - If the description lacks **width** and **height** or contains the key symbol `%`, the bot will open the
      Cropper application.
    - You can configure all the settings in Cropper Settings, in `/settings` you can oly see your current settings but
      cant change them. See the Screenshots section and find Cropper Settings screenshoot.


- ***Cropper:***
    - The user can open the Cropper application by sending `%`, `✂️` or by using `/cropper` command in the bot chat.
      The Cropper will also open automatically if the user doesn’t specify width and height during the
      **Photo Processing** stage.
    - In the Cropper application, the user can set the **width** and **height**, and a crop frame will be created
      accordingly. User also can add **number** or chose one of four types of **material** (Canvas, Banner, Cotton,
      Matte).
    - The user adjusts the crop frame position and presses the **Crop** button.
    - The bot processes the cropped photo, saves the resulting image to the specified folder, and sends the result back
      to the bot chat.


- ***Image Counter:***
    - The **Image Counter** counts the images in the folder and sends the resulting information.
    - In the settings, set the folder path where you want to count images. This folder can include subfolders.
    - o start counting, simply press the `🧮` button or use the `/counter` command.
    - The bot will send you messages showing how many images of each specific size and material were found.
      See an example in the screenshots section.


- ***Image Loader:***
    - **Image Loader** uploads images directly to the bot chat.
    - In the settings (use Cropper Settings), set the path to the folder from which you want to upload images to the
      chat.
    - The bot automatically detects images (.jpg, .png, .heic) and upload them to the chat.
    - One possible use case: you can process photos on your phone and upload them to your computer via OneDrive.
      OneDrive on your PC automatically saves the images to a local folder, and the bot retrieves them from that
      folder and sends them to the chat.
    - In the `/settings` you can clear this folder or just open it.

---

## How to run

You can run the project either as a `Python application` or as a compiled `.exe` file.

📌 ***Run as a Python project***
1. Clone the repository: 
```
git clone https://github.com/andrey-david/Sendy.git
```
2. Create and activate a virtual environment
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Create `.env` file in the project root and put in it your **Telegram bot token** and **Telegram user ID**.
5. Run `main.py`

📌 ***Run as .exe*** (You can just [download zip file](https://github.com/andrey-david/Sendy/releases))
1. Perform steps 1–3 from the **Run as a Python project** section.
2. Use `pyinstaller` to build the `.exe` file:
```
pyinstaller --noconsole --icon=sendy.ico --name Sendy main.py
```
3. Add in `/dist/Sendy` `sendy.ico` file and create `.env`. Put in `.env` your **Telegram bot token** and **Telegram 
user ID**.
Your folder should contain:
- _internal
- Sendy.exe
- sendy.ico
- .env
4. Run `Sendy.exe`
5. You can also include `updater.exe` if you want to always have the latest version of the Sendy program.
Use `pyinstaller` to build the `updater.exe` file:
```
pyinstaller --console --icon=updater/updater.ico --name=updater updater/updater.py
```
---

## Screenshots

- ***Photo Processing:***

The user sends an image with a description, and the bot returns the processed result.

<img src="\images\Photo_Processing_1.png"/>


**Photo Processing** `/settings`.

<img src="\images\Photo_Processing_2.png"/>


Example of the processed result.

<img src="\images\Photo_Processing_3.png"/>

<details>
  <summary>See full resulting image</summary>

<img src="\images\Photo_Processing_4.jpg"/>

</details>

- ***Cropper:***

To open the Cropper, simply add the `%` symbol to the description.

<img src="\images\Cropper_1.png"/>

Cropper main window.

<img src="\images\Cropper_2.png"/>

What you’ll see in the bot chat after pressing the `Crop` button.

<img src="\images\Cropper_3.png"/>

<details>
  <summary>See full resulting image</summary>

<img src="\images\Cropper_4.jpg"/>

</details>

**Cropper Settings**.

<img src="\images\Cropper_5.png"/>

- ***Image Counter:***

Example of counting images in `counter_test` folder.

<img src="\images\Image_counter_1.png"/>

- ***Image Loader:***

To load images, simply put them in the folder and the bot will automatically upload them to the chat.

<img src="\images\Image_loader_1.png"/>

---

## Technologies

- **The project runs on Python 3.12 and uses the following core libraries:**
    - aiogram
    - PyQt5
    - PIL (Pillow)

---
