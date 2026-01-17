import os
import subprocess
import time
from google import genai

# --- НАСТРОЙКИ ---
API_KEY = "AIzaSyACNo-9VHwbHtZzh9sI-gxYBuBmWzsV0kI"  # Получи на aistudio.google.com
MODEL_NAME = 'gemini-2.0-flash' # Самая быстрая и стабильная в 2026
TARGET_COVERAGE = 80

# Инициализация нового клиента (SDK 2026)
client = genai.Client(api_key=API_KEY)

def get_low_coverage_files():
    print("📊 Анализирую текущее покрытие...")
    result = subprocess.run(
        ['pytest', '--cov=app', '--cov-report=term-missing'],
        capture_output=True, text=True
    )
    
    low_cov_files = []
    lines = result.stdout.split('\n')
    
    for line in lines:
        if 'app/' in line and '%' in line:
            parts = line.split()
            try:
                filename = parts[0]
                coverage = int(parts[-2].replace('%', ''))
                if coverage < TARGET_COVERAGE and '__init__' not in filename:
                    missing_lines = parts[-1] if len(parts) > 5 else "all"
                    low_cov_files.append({
                        "file": filename, 
                        "cov": coverage, 
                        "missing": missing_lines
                    })
            except (ValueError, IndexError):
                continue
    return low_cov_files

import pyperclip

def generate_tests_for_file(file_info):
    target_file = file_info['file']
    missing = file_info['missing']
    
    with open(target_file, 'r') as f:
        source_code = f.read()
     # Пытаемся прочитать conftest.py, чтобы модель знала о фикстурах БД
    conftest_code = ""
    if os.path.exists("tests/conftest.py"):
        with open("tests/conftest.py", "r") as f:
            conftest_code = f.read()

    prompt = f"""
       Используются фикстуры из conftest.py: ( db_session, sample_user_client_data, sample_user_landlord_data, sample_apartment_data). 
    Написать тесты для файла: {target_file}
    
    КОД ФАЙЛА ДЛЯ ТЕСТОВ:
    {source_code}
    
    ВАЖНО: 
    - Импортировать модели: from app.models.{os.path.basename(target_file).replace('.py', '')} import ...
    - Не писать лишних рассуждений, только код.
    Напиши pytest тесты для этого файла: {target_file}
    Пропущенные строки в покрытии: {missing}
    
    ИСХОДНЫЙ КОД:
    {source_code}
    
    Верни только чистый код Python. Используй TestClient.
    """

    pyperclip.copy(prompt)
    
    print("\n" + "="*50)
    print(f"🚀 Промпт для файла {target_file} СКОПИРОВАН!")
    print(f"1. Перейди в браузер (Gemini/ChatGPT)")
    print(f"2. Нажми Ctrl+V и Enter")
    print(f"3. Сохрани результат")
    print("="*50)
    
    input("Нажмите Enter в этом терминале, когда закончите с этим файлом, чтобы скопировать следующий...")

if __name__ == "__main__":
    files_to_fix = get_low_coverage_files()
    for file in files_to_fix:
        generate_tests_for_file(file)




# 3. Если всё же Selenium (Путь «Партизана»)
# Если вы решите пойти этим путем, необходимо использовать библиотеку undetected-chromedriver, чтобы Google не заблокировал вас как бота.
# Пример логики для "Старшего товарища":
# python

# from undetected_chromedriver import Chrome
# import time

# driver = Chrome()
# driver.get("https://gemini.google.com")

# # Логинитесь вручную один раз
# input("Залогинься в Google и нажми Enter...")

# def ask_mentor(text):
#     textarea = driver.find_element(By.CSS_SELECTOR, "div[role='textbox']")
#     textarea.send_keys(text)
#     textarea.send_keys(Keys.ENTER)
#     # Тут нужен сложный поиск ответа и ожидание генерации