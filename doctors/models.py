from django.db import models
from django.contrib.auth.hashers import make_password

class Doctor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    slmc_id = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # Store hashed passwords later!
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)  # Hash the password before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (SLMC: {self.slmc_id})"

