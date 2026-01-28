from django.db import models

class Suppliers(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive')]

    profile_picture = models.ImageField(upload_to='suppliers/profile/', blank=True, null=True)
    document = models.FileField(upload_to='suppliers/documents/', blank=True, null=True)

    password = models.CharField(max_length=10)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)

    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)

    mbno = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)


class Workers(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive')]

    profile_picture = models.ImageField(upload_to='worker/profile/', blank=True, null=True)
    document = models.FileField(upload_to='worker/documents/', blank=True, null=True)

    password = models.CharField(max_length=10)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)

    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)

    mbno = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)




