from functools import wraps
from flask import abort
from flask_login import current_user


def roles_requeridos(*roles):
    """Exige que el usuario autenticado sea de tipo 'usuario' (no cliente del portal)
    y que su rol este en la lista permitida."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if not current_user.is_authenticated or current_user.tipo != "usuario":
                abort(403)
            if current_user.rol not in roles:
                abort(403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador


def solo_cliente_portal(vista):
    """Exige que el autenticado sea un acceso de cliente del portal, no un usuario interno."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != "cliente":
            abort(403)
        return vista(*args, **kwargs)
    return envoltura
