from enum import IntEnum


class UserRole(IntEnum):
    SUPER_ADMIN = 1
    SUPPLIER_ADMIN = 2
    CUSTOMER_ADMIN = 3
    CUSTOMER_USER = 4
    COMPANY_ADMIN = 5
    COMPANY_USER = 6

    @classmethod
    def get_name(cls, role_id: int) -> str:
        role_map = {
            cls.SUPER_ADMIN: "super_admin",
            cls.SUPPLIER_ADMIN: "supplier_admin",
            cls.CUSTOMER_ADMIN: "customer_admin",
            cls.CUSTOMER_USER: "customer_user",
            cls.COMPANY_ADMIN: "company_admin",
            cls.COMPANY_USER: "company_user",
        }
        return role_map.get(role_id, "undefined")

    @classmethod
    def has_permission(cls, user_role_id: int, allowed_roles: list[int]) -> bool:
        return user_role_id in allowed_roles

