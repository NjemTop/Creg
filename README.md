# Creg

Creg - это приложение для управления клиентами, их контактами и другой важной информацией, разработанное на Django. Этот проект используется для...

## Содержание
1. [Установка](#Установка)
2. [Использование](#Использование)
3. [Конфигурация](#Конфигурация)
4. [Тестирование](#Тестирование)
5. [Деплоймент](#Деплоймент)
6. [Архитектура](#Архитектура)
7. [Контакты](#Контакты)

## Установка
### Локальная установка (без Docker)
1. Клонируйте репозиторий:
    ```bash
    git clone https://github.com/NjemTop/Creg.git
    ```
2. Перейдите в директорию проекта:
    ```bash
    cd Creg
    ```
3. Установите зависимости:
    ```bash
    pip install -r backend/requirements.txt
    ```
4. Настройте переменные окружения:
    ```bash
    cp .env.example .env
    ```
5. Запустите приложение:
    ```bash
    python manage.py runserver
    ```

### Запуск с Docker Compose
1. Клонируйте репозиторий и перейдите в директорию проекта:
    ```bash
    git clone https://github.com/NjemTop/Creg.git
    cd Creg
    ```
2. Запустите сборку и поднимите контейнеры:
    ```bash
    docker-compose build && docker-compose up -d
    ```
3. Создайте администратора:
    ```bash
    docker-compose exec web python3 manage.py createsuperuser
    ```

### Локальная установка (MacOS и Windows)
#### Для MacOS:
1. Установите переменное окружение для локального запуска:
    ```bash
    export DJANGO_ENV=local
    ```
2. Установите Homebrew:
    ```bash
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```
3. Добавьте Homebrew в PATH:
    ```bash
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
    ```
4. Установите PostgreSQL:
    ```bash
    brew install postgresql
    ```
5. Запустите сервер PostgreSQL:
    ```bash
    brew services start postgresql
    ```
6. Создайте базу данных и пользователя:
    ```bash
    createdb creg
    createuser -P -s postgres
    ```

#### Для Windows:
1. Скачайте и установите PostgreSQL для Windows [отсюда](https://www.postgresql.org/download/windows/).
2. Войдите в консоль PostgreSQL:
    ```bash
    psql -U postgres
    ```
3. Создайте базу данных:
    ```bash
    CREATE DATABASE creg;
    ```
4. Создайте пользователя:
    ```bash
    CREATE USER postgres WITH PASSWORD 'password';
    ```
5. Назначьте права пользователю:
    ```bash
    GRANT ALL PRIVILEGES ON DATABASE creg TO postgres;
    ```
6. Переключитесь на созданную базу данных:
    ```bash
    \c creg
    ```
7. Назначьте пользователю права суперпользователя:
    ```bash
    ALTER USER postgres WITH SUPERUSER;
    ```

## Использование
- Для доступа к админке используйте ссылку `/admin`.
- Основные функции проекта включают управление клиентами, создание рассылок и т.д.

## Конфигурация
- Настройка базы данных происходит в файле `settings.py`.
- Если требуется интеграция с внешними сервисами, настройте API ключи в `.env` файле.

## Тестирование
Для запуска тестов используйте команду:
```bash
python manage.py test
```

## Деплоймент
### Деплоймент с использованием Docker Compose
1. Соберите контейнеры и запустите их:
    ```bash
    docker-compose build && docker-compose up -d
    ```
2. Создайте администратора:
    ```bash
    docker-compose exec web python3 manage.py createsuperuser
    ```
### Деплоймент с использованием Kubernetes
1. Заполните файл `manifest/05_secrets.yaml` необходимыми значениями:
    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: db-secret
      namespace: creg
    type: Opaque
    data:
      POSTGRES_DB: <ваше-значение>
      POSTGRES_USER: <ваше-значение>
      POSTGRES_PASSWORD: <ваше-значение>
      DB_HOST: <ваше-значение>
      DB_PORT: <ваше-значение>
    ```

2. Примените манифесты в вашем Kubernetes кластере:
    ```bash
    kubectl apply -f manifest/
    ```

3. Убедитесь, что все поды запущены и работают корректно:
    ```bash
    kubectl get pods -n creg
    ```

## Архитектура
```markdown
## Структура проекта

- `main/`: Основное приложение, содержащее основные функции и управление клиентами.
- `api/`: REST API для взаимодействия с проектом.
- `apiv2/`: Приватный API с дополнительными функциями.
- `scripts/`: Скрипты для выполнения таких задач, как уведомления по электронной почте, обновления и многое другое.
- `templates/`: HTML-шаблоны, используемые в проекте.
- `static/`: Static файлы, такие как CSS, JavaScript и images.
```

## Контакты
Email: adenalka@gmail.com
