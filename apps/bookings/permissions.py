from rest_framework import permissions


class IsCustomerOrListingOwnerOrAdmin(permissions.BasePermission):
    """
    Дозволяє доступ:
    - Клієнту (customer) бронювання
    - Власнику оголошення (listing.owner)
    - Адміну
    """

    def has_object_permission(self, request, view, obj):
        # Admins мають повний доступ
        if request.user.is_admin():
            return True

        # Власник оголошення має доступ
        if obj.listing.owner == request.user:
            return True

        # Клієнт має доступ до свого бронювання
        if obj.customer == request.user:
            return True

        return False


class IsListingOwnerOrAdmin(permissions.BasePermission):
    """
    Дозволяє доступ тільки:
    - Власнику оголошення (listing.owner)
    - Адміну

    Використовується для approve, reject, complete
    """

    def has_object_permission(self, request, view, obj):
        # Admins мають повний доступ
        if request.user.is_admin():
            return True

        # Власник оголошення має доступ
        return obj.listing.owner == request.user


class IsCustomerOnly(permissions.BasePermission):
    """
    Дозволяє доступ тільки клієнту бронювання
    """

    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user
