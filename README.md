# Crag

В процессе переноса из Flask на Django

Вэб-сервер работает по порту 8137<br>
PostgreSQL работает по порту 5432<br>
RabbitMQ работает по портам 5672 и 15672<br>


Запускаем как обычно `docker-compose build && docker-compose up -d`<br>
После запуска создаём админскую учётную запись с помощью команды `docker-compose exec web python3 manage.py createsuperuser`<br>

## Если мы хотим использовать проект локально, то нам нужно сделать следующее:

### Для MacOS:
1. Создаём БД с названием "database_1_TEST.db"
2. Нам нужно сделать переменное переменное окружение для определения локального запуска проекта
3. Перед запуском нужно выполнить команду: `export DJANGO_ENV=local` для установки переменного окружения DJANGO_ENV
4. Устанавливаем "Homebrew" командой:
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
5. Добавляем Homebrew в переменную PATH вашей оболочки:
`echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile`
`eval "$(/opt/homebrew/bin/brew shellenv)"`
6. Устанавливаем PostgreSQL с помощью Homebrew:
`brew install postgresql`
7. Запускаем сервер PostgreSQL:
`brew services start postgresql`
8. Создаём новую базу данных и пользователя с помощью следующих команд:
`createdb database_1_TEST.db`
`createuser -P -s sa`
9. Вводим пароль kJGnTXBT при создании пользователя.