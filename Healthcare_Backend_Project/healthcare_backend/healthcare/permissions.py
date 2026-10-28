from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsDoctorCreatorOrReadOnly(BasePermission):
    """All authenticated users may view doctors; only the creator may change/delete them."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.created_by_id == request.user.id
