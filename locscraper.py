import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

df = pd.read_csv('zomtrue.csv')
data = []

driver = webdriver.Chrome()

for link in df['links']:
    cleaned_link = link.split('/order')[0]
    driver.get(cleaned_link)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, '//a[starts-with(@href, "https://www.google.com/maps/dir/?api=1&destination=")]')
        ))

        driver.execute_script("window.scrollBy(0, 500)")
        driver.implicitly_wait(1)

        anchor = driver.find_element(By.XPATH, '//a[starts-with(@href, "https://www.google.com/maps/dir/?api=1&destination=")]')
        href = anchor.get_attribute("href")

        if "destination=" in href:
            coords = href.split('destination=')[1]
            latitude, longitude = map(float, coords.split(','))
        else:
            latitude, longitude = None, None

        address = driver.find_element(By.CSS_SELECTOR, 'p.sc-1hez2tp-0.clKRrC').text

        data.append({
            'Links': link,
            'Address': address,
            'Latitude': latitude,
            'Longitude': longitude
        })
    except:
        data.append({
            'Links': link,
            'Address': 'Timeout or Error',
            'Latitude': None,
            'Longitude': None
        })

driver.quit()

pd.DataFrame(data).to_csv('scraped_data.csv', index=False)
print(pd.DataFrame(data).head())

