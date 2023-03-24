import asyncio
import os
import pickle

import requests
import uvicorn
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ParseMode
from aiogram.utils import executor
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI

from settings import PASSWORD, EMAIL

app = FastAPI(
    title="Scraper"
)

# Bot setup
load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("/start"))

# Sleep time
REPEAT_TIME = 999


@dp.message_handler(commands=["start"])
async def cmd_answer(message: types.Message):
    await message.answer(
        "<b>Tesla scraper is ready.</b>")


class Scraper(object):
    def __init__(self):
        self.session = requests.session()
        self.cookies_file = "data/cookies.pkl"
        self.secure_url = "https://www.tesmanian.com/"
        self.base_url = "https://www.tesmanian.com/blogs/tesmanian-blog?page=1"

    # Login using email and pwd
    async def login(self):
        login_page = self.session.get("https://www.tesmanian.com/account/login/")
        login_data = {"email": EMAIL, "password": PASSWORD}
        response = self.session.post(login_page.url, data=login_data)
        with open(self.cookies_file, "wb") as f:
            pickle.dump(self.session.cookies, f)

    # Login with cookies
    async def authorization(self):
        with open(self.cookies_file, "rb") as f:
            cookies = pickle.load(f)
        self.session.cookies.update(cookies)
        response = self.session.get(self.secure_url)
        if response.ok:
            print("Authorized successfully")
        else:
            print("Failed to authorize")

    # Check status of website
    async def check_status(self):
        response = requests.head(self.secure_url)
        if response.ok:
            print("Status code is 200. I can start scraping.")
            return True
        else:
            print(f"Status code is {response.status_code}, something went wrong.")
            return False

    # Start scraping
    async def run(self, call: types.CallbackQuery):
        while True:
            response = self.session.get(self.base_url)
            soup = BeautifulSoup(response.content, "html.parser")
            cards = soup.find_all("div", class_="blog-post-card__info")

            results = []
            for card in cards:
                # Scrape main post-card with tag h2
                title_element_h2 = card.find("p", class_="h2")
                # Scrape other post-cards with tag h3
                title_element_h3 = card.findNext("p", class_="h3")
                title_h2 = title_element_h2.text.strip() if title_element_h2 else None
                # title_h3 = title_element_h3.text.strip() if title_element_h3 else None
                link_element = card.find("a")
                link = link_element["href"] if link_element else None
                results.append({"title": title_h2, "link": link})

            # Send results to the Telegram bot
            chat_id = call.message.chat.id
            message = "Scraping results:\n\n"
            for result in results:
                message += f"{result['title']} - {result['link']}\n"
            await bot.send_message(chat_id=chat_id, text=message)

            await asyncio.sleep(REPEAT_TIME)


@app.on_event("startup")
async def start_app():
    scraper = Scraper()
    await scraper.login()
    await scraper.authorization()
    status_ok = await scraper.check_status()
    if not status_ok:
        raise Exception("Status code is not OK, stopping program")
    asyncio.create_task(scraper.run())


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
    executor.start_polling(dp, skip_updates=True)

    # async def send_results_to_telegram_bot(message: types.Message, results):
    #     chat_id = message.chat.id
    #     message = "<b>Scraped Results:</b>\n\n"
    #     for result in results:
    #         message += f"<a href='{result['link']}'>{result['title']}</a>\n\n"
    #     try:
    #         await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
    #         print('Results sent successfully to Telegram chat.')
    #     except Exception as e:
    #         print(f'Error sending results to Telegram chat: {e}')
