from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase

from users.models import User


class FullFlowTest(APITestCase):
    def setUp(self):
        cache.clear()
        mk = lambda e, r: User.objects.create_user(e, "Passw0rd!123", name=r, role=r, office_address="Ofis 3-qavat")
        self.admin, self.chef, self.chef2 = mk("a@x.uz", "admin"), mk("c@x.uz", "chef"), mk("c2@x.uz", "chef")
        self.courier, self.emp, self.emp2 = mk("d@x.uz", "delivery"), mk("e@x.uz", "employee"), mk("e2@x.uz", "employee")

    def as_(self, user):
        self.client.force_authenticate(user)
        return self.client

    def test_register_login_logout(self):
        self.client.force_authenticate(None)
        r = self.client.post("/api/auth/register", {"name": "Ali", "email": "ali@x.uz", "password": "Passw0rd!123",
                                                     "role": "admin"}, format="json")
        self.assertEqual(r.status_code, 400)  # admin sifatida ro'yxatdan o'tib bo'lmaydi
        r = self.client.post("/api/auth/register", {"name": "Ali", "email": "ali@x.uz", "password": "Passw0rd!123"},
                             format="json")
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/auth/login", {"email": "ali@x.uz", "password": "Passw0rd!123"}, format="json")
        self.assertEqual(r.status_code, 200)
        access, refresh = r.data["access"], r.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(self.client.get("/api/auth/profile").data["email"], "ali@x.uz")
        self.assertEqual(self.client.post("/api/auth/logout", {"refresh": refresh}, format="json").status_code, 205)
        self.assertEqual(self.client.post("/api/auth/refresh", {"refresh": refresh}, format="json").status_code, 401)
        self.assertEqual(self.client.get("/api/users").status_code, 403)

    def test_full_order_flow(self):
        # admin restoran yaratadi, oshpaz menyu qo'shadi
        r = self.as_(self.admin).post("/api/restaurants", {"name": "Osh markazi", "owner": self.chef.id}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        rid = r.data["id"]
        r = self.as_(self.chef).post("/api/menu/items", {"restaurant": rid, "name": "Osh", "price": "35000",
                                                        "category": "Asosiy"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        mid = r.data["id"]
        # boshqa oshpaz bu restoranga menyu qo'sha olmaydi
        r = self.as_(self.chef2).post("/api/menu/items", {"restaurant": rid, "name": "X", "price": "1"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.as_(self.chef2).put(f"/api/menu/items/{mid}", {"name": "hack", "price": "1",
                                                                             "restaurant": rid}, format="json").status_code, 403)
        # ommaviy ko'rish
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"/api/restaurants/{rid}/menu").data[0]["name"], "Osh")
        self.assertEqual(self.client.get("/api/menu/categories").data, ["Asosiy"])

        # xodim buyurtma beradi
        r = self.as_(self.emp).post("/api/orders", {"restaurant": rid, "items": [{"menu_item": mid, "quantity": 2}]},
                                    format="json")
        self.assertEqual(r.status_code, 201, r.data)
        oid = r.data["id"]
        self.assertEqual(r.data["total_amount"], "70000.00")
        self.assertEqual(r.data["delivery_address"], "Ofis 3-qavat")
        # boshqa xodim ko'rolmaydi, ro'yxat faqat admin
        self.assertEqual(self.as_(self.emp2).get(f"/api/orders/{oid}").status_code, 404)
        self.assertEqual(self.as_(self.emp).get("/api/orders").status_code, 403)
        self.assertEqual(self.as_(self.emp).get(f"/api/users/{self.emp2.id}/orders").status_code, 403)
        self.assertEqual(self.as_(self.emp).get(f"/api/users/{self.emp.id}/orders").data["count"], 1)
        # xodim status o'zgartira olmaydi
        self.assertEqual(self.as_(self.emp).put(f"/api/orders/{oid}/status", {"status": "confirmed"},
                                                format="json").status_code, 403)
        # to'lov
        r = self.as_(self.emp).post(f"/api/orders/{oid}/payments", {"payment_method": "cash"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        pid = r.data["id"]
        self.assertEqual(self.as_(self.emp).post(f"/api/orders/{oid}/payments", {"payment_method": "card"},
                                                 format="json").status_code, 400)
        self.assertEqual(self.as_(self.emp).put(f"/api/payments/{pid}/confirm").status_code, 403)

        # oshpaz statuslar
        c = self.as_(self.chef)
        self.assertEqual(c.put(f"/api/orders/{oid}/status", {"status": "ready"}, format="json").status_code, 400)
        for s in ("confirmed", "preparing", "ready"):
            self.assertEqual(c.put(f"/api/orders/{oid}/status", {"status": s}, format="json").status_code, 200)
        self.assertEqual(c.put(f"/api/orders/{oid}/status", {"status": "delivered"}, format="json").status_code, 403)
        # boshqa oshpaz bu buyurtmani ko'rolmaydi
        self.assertEqual(self.as_(self.chef2).get(f"/api/orders/{oid}").status_code, 404)

        # yetkazuvchi tayinlash
        self.assertEqual(self.as_(self.emp).get("/api/orders/my").data["count"], 1)
        self.assertEqual(self.as_(self.chef).get(f"/api/restaurants/{rid}/orders").data["count"], 1)
        self.assertEqual(self.as_(self.chef2).get(f"/api/restaurants/{rid}/orders").data["count"], 0)
        self.assertEqual(self.as_(self.admin).get("/api/orders?status=ready&unassigned=true").data["count"], 1)
        self.assertEqual(self.as_(self.courier).get("/api/orders/my").data["count"], 0)
        r = self.as_(self.admin).put(f"/api/orders/{oid}/courier", {"courier": self.courier.id}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(self.as_(self.courier).get("/api/orders/my").data["count"], 1)
        self.assertEqual(self.as_(self.admin).get("/api/orders?unassigned=true").data["count"], 0)
        d = self.as_(self.courier)
        self.assertEqual(d.put(f"/api/orders/{oid}/status", {"status": "delivering"}, format="json").status_code, 200)
        t = self.as_(self.emp).get(f"/api/orders/{oid}/track").data
        self.assertEqual((t["status"], t["courier"]["id"]), ("delivering", self.courier.id))
        self.assertEqual(self.as_(self.courier).put(f"/api/orders/{oid}/status", {"status": "delivered"},
                                                    format="json").status_code, 200)
        # to'lovni admin tasdiqlaydi
        r = self.as_(self.admin).put(f"/api/payments/{pid}/confirm", {"transaction_id": "T1"}, format="json")
        self.assertEqual(r.data["status"], "completed")
        self.assertEqual(self.as_(self.chef).get(f"/api/orders/{oid}/payments").status_code, 200)
        self.assertEqual(self.as_(self.courier).get(f"/api/orders/{oid}/payments").status_code, 403)

    def test_employee_edit_delete_rules(self):
        rest = self.as_(self.admin).post("/api/restaurants", {"name": "R", "owner": self.chef.id}, format="json").data["id"]
        mid = self.as_(self.chef).post("/api/menu/items", {"restaurant": rest, "name": "Lag'mon", "price": "25000"},
                                       format="json").data["id"]
        later = (timezone.now() + timedelta(hours=2)).isoformat()
        oid = self.as_(self.emp).post("/api/orders", {"restaurant": rest, "delivery_time": later,
                                                      "items": [{"menu_item": mid, "quantity": 1}]}, format="json").data["id"]
        r = self.as_(self.emp).put(f"/api/orders/{oid}", {"delivery_address": "Yangi manzil", "status": "delivered"},
                                   format="json")
        self.assertEqual(r.data["delivery_address"], "Yangi manzil")
        self.assertEqual(r.data["status"], "pending")  # status PUT orqali o'zgarmaydi
        self.as_(self.chef).put(f"/api/orders/{oid}/status", {"status": "confirmed"}, format="json")
        self.assertEqual(self.as_(self.emp).put(f"/api/orders/{oid}", {"delivery_address": "Z"}, format="json").status_code, 403)
        self.assertEqual(self.as_(self.emp).delete(f"/api/orders/{oid}").status_code, 403)
        self.assertEqual(self.as_(self.admin).delete(f"/api/orders/{oid}").status_code, 204)
