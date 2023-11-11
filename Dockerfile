# Используем официальный образ Python как базовый
FROM python:3.9-slim as builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Установка postgresql-client
RUN apt-get update && apt-get install -y postgresql-client

# Создаем папку logs
RUN mkdir /logs

# Установка необходимых зависимостей для компиляции библиотеки python-ldap
RUN apt-get update && apt-get install -y \
    gcc \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev

# Копируем файлы с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установим часовой пояс Москвы, для контейнера
RUN echo "Europe/Moscow" > /etc/timezone && dpkg-reconfigure -f noninteractive tzdata

# Установка зависимостей для Microsoft ODBC Driver for SQL Server
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg \
    curl \
    unixodbc \
    unixodbc-dev

# Добавление репозитория Microsoft и ключа подписи
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Установка ODBC драйвера
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Удаление ненужных файлов
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Копируем остальные файлы проекта
COPY . .
