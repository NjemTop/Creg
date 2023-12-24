import requests

url = "https://board-web-test.x5.ru/Rest/auth/Login"
payload = {
    "userName": "test781",
    "password": "test781"
}

headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(url, data=payload, headers=headers)

print(response.text)
if response.status_code == 204:
    print("Авторизация успешна")
else:
    print(f"Ошибка авторизации: {response.status_code}")
