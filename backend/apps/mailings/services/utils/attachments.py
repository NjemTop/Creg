import os
import uuid
import random
import base64
import io
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from PIL import Image
from django.conf import settings
from apps.mailings.services.integrations.yandex_disk import update_local_documentation

# logging
import logging

logger = logging.getLogger(__name__)

def attach_images(msg, logger=None):
    """Attach images from the HTML/Images folder to the email message."""
    images_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'Images')
    for image in os.listdir(images_dir):
        image_path = os.path.join(images_dir, image)
        if os.path.isfile(image_path):
            with open(image_path, 'rb') as f:
                img = MIMEImage(f.read(), name=os.path.basename(image))
                img.add_header('Content-ID', '<{}>'.format(image))
                msg.attach(img)
                if logger:
                    logger.info("Изображение %s успешно прикреплено.", image)
        else:
            if logger:
                logger.error("Изображение %s не найдено по пути %s.", image, image_path)

def attach_files(msg, language, logger=None):
    """Attach downloaded PDF files for the given language."""
    attachments_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment', language.upper())
    files_attached = False
    if os.path.isdir(attachments_dir):
        for attachment in os.listdir(attachments_dir):
            attachment_path = os.path.join(attachments_dir, attachment)
            if os.path.isfile(attachment_path):
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
                    msg.attach(part)
                    files_attached = True
                    if logger:
                        logger.info("Файл %s успешно прикреплен.", attachment)
            else:
                if logger:
                    logger.error("Файл %s не найден по пути %s.", attachment, attachment_path)
    if not files_attached and logger:
        logger.error("Ни один файл не был найден для прикрепления.")

def update_documentation(language, release_type, server_version, ipad_version, android_version, config):
    """Download documentation from Yandex.Disk if it's not present locally."""
    yandex_token = config["YANDEX_DISK"]["OAUTH-TOKEN"]
    yandex_folders = config["YANDEX_DISK_FOLDERS"]
    attachments_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment', language.upper())

    try:
        if not os.path.exists(attachments_dir):
            os.makedirs(attachments_dir)
            logger.info("Создана директория для документации: %s", attachments_dir)
    except OSError as error_message:
        logger.error("Ошибка при создании директории %s: %s", attachments_dir, str(error_message))
        raise

    if not os.listdir(attachments_dir):
        logger.info(
            "Документация для языка %s и версии %s не найдена локально, начинается скачивание...",
            language.upper(), server_version)
        update_local_documentation(
            yandex_token, yandex_folders, release_type, language, server_version, ipad_version, android_version)
    else:
        logger.info(
            "Документация для языка %s и версии %s уже скачана, повторное скачивание не требуется.",
            language.upper(), server_version)

def embed_hidden_logo(html, language):
    """Embed a hidden logo and unique id into the rendered HTML."""
    try:
        unique_id = uuid.uuid4()
        image_path = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'Images', 'bm_logo.png')
        with Image.open(image_path) as img:
            pixels = img.load()
            for _ in range(50):
                x = random.randint(0, img.width - 1)
                y = random.randint(0, img.height - 1)
                pixel = pixels[x, y]
                if len(pixel) == 3:
                    r, g, b = pixel
                    pixels[x, y] = (r ^ 1, g ^ 1, b ^ 1)
                elif len(pixel) == 4:
                    r, g, b, a = pixel
                    pixels[x, y] = (r ^ 1, g ^ 1, b ^ 1, a)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        html += f'<!-- Скрытый уникальный идентификатор письма: {unique_id} -->'
        html += f'<p style="display:none;">ID письма: {unique_id}</p>'
        html += f'<img src="data:image/png;base64,{img_base64}" style="display:none;" alt="hidden logo"/>'
    except Exception as e:
        logger.error("Ошибка при встраивании скрытого логотипа: %s", str(e))
    return html
