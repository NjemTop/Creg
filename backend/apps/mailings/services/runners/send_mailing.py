"""Helpers to send production mailings using :class:`EmailSender`."""

from apps.mailings.services.base.email_sender import EmailSender


def send_mailing(emails, release_type, server_version='', ipad_version='', android_version='', language='ru'):
    """Send a mailing to the provided list of emails.

    Parameters mirror the ones used by :class:`EmailSender`. The function
    instantiates the sender and calls ``send_email``. ``emails`` can be a single
    address or an iterable of addresses."""

    sender = EmailSender(
        emails=emails,
        mailing_type="standard_mailing",
        release_type=release_type,
        server_version=server_version,
        ipad_version=ipad_version,
        android_version=android_version,
        language=language,
    )
    return sender.send_email()
