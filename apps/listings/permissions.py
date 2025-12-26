from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Дозволяє доступ тільки власнику об'єкта або адміну
    """

    def has_object_permission(self, request, view, obj):
        # Admins мають повний доступ
        if request.user.is_admin():
            return True

        # Власник має доступ до свого оголошення
        return obj.owner == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Дозволяє читання всім, редагування тільки власнику
    """

    def has_object_permission(self, request, view, obj):
        # Читання дозволено всім
        if request.method in permissions.SAFE_METHODS:
            return True

        # Редагування тільки власнику або адміну
        return obj.owner == request.user or request.user.is_admin()


class IsOwnerToCreate(permissions.BasePermission):
    """
    Створювати оголошення можуть тільки Owners та Admins
    """

    def has_permission(self, request, view):
        # Перегляд дозволено всім
        if request.method in permissions.SAFE_METHODS:
            return True

        # Створення тільки для Owners та Admins
        if request.method == 'POST':
            return request.user.is_authenticated and (
                request.user.is_owner() or request.user.is_admin()
            )

        # Інші небезпечні методи (PUT/PATCH/DELETE) вимагають автентифікації
        return request.user.is_authenticated


class IsOwnerRoleOrAdmin(permissions.BasePermission):
    """
    Дозволяє доступ тільки власникам та адміністраторам
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_owner() or request.user.is_admin()
        )
