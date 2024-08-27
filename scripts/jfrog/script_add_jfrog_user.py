import requests
import json

# Параметры JFrog
JFROG_URL = "https://dr2.boardmaps.ru/ui"
JFROG_USER = "admin"
JFROG_PASSWORD = "7mgluCk3_4PAKvuxkJXX"

# Функция для авторизации в JFrog
def authenticate():
    """
    Функция для авторизации в систему JFrog
    """
    url = f"{JFROG_URL}/api/v1/ui/auth/login?_spring_security_remember_me=false"
    headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    }
    data = {
        "user": JFROG_USER,
        "password": JFROG_PASSWORD,
        "type": "login"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.cookies

# Функция для создания пользователя в JFrog
def create_user(username, password, cookies):
    """
    Функция для создания пользователя.
    На себя принимает "username" и "password",
    а также "cookies" полученные ранее при авторизации в систему JFrog
    """
    url = f"{JFROG_URL}/api/v1/access/api/ui/users"
    headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    }
    data = {
        "profileUpdatable": True,
        "internalPasswordDisabled": False,
        "watchManager": False,
        "reportsManager": False,
        "policyManager": False,
        "resourcesManager": False,
        "policyViewer": False,
        "email": f"{username}@example.com",
        "password": password,
        "username": username,
        "groups": ["Clients"],
        "disableUiAccess": True
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=json.dumps(data))
    response.raise_for_status()
    print(f"User {username} created successfully.")

# Чтение файла user.txt и создание пользователей
def main():
    cookies = authenticate()
    with open("scripts/jfrog/user.txt", "r") as file:
        for line in file:
            if line.strip():  # Пропуск пустых строк
                parts = line.split(", ")
                username = parts[0].split(": ")[1]
                password = parts[1].split(": ")[1]
                create_user(username, password, cookies)

if __name__ == "__main__":
    main()
