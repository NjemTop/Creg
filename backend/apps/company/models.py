from django.db import models


class Employee(models.Model):
    """Сотрудники компании"""
    ROLE_CHOICES = [
        ('Менеджер', 'Менеджер'),
        ('Техподдержка', 'Техподдержка'),
        ('Разработчик', 'Разработчик'),
        ('Администратор', 'Администратор'),
    ]

    first_name = models.CharField(verbose_name="Имя", max_length=100)
    last_name = models.CharField(verbose_name="Фамилия", max_length=100)
    email = models.EmailField(verbose_name="Почта", unique=True)
    role = models.CharField(verbose_name="Роль", max_length=50, choices=ROLE_CHOICES)
    
    keycloak_id = models.CharField(verbose_name="ID в Keycloak", max_length=255, unique=True, blank=True, null=True)  # Связь с Keycloak
    agent_id = models.IntegerField(verbose_name="ID в тикет системе", null=True, blank=True)
    telegram_id = models.IntegerField(verbose_name="Telegram ID", blank=True, null=True)
    telegram_username = models.CharField(verbose_name="Telegram Username", max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        db_table = "employee"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"


class EmployeeNotificationSettings(models.Model):
    """Настройки уведомлений сотрудников"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="notification_settings", verbose_name="Сотрудник")
    
    test_automatic_email = models.BooleanField(verbose_name="Тестовая отправка рассылки", default=False)
    new_client = models.BooleanField(verbose_name="Уведомления о новых клиентах", default=False)

    class Meta:
        verbose_name = "Настройки уведомлений сотрудника"
        verbose_name_plural = "Настройки уведомлений сотрудников"
        db_table = "employee_notification_settings"

    def __str__(self):
        return f"Настройки {self.employee.first_name} {self.employee.last_name}"
