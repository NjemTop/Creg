"""Helpers to send a test mailing using :class:`EmailSender`."""

from apps.mailings.services.base.email_sender import EmailSender


def send_test_email(email, release_type, server_version='', ipad_version='', android_version='', language='ru'):
    """Send a single test email."""
    sender = EmailSender(
        emails=[email],
        mailing_type="standard_mailing",
        release_type=release_type,
        server_version=server_version,
        ipad_version=ipad_version,
        android_version=android_version,
        language=language,
    )
    return sender.send_email()
