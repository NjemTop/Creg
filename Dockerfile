# Этап установки зависимостей
# Устанавливаем "легкую" зависимость
FROM python:3.9-alpine AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем папку logs
RUN mkdir /logs

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev bash && \
    apk add --no-cache celery && \
    pip install --no-cache-dir psycopg2-binary && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

# Этап сборки приложения
FROM python:3.9-alpine
WORKDIR /app
COPY --from=builder /app /app

# Устанавливаем часовой пояс
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone && \
    apk del tzdata

# Копируем остальные файлы проекта
COPY . .

# Запускаем сервер Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8137"]
