import platform
import subprocess
import time
import string
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Проверка наличия браузера Firefox
def check_firefox_installed():
    try:
        if platform.system() == 'Linux':
            subprocess.run(['firefox-esr', '--version'], check=True, capture_output=True)
        elif platform.system() == 'Darwin':
            subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'], check=True, capture_output=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

# Установка браузера Firefox
def install_firefox():
    try:
        subprocess.run(['sudo', 'apt', 'install', '-f', '-y'], check=True)
        subprocess.run(['sudo', 'apt', 'update'], check=True)
        subprocess.run(['sudo', 'apt', 'install', 'firefox'], check=True)
    except subprocess.CalledProcessError as error_message:
        print("Ошибка при установке Firefox:", error_message)
        exit()

# Функция для создания экземпляра сервиса Geckodriver
def create_driver_service():
    try:
        geckodriver_path = subprocess.check_output(['which', 'geckodriver']).decode().strip()
    except subprocess.CalledProcessError:
        print("Драйвер Firefox не найден. Убедитесь, что он установлен.")
        exit()
    return Service(geckodriver_path)

# Функция для создания экземпляра драйвера Firefox
def create_driver(service):
    try:
        options = FirefoxOptions()
        options.headless = True  # Запуск Firefox в безголовом режиме
        driver = webdriver.Firefox(service=service, options=options)
        return driver
    except Exception as e:
        print("Ошибка при инициализации драйвера:", str(e))
        exit()

# Функция для авторизации
def login(driver, username, password):
    try:
        login_url = 'https://dr.boardmaps.ru/ui/login'
        driver.get(login_url)

        # Ожидание появления полей ввода
        username_input = WebDriverWait(driver, 10).until(
            # Находим окно ввода УЗ
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="username"]'))
        )
        password_input = WebDriverWait(driver, 10).until(
            # Находим окно ввода пароля
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
        )

        # Вводим данные авторизации
        username_input.send_keys(username)
        password_input.send_keys(password)

        # Нажимаем кнопку авторизации
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button.el-button--brand'))
        )
        login_button.click()
    except Exception as error_message:
        print("Ошибка при авторизации:", str(error_message))
        driver.quit()
        exit()

# Функция для создания пользователя
def create_user(driver, username, email, password):
    try:
        create_user_url = 'https://dr.boardmaps.ru/ui/admin/management/users/new'

        driver.get(create_user_url)

        # Добавляем паузу для полной загрузки страницы
        time.sleep(5)

        # Заполнить данные пользователя и отправить форму
        username_input = WebDriverWait(driver, 10).until(
            # Находим окно, куда вводить данные о UserName
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-cy="user-name"]'))
        )
        email_input = WebDriverWait(driver, 10).until(
            # Находим окно, куда вводить данные о Email
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-cy="user-email"]'))
        )
        password_input = WebDriverWait(driver, 10).until(
            # Находим окно, куда вводить данные о вводе пароля
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-cy="user-password"]'))
        )
        retype_password_input = WebDriverWait(driver, 10).until(
            # Находим окно, куда вводить данные о повторном вводе пароля
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-cy="user-retype-password"]'))
        )

        # Передаём все значение в найденные ранее поля
        username_input.send_keys(username)
        email_input.send_keys(email)
        password_input.send_keys(password)
        retype_password_input.send_keys(password)

        # Найти кнопку "Exclude All Items"
        exclude_all_button = WebDriverWait(driver, 10).until(
            # Находим элемент с удалением всех ролей пользователя
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-cy="excludeAllItemsButton"]'))
        )
        exclude_all_button.click()

        # Выставить галку на выбор роли "Public"
        public_checkbox = WebDriverWait(driver, 10).until(
            # Находим элемент с чекбоксом паблик роли
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-cy="Public"]'))
        )
        public_checkbox.click()

        # Найти кнопку "Include Single Item"
        include_single_button = WebDriverWait(driver, 10).until(
            # Находим элемент с назначением выбранной роли
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-cy="includeSingleItemButton"]'))
        )
        include_single_button.click()
        
        # Найти кнопку "Save"
        save_button = WebDriverWait(driver, 10).until(
            # Находим элемент кнопки сохранения пользователя
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button.el-button--primary[data-cy="form-submit"]'))
        )
        save_button.click()

        print("Пользователь успешно создан")

    except Exception as error_message:
        print("Ошибка при создании пользователя:", str(error_message))

# Проверка наличия браузера Firefox и его установка при необходимости
if not check_firefox_installed():
    install_firefox()

def generate_random_password():
    """
    Функция генерации случайного пароля
    """
    uppercase_letters = string.ascii_uppercase
    lowercase_letters = string.ascii_lowercase
    digits = string.digits

    password_characters = uppercase_letters + lowercase_letters + digits
    password_length = 10

    password = ''.join(random.choice(password_characters) for _ in range(password_length))
    return password

def add_user_jfrog(username, email, password):

    # Создание экземпляра сервиса Geckodriver
    driver_service = create_driver_service()

    # Создание экземпляра драйвера Firefox
    driver = create_driver(driver_service)

    # Авторизация
    login(driver, 'creg_system', '8QBmmf4GRP')

    # Создание пользователя
    create_user(driver, username, email, password)

    # Закрытие драйвера и выход из сеанса
    driver.quit()


# user_name = 'test_client'
# user_email = 'test_client@example.com'
# user_password = 'Rfnzkj123123'

# # Вызов функции для создания пользователя
# add_user_jfrog(user_name, user_email, user_password)
