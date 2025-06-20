from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from datetime import datetime

options = Options()
options.headless = True  # Enable headless mode for invisible operation

url = 'https://yandex.ru/maps/org/peredovyye_platezhnyye_resheniya/103262022758/reviews/' # ППР
url = 'https://yandex.ru/maps/org/korporatsiya_spetsialnykh_tekhnologiy/209569973500/reviews/' # Корпорация Специальных Технологий
url = 'https://yandex.ru/maps/org/rn_kart/1423401275/reviews/' # РН-Карт Роснефть
url = 'https://yandex.ru/maps/org/likard/1281619984/reviews/' # Ликард Лукойл
url = 'https://yandex.ru/maps/org/mosoyl/115211564335/reviews/' # МосОйл топливные карты
url = 'https://yandex.ru/maps/org/tk_toplivnyye_resheniya/211128449644/reviews/' # ТК Топливные решения
url = 'https://yandex.ru/maps/org/e1_card/158246068510/reviews/' # E1 Card
url = 'https://yandex.ru/maps/org/masters/1724424178/reviews/' # Мастерс
url = 'https://yandex.ru/maps/org/yunikard_oyl/162561333238/reviews/' # Юникард-Ойл

driver = webdriver.Chrome(options=options)
driver.get(url) 

# скроллим страницу до конца, чтобы загрузить все отзывы, по умолчанию загружается 50 отзывов

scrollable_div = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "scroll__container")) # business-reviews-card-view__review scroll _width_wide
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

# чтобы отзыв полностью загрузился, нужно нажать кнопку "еще"

reviews = driver.find_elements(By.CLASS_NAME, 'business-reviews-card-view__review')
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
    if len(parts) == 3: # 16 июня 2024
        day, month_name, year = parts
    else: # 16 июня, текущий год не указывается
        day, month_name, year = parts[0], parts[1], '2025'
    month = months.get(month_name.lower())
    if month:
        return f"{year}-{month}-{int(day):02d}"  # YYYY-MM-DD
    
date_review_list = []
review_list = []
stars_list = []
date_response_list = []
response_list = []

for review in reviews:
    try:
        actions.move_to_element(review).perform()
        # дата отзыва
        date_elem = review.find_element(By.CLASS_NAME, 'business-review-view__date')
        date_review_list.append(parse_russian_date(date_elem.text))
        
        # клик по кнопке "еще"
        try:
            # Пытаемся кликнуть на кнопку "еще", если она есть
            review.find_element(By.CLASS_NAME, 'business-review-view__expand').click()
            time.sleep(0.3)
        except:
            pass
        review_text = review.find_element(By.CLASS_NAME, 'spoiler-view__text-container')
        review_list.append(review_text.text)

        # отзыв в div.business-reviews-card-view__review и в одном из отзывов нет div.business-rating-badge-view с оценкой
        stars = review.find_element(By.CLASS_NAME, 'business-rating-badge-view__stars')
        aria_label = stars.get_attribute('aria-label')
        # print(f"aria-label: {aria_label}")
        match = re.search(r'Оценка\s+(\d)', aria_label)
        if match:
            stars_list.append(match.group(1))
        else:
            stars_list.append('')  # Если атрибут не содержит оценку


        # чтобы загрузить ответ на отзыв, нужно нажать кнопку "Посмотреть ответ организации"
        review.find_element(By.CLASS_NAME, 'business-review-view__comment-expand').click()
        date_response = review.find_element(By.CLASS_NAME, 'business-review-comment-content__date')
        date_response_list.append(date_response.text)

        response = review.find_element(By.CLASS_NAME, 'business-review-comment-content__bubble')
        response_list.append(response.text)
    except: 
        date_response_list.append('')
        response_list.append('')


html_content = driver.page_source
driver.quit()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept-Language': 'ru-RU,ru;q=0.9',
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(html_content, 'lxml')

review_user = soup.find_all('span', itemprop='name')
data = [['user', 'date_review', 'stars', 'review', 'date_response', 'response']] # 'stars', 


for i in range(len(reviews)):
    data.append([review_user[i].text, date_review_list[i], stars_list[i], review_list[i], \
        date_response_list[i], response_list[i]])


with open ('ya_maps_unicard_oil.csv', 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(data)