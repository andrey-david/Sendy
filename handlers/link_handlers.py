"""Link handlers

Handle Instagram link searches in Google Sheets.
"""

import logging
import re

import gspread
from aiogram import F, Router
from aiogram.types import Message
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError, WorksheetNotFound

from lexicon import link_lex
from data import data

link_router = Router(name="link_router")
logger = logging.getLogger(__name__)

SHEET_NAME = "One_Holst Учёт"
WORKSHEET_NAMES = ("Учет клиентов", "Металл")

URL_PATTERN = re.compile(
    r"https?://(?:www\.)?instagram\.com/[^\s]+|"
    r"(?:www\.)?instagram\.com/[^\s]+",
    re.IGNORECASE,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def create_spreadsheet() -> gspread.Spreadsheet | None:
    """Authenticate with Google Sheets and open the spreadsheet."""
    credentials_file = data.link_credentials_file_path

    if not credentials_file.is_file():
        logger.error("Credentials file '%s' was not found", credentials_file)
        return None

    try:
        credentials = Credentials.from_service_account_file(
            str(credentials_file),
            scopes=SCOPES,
        )
        client = gspread.authorize(credentials)
        return client.open(SHEET_NAME)
    except (OSError, ValueError, gspread.exceptions.GSpreadException):
        logger.exception("Failed to initialize Google Sheets")
        return None


def extract_url(text: str) -> str | None:
    """Extract the first Instagram URL from the given text."""
    match = URL_PATTERN.search(text)
    return match.group(0).rstrip(".,;!?)\"]}") if match else None


def normalize(url: str) -> str:
    """Normalize a URL to the instagram.com/username format."""
    url = url.strip().lower()
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)

    parts = url.split("?", maxsplit=1)[0].rstrip("/").split("/")

    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"

    return parts[0]


def search_in_worksheet(
        spreadsheet: gspread.Spreadsheet,
        worksheet_name: str,
        user_link_norm: str,
) -> list[str]:
    """Return all matching numbers from the specified worksheet."""
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        rows = worksheet.get_all_values()
    except WorksheetNotFound:
        logger.error("Worksheet '%s' was not found", worksheet_name)
        return []

    found = []

    for row in rows[1:]:
        if len(row) < 3:
            continue

        if normalize(row[2]) == user_link_norm:
            found.append(row[0])

    logger.debug(
        "Worksheet '%s': found %d matches",
        worksheet_name,
        len(found),
    )

    return found


@link_router.message(F.text.regexp(URL_PATTERN))
async def find_link(message: Message) -> None:
    """Search Google Sheets for the Instagram link in a message."""
    text = message.text or ""
    user_link = extract_url(text)
    spreadsheet = create_spreadsheet()

    if spreadsheet is None:
        await message.reply(link_lex["google_sheets_search_no_file"])
        return

    if not user_link:
        await message.reply(link_lex["instagram_link_not_found"])
        return

    user_link_norm = normalize(user_link)
    results = {}

    try:
        for worksheet_name in WORKSHEET_NAMES:
            numbers = search_in_worksheet(
                spreadsheet,
                worksheet_name,
                user_link_norm,
            )

            if numbers:
                results[worksheet_name] = numbers

    except APIError:
        logger.exception("Google Sheets API request failed")
        await message.reply(link_lex["google_sheets_search_error"])
        return

    if not results:
        await message.reply(link_lex["instagram_link_not_in_sheet"])
        return

    lines = []

    for worksheet_name, numbers in results.items():
        if worksheet_name == "Металл":
            lines.append(link_lex["metal_sheet_header"])

        lines.extend(
            f"{link_lex['number_label']}: {number}"
            for number in numbers
        )
        lines.append("")

    await message.reply("\n".join(lines).strip())
