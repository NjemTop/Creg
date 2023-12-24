# Используем официальный образ Python как базовый
FROM python:3.9-slim as builder

# Устанавливаем рабочую директорию
WORKDIR /app

RUN apt-get update && apt-get install -y \
    # Установка postgresql-client
    postgresql-client \
    # Установка необходимых зависимостей для компиляции библиотеки python-ldap
    gcc \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    # Установка зависимостей для Microsoft ODBC Driver for SQL Server
    gnupg \
    curl \
    unixodbc \
    unixodbc-dev \
    # Добавление репозитория Microsoft и ключа подписи
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    # Установка ODBC драйвера
    && apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    # Удаление ненужных файлов
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Копируем файлы с зависимостями и устанавливаем их
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Установим часовой пояс Москвы, для контейнера
RUN echo "Europe/Moscow" > /etc/timezone && dpkg-reconfigure -f noninteractive tzdata

# Создаем папку logs
RUN mkdir /logs

# Копируем остальные файлы проекта
COPY . .
