import requests
import json

def authenticate_and_get_company_name(proxy_url, username, password, cert_path):
    # Создаем сессию
    session = requests.Session()

    # URL эндпоинта авторизации и получения информации о компании
    auth_url = f"{proxy_url}/Rest/auth/Login"
    companies_url = f"{proxy_url}/api3/companies/current"

    # Учетные данные
    payload = {
        "userName": username,
        "password": password
    }

    # Заголовки запроса
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:

        # Запрос на авторизацию
        auth_response = session.post(auth_url, data=payload, headers=headers, cert=(cert_path))

        if auth_response.status_code == 204:
            print("Авторизация успешна!")

            # Запрос информации о компании
            companies_response = session.get(companies_url, headers=headers, cert=(cert_path))

            if companies_response.status_code == 200:
                company_data = companies_response.json()
                company_name = company_data['fullName']['translations']['ru']
                print(f"Название компании: {company_name}")
                return company_name
            else:
                print(f"Ошибка при получении информации о компании: {companies_response.text}")
        else:
            print(f"Ошибка авторизации: {auth_response.text}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def simulate_ipad_requests(proxy_url, username, password, cert_path):
    # Создаем сессию
    session = requests.Session()

    # Заголовки запроса
    headers = {
        "User-Agent": "Boardmaps/2611 CFNetwork/1410.0.3 Darwin/22.6.0"
    }

    # Учетные данные для регистрации устройства
    device_registration_payload = {
        "userName": username,
        "password": password
    }

    try:
        # Запрос на картинку
        # picture_response = session.get(f"{proxy_url}/pictures/00000000-0000-0000-0000-000000000001", headers=headers, cert=(cert_path, key_path))
        # print("Ответ на запрос картинки:", picture_response.status_code, picture_response.text)

        # Запрос на публичные настройки
        # public_settings_response = session.get(f"{proxy_url}/api2/publicsettings", headers=headers, cert=(cert_path, key_path))
        # print("Ответ на запрос публичных настроек:", public_settings_response.status_code, public_settings_response.text)

        # POST запрос на регистрацию устройства
        # device_registration_response = session.post(f"{proxy_url}/Services/AuthenticationService.svc/DeviceRegistration", json=device_registration_payload, headers=headers, cert=(cert_path, key_path))
        # print("Ответ на запрос регистрации устройства:", device_registration_response.status_code, device_registration_response.text)

        # # Запросы на сервис синхронизации
        # sync_service_response_1 = session.get(f"{proxy_url}/Services/SynchronizationService.svc/0", headers=headers, cert=(cert_path, key_path))
        # print("Ответ на первый запрос сервиса синхронизации:", sync_service_response_1.status_code, sync_service_response_1.text)

        # sync_service_response_2 = session.post(f"{proxy_url}/Services/SynchronizationService.svc/434993", headers=headers, cert=(cert_path, key_path))
        # print("Ответ на второй запрос сервиса синхронизации:", sync_service_response_2.status_code, sync_service_response_2.text)

        # # Запрос на получение skinBundle
        # skin_bundle_response = session.get(f"{proxy_url}/api/skinBundle", headers=headers, cert=(cert_path, key_path))
        # print("Ответ на запрос skinBundle:", skin_bundle_response.status_code, skin_bundle_response.text)

        print("Запросы выполнены успешно.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    x5_proxy_url = "https://board-web-test.x5.ru"
    x5_username = "test781"
    x5_password = "test781"
    x5_cert_path = "C:/Users/Adena/Documents/Сертификат/Danil.Soldatov.pem"
    x5_key_path = "C:/Users/Adena/Documents/Сертификат/Danil.Soldatov_private_key.pem"
    proxy_url = "https://rp-sys.boardmaps.ru"
    username = "demo-karaseva"
    password = "demo321"
    cert_path = "C:/Users/Adena/Documents/Сертификат/Test_Cert.pem"
    key_path = "C:/Users/Adena/Documents/Сертификат/Test_Cert_private_key.pem"

    authenticate_and_get_company_name(x5_proxy_url, x5_username, x5_password, x5_cert_path)





# import requests

# # Авторизация и получение сессионной куки
# url_auth = "https://bm-sup-5.boardmaps.com/Rest/auth/Login"
# payload_auth = {
#     "userName": "demo-karaseva",
#     "password": "demo321"
# }

# headers_auth = {
#     "Content-Type": "application/x-www-form-urlencoded"
# }

# session = requests.Session()  # Создаем сессию для хранения сессионной куки

# response_auth = session.post(url_auth, data=payload_auth, headers=headers_auth)

# if response_auth.status_code == 204:
#     print("Авторизация успешна")

#     # Создание заседания
#     url_create_meeting = "https://bm-sup-5.boardmaps.com/publicapi/meeting/create"
    
#     # Здесь формируйте объект MeetingCreationCommandDto
#     meeting_data = [
#         {
#             "ActualDate": "2023-10-30T10:00:00",
#             "AgendaAgreementDate": "2023-10-25T12:00:00",
#             "Attendance": {
#                 "AttendanceType": "InPerson"
#             },
#             "Name": "Заседание №1",
#             "Number": "1",
#             "PlaceAddress": "Адрес",
#             "PlaceName": "Место проведения",
#             "PlannedDate": "2023-11-15T14:00:00",
#             "MeetingType": {
#                 "MeetingType": "Meeting"
#             },
#             "Initiator": {
#                 "Id": "12345678-1234-1234-1234-123456789012"
#             }
#         }
#     ]

#     headers_create_meeting = {
#         "Content-Type": "application/json"
#     }

#     response_create_meeting = session.post(url_create_meeting, json=meeting_data, headers=headers_create_meeting)

#     if response_create_meeting.status_code == 200:
#         print("Заседание успешно создано")
#     else:
#         print(f"Ошибка создания заседания: {response_create_meeting.status_code}")
# else:
#     print(f"Ошибка авторизации: {response_auth.status_code}")

# import zeep
# import requests

# # Авторизация и получение сессионной куки
# url_auth = "https://bm-sup-5.boardmaps.com/Rest/auth/Login"
# payload_auth = {
#     "userName": "demo-karaseva",
#     "password": "demo321"
# }

# headers_auth = {
#     "Content-Type": "application/x-www-form-urlencoded"
# }

# session = requests.Session()  # Создаем сессию для хранения сессионной куки

# response_auth = session.post(url_auth, data=payload_auth, headers=headers_auth)

# if response_auth.status_code == 204:
#     print("Авторизация успешна")

#     # Создайте клиент SOAP
#     wsdl_url = "https://bm-sup-5.boardmaps.com/publicapi/MeetingManagementService.svc?wsdl"
#     client = zeep.Client(wsdl=wsdl_url)

#     # Внедрите сессионную куку в клиент SOAP
#     transport = zeep.Transport(session=session)
#     client.transport = transport
    
#     meeting_data = {
#         "ActualDate": "2023-10-30T10:00:00",
#         "AgendaAgreementDate": "2023-10-25T12:00:00",
#         "Attendance": {
#             "AttendanceType": "InPerson"
#         },
#         "Name": "Заседание №1",
#         "Number": "1",
#         "PlaceAddress": "Адрес",
#         "PlaceName": "Место проведения",
#         "PlannedDate": "2023-11-15T14:00:00",
#         "MeetingType": {
#             "MeetingType": "Meeting"
#         },
#         "Initiator": {
#             "Id": "12345678-1234-1234-1234-123456789012"
#         }
#     }

#     # Вызовите метод создания заседания с использованием клиента SOAP и сессионной куки
#     result = client.service.Create(meeting_data)
#     print(result)

#     try:
#         result = client.service.Create(meeting_data)
#         if result:
#             print("Заседание успешно создано")
#         else:
#             print("Ошибка при создании заседания")
#             print(result)
#     except Exception as e:
#         print(f"Ошибка при вызове Create: {str(e)}")
# else:
#     print(f"Ошибка авторизации: {response_auth.status_code}")