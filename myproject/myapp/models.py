from django.db import models

# Create your models here.

class VirusInfo(models.Model):

    class Meta:
        db_table = 'virus_info'

    virus_name = models.CharField(max_length=255)
    aliases = models.TextField()
    discovery_date = models.DateField()
    origin = models.CharField(max_length=255)
    length = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    risk_assessment = models.CharField(max_length=255)
    minimum_engine = models.CharField(max_length=255)
    minimum_dat = models.CharField(max_length=255)
    dat_release_date = models.DateField()
    virus_characteristics = models.TextField()
    symptoms = models.TextField()
    method_of_infection = models.TextField()
    removal_instructions = models.TextField()

    def __str__(self):
        return self.virus_name