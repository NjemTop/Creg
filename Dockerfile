# Этап установки зависимостей
# Устанавливаем "легкую" зависимость
FROM python:3.9 AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем папку logs
RUN mkdir /logs

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc musl-dev libpq-dev && \
    pip install --no-cache-dir psycopg2-binary && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y gcc musl-dev libpq-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Этап сборки приложения
FROM python:3.9
WORKDIR /app
COPY --from=builder /app /app

# Устанавливаем часовой пояс
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/* && \
    cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone

# Копируем остальные файлы проекта
COPY . .

# Запускаем сервер Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8137"]
