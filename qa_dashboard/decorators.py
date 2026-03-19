from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(*allowed_roles):
    """
    Decorator for views that checks that the user is logged in and has a specific role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Relying on @login_required to handle authentication

            if request.user.role in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                if request.user.role == 'AGENT':
                    raise PermissionDenied("This section is for management only.")
                # If they are a Manager accessing a Top Management only page:
                raise PermissionDenied("This section is for top management only.")
        return _wrapped_view
    return decorator
