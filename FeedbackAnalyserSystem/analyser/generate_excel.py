import json
import openpyxl

def generate_anchors_excel():
    # 1. Читаем ваши JSON файлы
    try:
        with open('anchors.json', 'r', encoding='utf-8') as f:
            en_data = json.load(f)
            
        with open('sentiment_anchors_ru.json', 'r', encoding='utf-8') as f:
            ru_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Ошибка: Не найден файл {e.filename}")
        return

    # 2. Создаем новую Excel книгу
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sentiment Anchors"

    # 3. Записываем заголовки (ваша функция во views.py начинает читать со 2-й строки)
    ws.append(["Text", "Sentiment", "Language"])

    # 4. Заполняем английскими якорями
    for sentiment, texts in en_data.items():
        for text in texts:
            ws.append([text, sentiment, "en"])

    # 5. Заполняем русскими якорями
    for sentiment, texts in ru_data.items():
        for text in texts:
            ws.append([text, sentiment, "ru"])

    # 6. Сохраняем файл
    filename = "combined_anchors.xlsx"
    wb.save(filename)
    print(f"✅ Файл '{filename}' успешно создан! Добавлено строк: {ws.max_row - 1}")

if __name__ == "__main__":
    generate_anchors_excel()