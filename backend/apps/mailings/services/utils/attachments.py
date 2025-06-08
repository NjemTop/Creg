import os
import base64
import uuid
import io
from PIL import Image
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from django.conf import settings
from logger.log_config import scripts_info_logger, scripts_error_logger
from apps.mailings.services.integrations.yandex_disk import update_local_documentation


def clear_attachments_directory():
    attachments_root = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment')
    if os.path.isdir(attachments_root):
        for item in os.listdir(attachments_root):
            item_path = os.path.join(attachments_root, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    scripts_info_logger.info(f"Удалён файл: {item_path}")
                elif os.path.isdir(item_path):
                    os.rmdir(item_path)
                    scripts_info_logger.info(f"Удалена папка: {item_path}")
            except Exception as e:
                scripts_error_logger.error(f"Ошибка при удалении {item_path}: {e}")


def update_documentation(language, release_type, server_version, ipad_version, android_version, config):
    yandex_token = config["YANDEX_DISK"]["OAUTH-TOKEN"]
    yandex_folders = config["YANDEX_DISK_FOLDERS"]
    attachments_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment', language.upper())

    if not os.path.exists(attachments_dir):
        os.makedirs(attachments_dir)
        scripts_info_logger.info(f"Создана папка: {attachments_dir}")

    if not os.listdir(attachments_dir):
        scripts_info_logger.info(f"Документация для языка {language.upper()} не найдена, начинается загрузка...")
        update_local_documentation(yandex_token, yandex_folders, release_type, language,
                                   server_version, ipad_version, android_version)


def attach_images(msg, logger):
    images_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'Images')
    for image in os.listdir(images_dir):
        path = os.path.join(images_dir, image)
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                img = MIMEImage(f.read(), name=os.path.basename(path))
                img.add_header('Content-ID', f'<{image}>')
                msg.attach(img)
                logger.info(f"Прикреплено изображение: {image}")
        else:
            logger.error(f"Изображение не найдено: {path}")


def attach_files(msg, language, logger):
    attach_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment', language.upper())
    if os.path.isdir(attach_dir):
        for file in os.listdir(attach_dir):
            path = os.path.join(attach_dir, file)
            if os.path.isfile(path):
                with open(path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(path))
                    msg.attach(part)
                    logger.info(f"Файл прикреплён: {file}")
            else:
                logger.error(f"Файл не найден: {path}")


def embed_hidden_logo(html: str, language: str) -> str:
    try:
        image_path = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'Images', 'bm_logo.png')
        with Image.open(image_path) as img:
            pixels = img.load()
            for _ in range(50):
                x, y = uuid.uuid4().int % img.width, uuid.uuid4().int % img.height
                r, g, b = pixels[x, y][:3]
                pixels[x, y] = (r ^ 1, g ^ 1, b ^ 1)

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        html += f'<!-- ID письма: {uuid.uuid4()} -->'
        html += f'<img src="data:image/png;base64,{img_base64}" style="display:none;" alt="hidden logo"/>'
        return html
    except Exception as e:
        scripts_error_logger.error(f"Ошибка вставки скрытого логотипа: {e}")
        return html
