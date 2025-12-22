from rest_framework import permissions


class IsCustomerOrReadOnly(permissions.BasePermission):
    """
    Дозволяє читання всім, редагування тільки автору відгуку
    """

    def has_object_permission(self, request, view, obj):
        # Читання дозволено всім
        if request.method in permissions.SAFE_METHODS:
            return True

        # Редагування тільки автору або адміну
        return obj.customer == request.user or request.user.is_admin()


class IsListingOwnerOrReadOnly(permissions.BasePermission):
    """
    Дозволяє читання всім, дії тільки власнику оголошення
    Використовується для відповіді власника на відгук
    """

    def has_object_permission(self, request, view, obj):
        # Читання дозволено всім
        if request.method in permissions.SAFE_METHODS:
            return True

        # Дії тільки для власника оголошення або адміна
        return obj.listing.owner == request.user or request.user.is_admin()


class CanCreateReviewAsCustomer(permissions.BasePermission):
    """Дозволяє створювати відгуки тільки клієнтам"""

    def has_permission(self, request, view):
        # Читання дозволено всім
        if request.method in permissions.SAFE_METHODS:
            return True

        # Створювати можуть лише автентифіковані клієнти
        if request.method == 'POST':
            return request.user.is_authenticated and not request.user.is_owner()

        # Інші методи доступні тільки автентифікованим користувачам
        return request.user.is_authenticated
