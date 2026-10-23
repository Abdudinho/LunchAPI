import django_filters

from .models import Order


class OrderFilter(django_filters.FilterSet):
    # ?unassigned=true  -> yetkazuvchi tayinlanmagan buyurtmalar
    unassigned = django_filters.BooleanFilter(method="filter_unassigned")

    class Meta:
        model = Order
        fields = ["status", "restaurant", "user", "courier"]

    def filter_unassigned(self, qs, name, value):
        return qs.filter(courier__isnull=bool(value))
