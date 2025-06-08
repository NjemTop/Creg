from apps.mailings.services.base.email_sender import EmailSender
from apps.mailings.services.utils.attachments import clear_attachments_directory


def send_test_email(emails, mailing_type, release_type,
                    server_version=None, ipad_version=None, android_version=None, language='ru'):
    clear_attachments_directory()
    sender = EmailSender(
        emails=emails,
        mailing_type=mailing_type,
        release_type=release_type,
        server_version=server_version,
        ipad_version=ipad_version,
        android_version=android_version,
        language=language
    )
    return sender.send_email()
