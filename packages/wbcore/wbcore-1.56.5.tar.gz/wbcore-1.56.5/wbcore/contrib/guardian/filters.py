from rest_framework.filters import BaseFilterBackend


class ObjectPermissionsFilter(BaseFilterBackend):
    """
    A filter backend that limits results to those where the requesting user
    has read object level permissions.
    """

    def filter_queryset(self, request, queryset, view):
        from guardian.shortcuts import get_objects_for_user
        from wbcore.contrib.guardian.models.mixins import PermissionObjectModelMixin

        model_class = queryset.model
        if issubclass(model_class, PermissionObjectModelMixin):
            user = request.user

            return get_objects_for_user(
                user, [model_class.view_perm_str], queryset, **model_class.guardian_shortcut_kwargs
            )
        return queryset
