# Generated by Django 4.2 on 2023-05-09 12:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_alter_bmserverscard_client_card_techaccountcard'),
    ]

    operations = [
        migrations.RenameField(
            model_name='techaccountcard',
            old_name='client_id',
            new_name='client_card',
        ),
    ]