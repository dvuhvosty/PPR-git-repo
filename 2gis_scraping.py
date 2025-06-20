from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

import requests
from bs4 import BeautifulSoup

import time
import csv
from datetime import datetime

options = Options()
options.headless = True  # Enable headless mode for invisible operation

url = 'https://2gis.ru/moscow/firm/4504127916787967/tab/reviews' # ППР
url = "https://2gis.ru/moscow/firm/563478234639522/tab/reviews" # РН-Карт Роснефть
url = 'https://2gis.ru/moscow/firm/70000001019039929/tab/reviews' # Газпромнефть-региональные продажи
url = 'https://2gis.ru/moscow/firm/70000001028525750/tab/reviews' # Топливные решения

driver = webdriver.Chrome(options=options)
driver.get(url) 

# скроллим страницу до конца, чтобы загрузить все отзывы, по умолчанию загружается 50 отзывов

scrollable_div = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "_1rkbbi0x"))  
) # scroll=true

prev_height = -1 
max_scrolls = 100
scroll_count = 0

while scroll_count < max_scrolls:
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
    time.sleep(1)  # подождать подгрузки
    new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
    if new_height == prev_height:
        break
    prev_height = new_height
    scroll_count += 1

# дата отзыва вставляется при видимости отзыва на экране, поэтому на каждом отзыве останавливаемся отдельно

reviews = driver.find_elements(By.CLASS_NAME, '_1k5soqfl')
actions = ActionChains(driver)

# переписываем дату из формата "16 июня 2025" в 2025-06-16

months = {
    "января": "01",
    "февраля": "02",
    "марта": "03",
    "апреля": "04",
    "мая": "05",
    "июня": "06",
    "июля": "07",
    "августа": "08",
    "сентября": "09",
    "октября": "10",
    "ноября": "11",
    "декабря": "12"
}

def parse_russian_date(date_str):
    parts = date_str.split()
    if len(parts) == 3: # 16 июня 2025
        day, month_name, year = parts
    else: # 16 июня 2025, отредактирован
        day, month_name, year = date_str.split(',')[0].split()
    month = months.get(month_name.lower())
    if month:
        return f"{year}-{month}-{int(day):02d}"  # YYYY-MM-DD

# останавливаемся на каждом отзыве - узнаем его дату написания
# останавливаемся на каждом ответе и нажимаем на него, чтобы он подгрузился полностью - из него получаем полный ответ и дату ответа 

date_review_list = []
date_response_list = []
response_list = []
for review in reviews:
    try:
        actions.move_to_element(review).perform()
        date_elem = review.find_element(By.CLASS_NAME, '_a5f6uz')
        date_review_list.append(parse_russian_date(date_elem.text))
        date_response_elem = review.find_element(By.CLASS_NAME, '_1evjsdb')
        date_response_list.append(parse_russian_date(date_response_elem.text.split(',')[0]))

        response_elem = review.find_element(By.CLASS_NAME, '_1wk3bjs')
        response_elem.click()
        response_list.append(response_elem.text)
    except:
        date_response_list.append('')
        response_list.append('')

# количество звезд определяется по ширине элемента - 10px - 1 звезда и т.д.

stars_list = []
stars = driver.find_elements(By.CLASS_NAME, '_1fkin5c')
for el in stars[1:]:
    stars_list.append(el.size['width'] // 10)

html_content = driver.page_source
driver.quit()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept-Language': 'ru-RU,ru;q=0.9',
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(html_content, 'lxml')

review_user = soup.find_all('span', class_='_16s5yj36')
reviews = soup.find_all('div', class_='_49x36f')
data = [['user', 'date_review', 'stars', 'review', 'date_response', 'response']]

for i in range(len(reviews)):
    data.append([review_user[i].text, date_review_list[i], stars_list[i], reviews[i].text, \
        date_response_list[i], response_list[i]])

with open ('oil-solutions.csv', 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(data)


