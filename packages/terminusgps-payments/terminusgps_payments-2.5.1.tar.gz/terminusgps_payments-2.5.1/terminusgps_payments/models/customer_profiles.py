from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class CustomerProfile(models.Model):
    """An Authorizenet customer profile."""

    id = models.BigIntegerField(primary_key=True)
    """Authorizenet customer profile id."""
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    """Associated user."""

    class Meta:
        verbose_name = _("customer profile")
        verbose_name_plural = _("customer profiles")

    def __str__(self) -> str:
        """Returns the customer's username."""
        return self.user.username

    def get_absolute_url(self) -> str:
        return reverse(
            "terminusgps_payments:detail customer profile",
            kwargs={"profile_pk": self.pk},
        )

    @property
    def merchant_id(self) -> str:
        """Merchant-designated id for Authorizenet API calls."""
        return str(self.user.pk)

    @property
    def email(self) -> str:
        """Customer email address."""
        return self.user.email

    @property
    def description(self) -> str:
        """Customer full name (first + last)."""
        return f"{self.user.first_name} {self.user.last_name}"
