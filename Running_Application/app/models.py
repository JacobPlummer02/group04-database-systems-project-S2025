from django.db import models
from django.contrib.auth.models import User

class Meet(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.date})"

class RaceResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meet = models.ForeignKey(Meet, on_delete=models.CASCADE, related_name='results')
    event_name = models.CharField(max_length=200)
    result = models.CharField(max_length=20)
    place = models.IntegerField()

    def __str__(self):
        return f"{self.user.email} - {self.event_name} - {self.result}"
