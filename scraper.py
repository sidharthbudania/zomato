import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

restaurant_links = [
    "https://www.zomato.com/visakhapatnam/siripuram-restaurants",
    "https://www.zomato.com/visakhapatnam/mvp-colony-restaurants",
    "https://www.zomato.com/visakhapatnam/maharani-peta-restaurants",
]

all_urls, all_rest_name, all_ratings, all_price = [], [], [], []
all_cuisine, all_images, all_address, all_timing, all_contact = [], [], [], [], []

driver = webdriver.Chrome()

for link in restaurant_links:
    driver.get(link)
    time.sleep(2)

    scroll_pause_time = 1.8
    screen_height = driver.execute_script("return window.screen.height;")
    i = 1
    while True:
        driver.execute_script("window.scrollTo(0, {});".format(screen_height * i))
        i += 1
        time.sleep(scroll_pause_time)
        if screen_height * i > driver.execute_script("return document.body.scrollHeight;"):
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    divs = soup.findAll('div', class_='jumbo-tracker')

    for parent in divs:
        name_tag = parent.find("h4")
        if not name_tag:
            continue

        rest_name = name_tag.text.strip()
        link_tag = parent.find("a", class_="sc-hqGPoI")
        full_link = urljoin("https://www.zomato.com", link_tag.get('href')) if link_tag else ""
        image_tag = parent.find("img", class_="sc-s1isp7-5")
        image_url = image_tag.get("src") if image_tag else None
        rating_tag = parent.find("div", class_="sc-1q7bklc-1")
        rating = rating_tag.text.strip() if rating_tag else None

        try:
            tags = parent.find_all("p", class_="sc-1hez2tp-0")
            cuisine = tags[0].text.strip() if len(tags) > 0 else ""
            price = tags[1].text.strip() if len(tags) > 1 else ""
            address = tags[2].text.strip() if len(tags) > 2 else ""
            timing = tags[3].text.strip() if len(tags) > 3 else ""
        except:
            cuisine = price = address = timing = ""

        all_rest_name.append(rest_name)
        all_urls.append(full_link)
        all_ratings.append(rating)
        all_price.append(price)
        all_cuisine.append(cuisine)
        all_images.append(image_url)
        all_address.append(address)
        all_timing.append(timing)

        driver.get(full_link)
        time.sleep(2)
        detail_soup = BeautifulSoup(driver.page_source, "html.parser")
        tel_tag = detail_soup.find("a", href=lambda h: h and "tel:" in h)
        mail_tag = detail_soup.find("a", href=lambda h: h and "mailto:" in h)
        contact = tel_tag.get_text(strip=True) if tel_tag else (mail_tag.get_text(strip=True) if mail_tag else "")
        all_contact.append(contact)

df = pd.DataFrame({
    'links': all_urls,
    'names': all_rest_name,
    'ratings': all_ratings,
    'price for one': all_price,
    'cuisine': all_cuisine,
    'images': all_images,
    'address': all_address,
    'timing': all_timing,
    'contact': all_contact
})

df.to_csv("restaurant_data.csv", index=False)
df.to_json("restaurant_data.json", orient="records", indent=4)
driver.close()
