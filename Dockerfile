# Этап установки зависимостей
# Устанавливасем "лёгкую" зависимость
FROM python:3.9-alpine AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем папку logs
RUN mkdir /logs

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
    pip install --no-cache-dir psycopg2-binary && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

# Этап сборки приложения
FROM python:3.9-alpine
WORKDIR /app
COPY --from=builder /app /app
# Установим часовой пояс Москвы, для контейнера
RUN echo "Europe/Moscow" > /etc/timezone && dpkg-reconfigure -f noninteractive tzdata

# Копируем остальные файлы проекта
COPY . .

# Запустите сервер Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8137"]
