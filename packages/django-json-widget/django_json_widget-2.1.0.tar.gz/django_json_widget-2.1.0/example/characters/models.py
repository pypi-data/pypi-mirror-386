from django.db.models import JSONField
from django.db import models


class Character(models.Model):
    name = models.CharField(max_length=200)
    data = JSONField()
    other_data = JSONField()

    def __str__(self):  # __unicode__ on Python 2
        return self.name
