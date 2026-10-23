from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    roles: tuple = ()

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.role in self.roles)


def roles(*names):
    return type("Has_" + "_".join(names), (HasRole,), {"roles": names})


IsAdmin = roles("admin")
IsEmployee = roles("employee")
IsEmployeeOrAdmin = roles("employee", "admin")
IsChefOrAdmin = roles("chef", "admin")
IsDeliveryOrAdmin = roles("delivery", "admin")
