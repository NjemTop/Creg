# Используем официальный образ Python как базовый
FROM python:3.9

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем папку logs
RUN mkdir /logs

# Копируем файлы с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Запустите сервер Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8137"]
