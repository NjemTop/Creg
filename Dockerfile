# Используем официальный образ Python как базовый
FROM python:3.9-slim as builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем папку logs
RUN mkdir /logs

# Копируем файлы с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установим часовой пояс Москвы, для контейнера
RUN echo "Europe/Moscow" > /etc/timezone && dpkg-reconfigure -f noninteractive tzdata

# Устанавливаем дополнительные пакеты
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка браузера Firefox и Geckodriver
RUN apt-get update \
    && apt-get install -y firefox-esr \
    && apt-get install -y wget \
    && apt-get install -y libgtk-3-0 \
    && apt-get install -y libdbus-glib-1-2 \
    && apt-get install -y libxt6 \
    && rm -rf /var/lib/apt/lists/*

# Установка Geckodriver
RUN wget -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz \
    && tar -xf /tmp/geckodriver.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/geckodriver \
    && rm /tmp/geckodriver.tar.gz

# Копируем остальные файлы проекта
COPY . .

# Копируем файл env внутрь контейнера
COPY .env .
