from django.db.models import Q

from .models import MenuItem, Restaurant


def _role(user):
    return user.role if user.is_authenticated else None


def visible_restaurants(user):
    if _role(user) == "admin":
        return Restaurant.objects.all()
    q = Q(is_active=True)
    if _role(user) == "chef":
        q |= Q(owner=user)
    return Restaurant.objects.filter(q)


def visible_menu_items(user):
    qs = MenuItem.objects.select_related("restaurant")
    if _role(user) == "admin":
        return qs
    q = Q(is_available=True, restaurant__is_active=True)
    if _role(user) == "chef":
        q |= Q(restaurant__owner=user)
    return qs.filter(q)
