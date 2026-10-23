from .models import Order


def orders_for(user):
    """Rolga qarab ko'rinadigan buyurtmalar (object-level ruxsat shu yerda hal bo'ladi)."""
    qs = Order.objects.select_related("restaurant", "user", "courier").prefetch_related("items")
    role = user.role
    if role == "admin":
        return qs
    if role == "employee":
        return qs.filter(user=user)
    if role == "chef":
        return qs.filter(restaurant__owner=user)
    if role == "delivery":
        return qs.filter(courier=user)
    return qs.none()
