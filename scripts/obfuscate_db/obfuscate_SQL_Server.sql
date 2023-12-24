-- Обновляем почты
UPDATE boardmaps_Users SET Email = 'example@example.com';

-- Делаем телефоны пустыми
UPDATE boardmaps_Users SET Phone = NULL;

-- Обновляем данные в boardmaps_HoldingSettings
UPDATE boardmaps_HoldingSettings
SET Value = ''
WHERE Name IN (
    'onlinepresentation.pspdfdashboardpassword',
    'filestorage.storage.location',
    'onlinepresentation.pspdfdashboardlogin',
    'email.smtp.host',
    'email.smtp.username',
    'email.smtp.password',
    'email.smtp.port',
    'client.weburl',
    'client.serverurl',
    'webapps.webappsserverurl',
    'email.fromaddress',
    'client.holdingadmin.passwordhash',
    'onlinepresentation.pspdfserverurl',
    'client.webexternalurl',
    'client.serverexternalurl',
    'exchange.credentials.username',
    'exchange.credentials.password',
    'exchange.credentials.email'
);

-- Обновляем данные в boardmaps_SystemSettings
UPDATE boardmaps_SystemSettings
SET Value = ''
WHERE Name IN (
    'fulltextsearch.connectionstring',
    'security.authentication.oauth.authority',
    'limesurvey.serverurl',
    'azure.storage.siteurl',
    'sharepoint.siteurl',
    'client.weburl',
    'filestorage.storage.location',
    'webapps.webappsserverurl',
    'onlinepresentation.pspdfserverurl',
    'onlinepresentation.pspdfapiauthtoken',
    'phonebook.defaultuserpassword',
    'client.serverurl',
    'sharepoint.authentication.username',
    'activedirectoryintegration.domain',
    'sharepoint.authentication.password',
    'activedirectoryintegration.figurantsgroupdistinguishedname',
    'activedirectoryintegration.usersgroupdistinguishedname',
    'client.webexternalurl',
    'client.serverexternalurl'
);

-- Обновляем различные настройки на false
UPDATE boardmaps_HoldingSettings
SET Value = 'false'
WHERE Name IN (
    'email.enabled',
    'email.smtp.enablessl',
    'webapps.enabled',
    'push.apnsconnection.isenabled',
    'exchange.isenabled'
);

UPDATE boardmaps_SystemSettings
SET Value = 'false'
WHERE Name IN (
    'activedirectoryintegration.enabled',
    'security.authentication.oauth.enabled',
    'push.apnsconnection.isenabled'
);

-- Удаляем связанные записи и сами записи из различных таблиц
DELETE FROM boardmaps_DeviceUsers WHERE DeviceId IN (SELECT Id FROM boardmaps_Devices);
DELETE FROM boardmaps_Devices;

DELETE FROM boardmaps_DocumentFileReads WHERE DocumentFileId IN (SELECT Id FROM boardmaps_DocumentFiles);
DELETE FROM boardmaps_DocumentFiles WHERE FileId IN (SELECT Id FROM boardmaps_Files);

DELETE FROM boardmaps_Documents WHERE FileId IN (SELECT Id FROM boardmaps_Files);
DELETE FROM boardmaps_LogArchive WHERE FileId IN (SELECT Id FROM boardmaps_Files);
DELETE FROM boardmaps_BaseAnnotations WHERE FileId IN (SELECT Id FROM boardmaps_Files);
DELETE FROM boardmaps_Files;

DELETE FROM boardmaps_ActiveDirectorySettings;
