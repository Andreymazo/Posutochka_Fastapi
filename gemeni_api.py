# pip install -U google-generativeai
# Чтобы использовать AI на Google Search через API, не нужен Selenium. Google предоставляет прямой доступ через
# Google AI SDK или Vertex AI.
# Для автоматизации написания тестов это самый быстрый способ.
# 1. Получение ключа API

#     Зайдите в Google AI Studio.
#     Создайте бесплатный (или платный) ключ API.

import google.generativeai as genai
import os

# 1. Настройка
genai.configure(api_key="ВАШ_API_КЛЮЧ")
model = genai.GenerativeModel('gemini-2.0-pro-exp')

def upgrade_my_tests(router_path, test_path):
    # Читаем код роутера
    with open(router_path, 'r') as f:
        router_code = f.read()

    # Формируем промпт
    prompt = f"""
    Вы — старший разработчик. Я использую FastAPI.
    Вот код моего роутера:
    {router_code}

    Напишите для него профессиональные тесты на pytest, используя TestClient.
    Учтите схемы Pydantic и зависимости. Верните ТОЛЬКО чистый код Python.
    """

    # Делаем запрос по API
    print(f"Отправляю {router_path} в Google AI...")
    response = model.generate_content(prompt)

    # Записываем результат
    with open(test_path, 'w') as f:
        f.write(response.text.replace('```python', '').replace('```', ''))

    print(f"Готово! Тесты записаны в {test_path}")

# Запуск
upgrade_my_tests('app/routers/payments.py', 'tests/test_payments_new.py')


# Давай сделаем по-настоящему крутой инструмент: скрипт, который сам парсит твой отчет
# coverage, находит файлы с самым низким процентом и автоматически отправляет их в Google AI для генерации тестов.
# Шаг 1: Подготовка
# Тебе понадобится установленная библиотека:
# bash

# pip install -U google-generativeai

# Используйте код с осторожностью.
# Шаг 2: Скрипт «Авто-Тестировщик 2026»
# Создай файл ai_coverage_fixer.py в корне проекта. Этот скрипт будет «мозгом», который свяжет твой код и API.
# Here is the Python code for the "Auto-Tester 2026" script:
# python

# import os
# import subprocess
# import google.generativeai as genai

# # --- НАСТРОЙКИ ---
# API_KEY = "AIzaSyACNo-9VHwbHtZzh9sI-gxYBuBmWzsV0kI"  # Получи на aistudio.google.com
# MODEL_NAME = 'gemini-1.5-pro' # Самая стабильная для кода в 2026 году
# TARGET_COVERAGE = 80           # Файлы с покрытием ниже этого пойдут в работу

# genai.configure(api_key=API_KEY)
# model = genai.GenerativeModel(MODEL_NAME)

# def get_low_coverage_files():
#     """Запускает pytest-cov и находит проблемные файлы."""
#     print("📊 Анализирую текущее покрытие...")
#     # Запускаем pytest и получаем текстовый отчет
#     result = subprocess.run(
#         ['pytest', '--cov=app', '--cov-report=term-missing'],
#         capture_output=True, text=True
#     )
    
#     low_cov_files = []
#     lines = result.stdout.split('\n')
    
#     for line in lines:
#         if 'app/' in line and '%' in line:
#             parts = line.split()
#             filename = parts[0]
#             try:
#                 coverage = int(parts[-2].replace('%', ''))
#                 # Если покрытие ниже цели и это не __init__
#                 if coverage < TARGET_COVERAGE and '__init__' not in filename:
#                     missing_lines = parts[-1] if len(parts) > 5 else "all"
#                     low_cov_files.append({
#                         "file": filename, 
#                         "cov": coverage, 
#                         "missing": missing_lines
#                     })
#             except ValueError:
#                 continue
#     return low_cov_files

# def generate_tests_for_file(file_info):
#     """Отправляет файл в AI и записывает результат."""
#     target_file = file_info['file']
#     missing = file_info['missing']
#     test_file = f"tests/test_{os.path.basename(target_file)}"
    
#     print(f"🤖 Обрабатываю {target_file} ({file_info['cov']}%). Нужны строки: {missing}")
    
#     with open(target_file, 'r') as f:
#         source_code = f.read()

#     # Читаем существующий тест, если он есть
#     existing_test = ""
#     if os.path.exists(test_file):
#         with open(test_file, 'r') as f:
#             existing_test = f.read()

#     prompt = f"""
#     Ты — Senior Python QA Engineer. Твоя задача — поднять покрытие тестами для FastAPI проекта.
    
#     ФАЙЛ: {target_file}
#     ТЕКУЩЕЕ ПОКРЫТИЕ: {file_info['cov']}%
#     ПРОПУЩЕННЫЕ СТРОКИ: {missing}
    
#     ИСХОДНЫЙ КОД:
#     {source_code}
    
#     СУЩЕСТВУЮЩИЕ ТЕСТЫ (если есть):
#     {existing_test}
    
#     ЗАДАНИЕ:
#     Напиши новые тесты на pytest, которые покроют пропущенные строки {missing}. 
#     - Используй TestClient.
#     - Мокай базу данных через unittest.mock или фикстуры, если нужно.
#     - Если тесты уже есть, добавь только НОВЫЕ функции в конец.
#     - Верни ТОЛЬКО чистый код Python без пояснений.
#     """

#     response = model.generate_content(prompt)
#     clean_code = response.text.replace('```python', '').replace('```', '').strip()

#     with open(test_file, 'a' if existing_test else 'w') as f:
#         if not existing_test:
#             f.write(clean_code)
#         else:
#             f.write(f"\n\n{clean_code}")
    
#     print(f"✅ Тесты записаны в {test_file}")

# if __name__ == "__main__":
#     files_to_fix = get_low_coverage_files()
#     if not files_to_fix:
#         print("🎉 Все файлы имеют отличное покрытие!")
#     else:
#         print(f"Найдено {len(files_to_fix)} файлов для доработки.")
#         for file in files_to_fix[:3]: # Делаем по 3 файла за раз, чтобы не спамить
#             generate_tests_for_file(file)
