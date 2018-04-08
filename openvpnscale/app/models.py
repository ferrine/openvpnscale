from django.db import models
from django.core import validators
import django.contrib.auth.models
from django.conf import settings


class Host(models.Model):
    ipv4 = models.GenericIPAddressField(
        protocol='IPv4',
        primary_key=True
    )
    hostname = models.CharField(
        max_length=50,
        blank=True
    )


class VPNServer(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    port = models.IntegerField(
        default=1142,
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(65535),
        ],
    )
    protocol = models.CharField(
        default='udp',
        max_length=3,
        choices=[('udp', 'udp'), ('tcp', 'tcp')]
    )

    class Meta:
        unique_togeter = (('host', 'port', 'protocol'), )


class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ManyToManyField(django.contrib.auth.models.Group)
    name = models.CharField(
        max_length=50,
        validators=[validators.validate_slug],
        primary_key=True
    )
    active = models.BooleanField(default=False)
