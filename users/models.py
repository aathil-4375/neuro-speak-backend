# backend/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    slmc_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_doctor = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"