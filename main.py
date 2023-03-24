import asyncio
import pickle

import requests
import uvicorn
from bs4 import BeautifulSoup
from fastapi import FastAPI

from settings import PASSWORD, EMAIL

app = FastAPI(
    title="Scraper"
)

REPEAT_TIME = 999


class Scraper(object):
    def __init__(self):
        self.session = requests.session()
        self.cookies_file = "data/cookies.pkl"
        self.secure_url = "https://www.tesmanian.com/"
        self.base_url = "https://www.tesmanian.com/blogs/tesmanian-blog?page=1"

    async def login(self):
        login_page = self.session.get("https://www.tesmanian.com/account/login/")
        login_data = {"email": EMAIL, "password": PASSWORD}
        response = self.session.post(login_page.url, data=login_data)
        with open(self.cookies_file, "wb") as f:
            pickle.dump(self.session.cookies, f)

    async def authorization(self):
        with open(self.cookies_file, "rb") as f:
            cookies = pickle.load(f)
        self.session.cookies.update(cookies)
        response = self.session.get(self.secure_url)
        if response.ok:
            print("Authorized successfully")
        else:
            print("Failed to authorize")

    async def check_status(self):
        response = requests.head(self.secure_url)
        if response.ok:
            print("Status code is 200. I can start scraping.")
            return True
        else:
            print(f"Status code is {response.status_code}, something went wrong.")
            return False

    async def run(self):
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
            print(results)

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
