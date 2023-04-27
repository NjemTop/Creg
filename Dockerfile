# Используйте официальный образ Python как базовый
FROM python:3.9

# Установите рабочую директорию
WORKDIR /app

# Копируйте файлы с зависимостями и установите их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируйте остальные файлы проекта
COPY . .

# Запустите сервер разработки Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
