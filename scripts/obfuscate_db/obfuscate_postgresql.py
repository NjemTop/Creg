import psycopg2
from dotenv import load_dotenv
import os
from .info_k8s import get_postgresql_info
import logging


logger = logging.getLogger(__name__)

class DatabaseCleanerPostgreSQL:
    def __init__(self, service_url):
        load_dotenv()  # Загрузка переменных окружения из .env файла

        self.service_url = service_url
        self.admin_username = os.getenv('ROOT_USERNAME')
        self.admin_password = os.getenv('ROOT_PASSWORD')

        # Получаем данные для подключения к PostgreSQL
        postgres_info = get_postgresql_info(self.service_url, self.admin_username, self.admin_password)
        if postgres_info:
            self.database = postgres_info['postgres_db']
            self.username = postgres_info['postgres_user']
            self.password = postgres_info['postgres_password']
            self.pod_name = postgres_info['pod_name']
        else:
            logger.error(f'Не удалось получить информацию о базе данных PostgreSQL')
            raise ValueError("Не удалось получить информацию о базе данных PostgreSQL")

        # Создание строки подключения к PostgreSQL
        self.connection_string = f"dbname={self.database} user={self.username} password={self.password} host={self.service_url} port=5432"


    def connect(self):
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.cursor = self.conn.cursor()
        except Exception as error_message:
            logger.error(f'Ошибка подключения к базе данных: {error_message}')
            self.cursor = None
            self.conn = None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def clean(self):
        if not self.cursor:
            error_message = 'Не установлено соединение с базой данных.'
            logger.error(error_message)
            raise ValueError(error_message)  # Выбрасываем исключение

        try:
            # Обновляем почты
            self.cursor.execute("UPDATE boardmaps_Users SET Email='example@example.com'")
            
            # Делаем телефоны пустыми
            self.cursor.execute("UPDATE boardmaps_Users SET Phone=NULL")
            
            # Обновляем данные в boardmaps_HoldingSettings
            settings_to_nullify_in_holding = [
                "onlinepresentation.pspdfdashboardpassword",
                "onlinepresentation.pspdfdashboardlogin",
                "email.smtp.host",
                "email.smtp.username",
                "email.smtp.password",
                "email.smtp.port",
                "client.weburl",
                "client.serverurl",
                "webapps.webappsserverurl",
                "email.fromaddress",
                "client.holdingadmin.passwordhash",
                "onlinepresentation.pspdfserverurl",
                "client.webexternalurl",
                "client.serverexternalurl",
                "exchange.credentials.username",
                "exchange.credentials.password",
                "exchange.credentials.email"
            ]
            for setting in settings_to_nullify_in_holding:
                self.cursor.execute(f"UPDATE boardmaps_HoldingSettings SET Value='' WHERE Name='{setting}'")
                
            # Обновляем данные в boardmaps_SystemSettings
            settings_to_nullify_in_system = [
                "fulltextsearch.connectionstring",
                "security.authentication.oauth.authority",
                "limesurvey.serverurl",
                "azure.storage.siteurl",
                "sharepoint.siteurl",
                "client.weburl",
                "filestorage.storage.location",
                "webapps.webappsserverurl",
                "onlinepresentation.pspdfserverurl",
                "onlinepresentation.pspdfapiauthtoken",
                "phonebook.defaultuserpassword",
                "client.serverurl",
                "sharepoint.authentication.username",
                "activedirectoryintegration.domain",
                "sharepoint.authentication.password",
                "activedirectoryintegration.figurantsgroupdistinguishedname",
                "activedirectoryintegration.usersgroupdistinguishedname",
                "client.webexternalurl",
                "client.serverexternalurl"
            ]
            for setting in settings_to_nullify_in_system:
                self.cursor.execute(f"UPDATE boardmaps_SystemSettings SET Value='' WHERE Name='{setting}'")
            
            # Обновляем настройку "email.enabled" на false
            self.cursor.execute("UPDATE boardmaps_HoldingSettings SET Value='false' WHERE Name='email.enabled'")
            
            # Обновляем настройку "email.smtp.enablessl" на false
            self.cursor.execute("UPDATE boardmaps_HoldingSettings SET Value='false' WHERE Name='email.smtp.enablessl'")

            # Обновляем настройку "activedirectoryintegration.enabled" на false
            self.cursor.execute("UPDATE boardmaps_SystemSettings SET Value='false' WHERE Name='activedirectoryintegration.enabled'")

            # Обновляем настройку "security.authentication.oauth.enabled" на false
            self.cursor.execute("UPDATE boardmaps_SystemSettings SET Value='false' WHERE Name='security.authentication.oauth.enabled'")

            # Обновляем настройку "webapps.enabled" на false
            self.cursor.execute("UPDATE boardmaps_HoldingSettings SET Value='false' WHERE Name='webapps.enabled'")

            # Обновляем настройку "push.apnsconnection.isenabled" на false
            self.cursor.execute("UPDATE boardmaps_HoldingSettings SET Value='false' WHERE Name='push.apnsconnection.isenabled'")

            # Обновляем настройку "push.apnsconnection.isenabled" на false
            self.cursor.execute("UPDATE boardmaps_SystemSettings SET Value='false' WHERE Name='push.apnsconnection.isenabled'")

            # Обновляем настройку "exchange.isenabled" на false
            self.cursor.execute("UPDATE boardmaps_HoldingSettings SET Value='false' WHERE Name='exchange.isenabled'")
                
            # Удаляем связанные записи из boardmaps_DeviceUsers
            self.cursor.execute("DELETE FROM boardmaps_DeviceUsers WHERE DeviceId IN (SELECT Id FROM boardmaps_Devices)")

            # Удаляем все записи из boardmaps_Devices
            self.cursor.execute("DELETE FROM boardmaps_Devices")

            # Удаляем связанные записи из boardmaps_DocumentFileReads
            self.cursor.execute("DELETE FROM boardmaps_DocumentFileReads WHERE DocumentFileId IN (SELECT Id FROM boardmaps_DocumentFiles)")

            # Удаляем связанные записи из boardmaps_DocumentFiles
            self.cursor.execute("DELETE FROM boardmaps_DocumentFiles WHERE FileId IN (SELECT Id FROM boardmaps_Files)")

            # Удаляем связанные записи из boardmaps_Documents
            self.cursor.execute("DELETE FROM boardmaps_Documents WHERE FileId IN (SELECT Id FROM boardmaps_Files)")

            # Удаляем связанные записи из boardmaps_LogArchive
            self.cursor.execute("DELETE FROM boardmaps_LogArchive WHERE FileId IN (SELECT Id FROM boardmaps_Files)")

            # Удаляем связанные записи из boardmaps_BaseAnnotations
            self.cursor.execute("DELETE FROM boardmaps_BaseAnnotations WHERE FileId IN (SELECT Id FROM boardmaps_Files)")

            # Удаляем все записи из boardmaps_Files
            self.cursor.execute("DELETE FROM boardmaps_Files")

            # Удаляем все записи из boardmaps_ActiveDirectorySettings
            self.cursor.execute("DELETE FROM boardmaps_ActiveDirectorySettings")

            self.conn.commit()
            logger.info(f'Данные успешно обновлены!')
        except Exception as error_message:
            logger.error(f'Ошибка при обновлении: {error_message}')
            raise
