-- Обновляем почты
UPDATE public."boardmaps_Users" SET "Email" = 'example@example.com';

-- Делаем телефоны пустыми
UPDATE public."boardmaps_Users" SET "Phone" = NULL;

-- Обновляем данные в boardmaps_HoldingSettings
UPDATE public."boardmaps_HoldingSettings"
SET "Value" = ''
WHERE "Name" IN (
    'email.fromaddress',
    'email.smtp.host',
    'email.smtp.username',
    'email.smtp.password',
    'email.smtp.port',
    'client.weburl',
    'client.serverurl',
    'client.serverexternalurl',
    'client.webexternalurl',
    'client.holdingadmin.passwordhash',
    'webapps.webappsserverurl',
    'exchange.credentials.username',
    'exchange.credentials.password',
    'exchange.credentials.email',
    'lync.lyncservice.address',
    'lync.securitytokenservice.address',
    'lync.credentials.username',
    'lync.credentials.password',
    'smpp.host',
    'smpp.port',
    'smpp.systemid',
    'smpp.password',
    'smpp.sourceaddress'
);

-- Обновляем данные в boardmaps_SystemSettings
UPDATE public."boardmaps_SystemSettings"
SET "Value" = ''
WHERE "Name" IN (
    'fulltextsearch.connectionstring',
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
    'security.authentication.oauth.authority',
    'security.authentication.oauth.clientid',
    'sharepoint.authentication.username',
    'sharepoint.authentication.password',
    'activedirectoryintegration.domain',
    'activedirectoryintegration.figurantsgroupdistinguishedname',
    'activedirectoryintegration.usersgroupdistinguishedname',
    'client.webexternalurl',
    'client.serverexternalurl'
);

-- Указываем интеграции в положение false
UPDATE public."boardmaps_HoldingSettings"
SET "Value" = 'false'
WHERE "Name" IN (
    'email.enabled',
    'email.smtp.enablessl',
    'webapps.enabled',
    'push.apnsconnection.isenabled',
    'exchange.isenabled',
    'lync.isenabled',
    'system.featuretoggle.smppintegrationenabled',
    'security.digitalsignature.isenabled'
);

UPDATE public."boardmaps_SystemSettings"
SET "Value" = 'false'
WHERE "Name" IN (
    'activedirectoryintegration.enabled',
    'security.authentication.oauth.enabled',
    'push.apnsconnection.isenabled'
);

-- Удаляем связанные записи и сами записи из различных таблиц
DELETE FROM public."boardmaps_DeviceUsers" WHERE "DeviceId" IN (SELECT "Id" FROM public."boardmaps_Devices");
DELETE FROM public."boardmaps_Devices";

DELETE FROM public."boardmaps_DocumentFileReads" WHERE "DocumentFileId" IN (SELECT "Id" FROM public."boardmaps_DocumentFiles");
DELETE FROM public."boardmaps_DocumentFiles" WHERE "FileId" IN (SELECT "Id" FROM public."boardmaps_Files");

DELETE FROM public."boardmaps_Documents" WHERE "FileId" IN (SELECT "Id" FROM public."boardmaps_Files");
DELETE FROM public."boardmaps_LogArchive" WHERE "FileId" IN (SELECT "Id" FROM public."boardmaps_Files");
DELETE FROM public."boardmaps_BaseAnnotations" WHERE "FileId" IN (SELECT "Id" FROM public."boardmaps_Files");
DELETE FROM public."boardmaps_Files";

DELETE FROM public."boardmaps_ActiveDirectorySettings";
