# -------------------------------------------------
# 1) Builder stage
# -------------------------------------------------
FROM python:3.12.8-slim AS builder

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем только файл зависимостей
COPY backend/requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
# Собираем колёса (wheels) во временную директорию /wheels
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# -------------------------------------------------
# 2) Final stage
# -------------------------------------------------
FROM python:3.12.8-slim

# Устанавливаем только необходимые рантайм-библиотеки
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем скомпилированные .whl из builder stage
COPY --from=builder /wheels /wheels
# Устанавливаем их
RUN pip install --no-cache-dir /wheels/*

COPY backend /app

CMD ["python", "manage.py", "runserver", "0.0.0.0:8137"]
