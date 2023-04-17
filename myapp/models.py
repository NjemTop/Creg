from django.db import models

class Client(models.Model):
    client_name = models.CharField(max_length=200)
    contact_status = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.client_name

class Favicon(models.Model):
    file = models.FileField(upload_to='media/favicons')

    def __str__(self):
        return self.file.name
