from fastapi import FastAPI
import asyncio
import requests
from bs4 import BeautifulSoup
import os

app = FastAPI(
    title="Scraper"
)


async def check_status():
    response = requests.head("https://www.tesmanian.com/blogs/")
    status_code = response.status_code
    if status_code == requests.codes.ok:
        print("Status code is 200. I can start scraping.")
    else:
        print(f"Status code is {status_code}, something went wrong.")


async def save_cookie():
    if os.path.exists("data/cookies.txt") and os.stat("data/cookies.txt").st_size != 0:
        pass
    else:
        # Send a GET request to the website to retrieve the cookies
        response = requests.get("https://www.tesmanian.com/blogs/tesmanian-blog?page=1")
        # Save the cookies to a file
        with open("data/cookies.txt", "w") as f:
            for cookie in response.cookies:
                f.write(f"{cookie.name}={cookie.value};")
        print("Saved new cookies.")


async def scrape_website():
    # Load the saved cookies from the file
    with open("data/cookies.txt", "r") as f:
        cookie_str = f.read().strip()
    cookies = {}
    for cookie in cookie_str.split(";"):
        cookie_parts = cookie.split("=")
        if len(cookie_parts) == 2:
            name, value = cookie_parts
            cookies[name] = value

    while True:
        response = requests.get("https://www.tesmanian.com/blogs/tesmanian-blog?page=1", cookies=cookies)
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all cards
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

        await asyncio.sleep(999)



@app.get("/")
async def read_root():
    asyncio.create_task(scrape_website())
    return {"message": "Scraping Tesmanian blog for new posts every 15 seconds."}