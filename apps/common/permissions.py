from rest_framework import permissions

class IsInGroup(permissions.BasePermission):

    def has_permission(self, request, view):
        allowed = getattr(view, 'permission_groups', None)
        if not allowed:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        user_groups = set(g.name for g in request.user.groups.all())
        return bool(user_groups.intersection(set(allowed)))

class IsOwnerOrDjangoPerm(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'owner') and request.user and request.user.is_authenticated:
            if obj.owner_id == request.user.id:
                return True

        return False