from django.db import models
from django.conf import settings
from netbox.models import NetBoxModel


def get_currency_choices():
    """Get currency choices from plugin configuration."""
    config = settings.PLUGINS_CONFIG.get("netbox_cesnet_service_path_plugin", {})
    return config.get(
        "currencies",
        [
            ("CZK", "Czech Koruna"),
            ("EUR", "Euro"),
            ("USD", "US Dollar"),
        ],
    )


def get_default_currency():
    """Get default currency from plugin configuration."""
    config = settings.PLUGINS_CONFIG.get("netbox_cesnet_service_path_plugin", {})
    return config.get("default_currency", "CZK")


class SegmentFinancialInfo(NetBoxModel):
    segment = models.OneToOneField(
        "cesnet_service_path_plugin.Segment", on_delete=models.CASCADE, related_name="financial_info"
    )

    monthly_charge = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Fixed monthly fee for the service lease"
    )

    charge_currency = models.CharField(
        max_length=3,
        choices=get_currency_choices,
        default=get_default_currency,
        help_text="Currency for all charges",
    )

    non_recurring_charge = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, help_text="One-time setup or installation fee"
    )

    commitment_period_months = models.PositiveIntegerField(
        blank=True, null=True, help_text="Number of months the contract cannot be terminated"
    )

    notes = models.TextField(blank=True, help_text="Additional financial notes")

    @property
    def total_commitment_cost(self):
        """Calculate total cost over commitment period."""
        if self.commitment_period_months and self.monthly_charge:
            return self.commitment_period_months * self.monthly_charge
        return None

    @property
    def total_cost_including_setup(self):
        """Total cost including non-recurring charge."""
        from decimal import Decimal

        total = self.total_commitment_cost or Decimal("0")
        if self.non_recurring_charge:
            total += self.non_recurring_charge
        return total if total > 0 else None

    class Meta:
        ordering = ("segment",)
