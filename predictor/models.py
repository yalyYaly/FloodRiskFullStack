from django.db import models

class FloodReport(models.Model):
    rainfall = models.FloatField()
    river_level = models.FloatField()
    area_type = models.CharField(max_length=20)
    risk = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.risk} risk - {self.created_at:%Y-%m-%d %H:%M}"