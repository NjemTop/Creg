# Используем официальный образ Python как базовый
FROM python:3.10.11-slim as builder

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
    procps

# Копируем файлы с зависимостями и устанавливаем их
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Этап создания конечного образа
FROM python:3.10.11-slim
WORKDIR /app

# Копируем установленные зависимости из билдера
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Установка зависимостей, необходимых для работы приложения
RUN apt-get update && apt-get install -y postgresql-client procps \
    # Удаление ненужных файлов
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Копируем остальные файлы проекта
COPY . .

# Установим часовой пояс Москвы, для контейнера
RUN echo "Europe/Moscow" > /etc/timezone && dpkg-reconfigure -f noninteractive tzdata

# Создаем папку logs
RUN mkdir -p /app/logs

CMD ["sh", "-c", "python3.10 manage.py makemigrations && python3.10 manage.py migrate && python3.10 manage.py runserver 0.0.0.0:8137"]
