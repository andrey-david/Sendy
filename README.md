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

text

---

## Screenshots

- ***Photo Processing:***

The user sends an image with a description, and the bot returns the processed result.

![](\images\Photo_Processing_1.png)


**Photo Processing** `/settings`.

![](\images\Photo_Processing_2.png)


Example of the processed result.

![](\images\Photo_Processing_3.png)

<details>
  <summary>See full resulting image</summary>

  ![](\images\Photo_Processing_4.jpg)

</details>

- ***Cropper:***

To open the Cropper, simply add the `%` symbol to the description.

![](\images\Cropper_1.png)

Cropper main window.

![](\images\Cropper_2.png)

What you’ll see in the bot chat after pressing the `Crop` button.

![](\images\Cropper_3.png)

<details>
  <summary>See full resulting image</summary>

  ![](\images\Cropper_4.jpg)

</details>

**Cropper Settings**.

![](\images\Cropper_5.png)

- ***Image Counter:***

Example of counting images in `counter_test` folder.

![](\images\Image_counter_1.png)

- ***Image Loader:***

To load images, simply put them in the folder and the bot will automatically upload them to the chat.

![](\images\Image_loader_1.png)

---

## Features

text

---

## Technologies

- **The project runs on Python 3.12 and uses the following core libraries:**
    - aiogram
    - PyQt5
    - PIL (Pillow)

---
