import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Данные берутся из скрытых настроек GitHub
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FORM_URL = os.environ.get("FORM_URL")
MY_EMAIL = os.environ.get("MY_EMAIL")
MY_NAME = os.environ.get("MY_NAME")
MY_ID = os.environ.get("MY_ID")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        response = requests.post(url, json=payload)
        # --- ДОБАВЬ ЭТИ ДВЕ СТРОКИ ---
        print(f"DEBUG: Статус ответа от Telegram: {response.status_code}")
        print(f"DEBUG: Текст ответа от Telegram: {response.text}")
    except Exception as e:
        print(f"Ошибка отправки в ТГ: {e}")

def run_bot():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    actions = ActionChains(driver)

    NEXT_BUTTON_XPATH = "//div[@role='button' and (contains(., 'Далее') or contains(., 'Далі') or contains(., 'Dalej') or contains(., 'Next'))]"

    try:
        print("Открываем форму...")
        driver.get(FORM_URL)

        # --- ЭКРАН 1 ---
        email_input = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@type='email']"))
        )
        email_input.send_keys(MY_EMAIL)

        next_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, NEXT_BUTTON_XPATH))
        )
        time.sleep(1)
        next_btn.click()
        time.sleep(2.5)

        # --- ЭКРАН 2 ---
        text_inputs = WebDriverWait(driver, 15).until(
            EC.visibility_of_all_elements_located((By.XPATH, "//input[@type='text']"))
        )
        text_inputs[0].send_keys(MY_NAME)
        time.sleep(0.5)
        text_inputs[1].send_keys(MY_ID)

        radio_label = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '2. Chcę') or contains(text(), '2. I want')]"))
        )
        radio_option = radio_label.find_element(By.XPATH, "./ancestor::div[contains(@role, 'radio') or @data-value]")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio_option)
        time.sleep(1)

        for attempt in range(4):
            if radio_option.get_attribute("aria-checked") == "true":
                break
            try:
                if attempt == 0: radio_option.click()
                elif attempt == 1: driver.execute_script("arguments[0].click();", radio_option)
                elif attempt == 2: actions.move_to_element(radio_option).click().perform()
                elif attempt == 3: radio_label.click()
            except: pass
            time.sleep(0.5)

        time.sleep(1)
        next_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, NEXT_BUTTON_XPATH))
        )
        try: next_btn.click()
        except: driver.execute_script("arguments[0].click();", next_btn)
        time.sleep(2.5)

        # --- ЭКРАН 3 ---
        try:
            city_dropdown = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='listbox']"))
            )
            try: city_dropdown.click()
            except: driver.execute_script("arguments[0].click();", city_dropdown)
            time.sleep(1.5)

            radom_option = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='option' and contains(., 'Radom')]"))
            )
            try: radom_option.click()
            except: driver.execute_script("arguments[0].click();", radom_option)
        except:
            radom_radio = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(@role, 'radio') or contains(@role, 'checkbox') or self::span][contains(., 'Radom')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radom_radio)
            time.sleep(0.5)
            try: radom_radio.click()
            except: driver.execute_script("arguments[0].click();", radom_radio)

        time.sleep(1)
        next_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, NEXT_BUTTON_XPATH))
        )
        try: next_btn.click()
        except: driver.execute_script("arguments[0].click();", next_btn)
        time.sleep(2.5)

        # --- ЭКРАН 4 ---
        try:
            slots_dropdown = driver.find_element(By.XPATH, "//div[@role='listbox']")
            try: slots_dropdown.click()
            except: driver.execute_script("arguments[0].click();", slots_dropdown)
            time.sleep(2)
        except:
            pass

        page_content = driver.page_source

        # --- ФИНАЛЬНАЯ ЛОГИКА ---
        is_slots_available = not any(phrase in page_content for phrase in ["Brak dostępnych", "Brak dismantling", "Brak dostępnych", "Брак доступных", "Нет доступных", "No available"])

        if is_slots_available:
            message = "🎉 ВНИМАНИЕ! СЛОТЫ НАЙДЕНЫ! БЕГОМ НА САЙТ! 🎉"
            print(message)
            send_telegram(message)

            # Звонок
            username = "@hzzry"
            call_text = "Внимание! Найдены свободные слоты! Срочно зайди на сайт!"
            call_text_formatted = call_text.replace(" ", "+")
            call_url = f"http://api.callmebot.com/telegram/start.php?user={username}&text={call_text_formatted}&lang=ru-RU-Standard-C"
            requests.get(call_url)
            print("📞 Запрос на звонок успешно отправлен!")
        else:
            message = "🤖 Бот проверил форму: слотов пока нет."
            print(message)
            send_telegram(message)

    except Exception as e:
        print(f"Произошла ошибка при выполнении: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    run_bot()
