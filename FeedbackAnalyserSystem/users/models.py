from django.db import models

class User(models.Model):
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    phone = models.IntegerField(null=True, blank=True)
    slug = models.SlugField(default="", null=False)

    def __str__(self):
        return f"{self.firstname} {self.lastname}"

class Feedback(models.Model):
    source_id = models.CharField(max_length=100)
    external_id = models.CharField(max_length=100)
    text = models.TextField()
    category = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    send_time = models.DateTimeField(null=True, blank=True)
    meta_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.source_id} - {self.external_id}"