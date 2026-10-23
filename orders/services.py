from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Order

S = Order.Status

TRANSITIONS = {
    S.PENDING: {S.CONFIRMED, S.CANCELLED},
    S.CONFIRMED: {S.PREPARING, S.CANCELLED},
    S.PREPARING: {S.READY},
    S.READY: {S.DELIVERING},
    S.DELIVERING: {S.DELIVERED},
}

ROLE_ALLOWED = {
    "chef": {S.CONFIRMED, S.CANCELLED, S.PREPARING, S.READY},
    "delivery": {S.DELIVERING, S.DELIVERED},
}



def change_status(order, new_status, actor):
    if actor.role != "admin":
        if new_status not in ROLE_ALLOWED.get(actor.role, set()):
            raise PermissionDenied("Bu statusni o'rnatishga ruxsatingiz yo'q.")
        if new_status not in TRANSITIONS.get(order.status, set()):
            raise ValidationError(f"'{order.status}' holatidan '{new_status}' ga o'tish mumkin emas.")
    if new_status == order.status:
        raise ValidationError("Buyurtma allaqachon shu holatda.")

    order.status = new_status
    order.save(update_fields=["status", "updated_at"])

    return order

