from django.db import models

class Suppliers(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

class Workers(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)


class Buyers(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
