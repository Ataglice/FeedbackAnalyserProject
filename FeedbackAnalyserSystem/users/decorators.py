from functools import wraps
from django.core.exceptions import PermissionDenied
from .models import CompanyMember
from main.utils import get_active_company 

def require_role(allowed_roles):
    """
    Декоратор, который проверяет роль пользователя в ЕГО активной компании.
    Использование: @require_role(['owner', 'admin'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            
            active_company = get_active_company(request)
            
            if not active_company:
                raise PermissionDenied("Компания не выбрана.")
            
            try:
                # Ищем "договор" между текущим юзером и активной компанией
                membership = CompanyMember.objects.get(user=request.user, company=active_company)
                
                # Если роль юзера не входит в список разрешенных — выгоняем
                if membership.role not in allowed_roles:
                    raise PermissionDenied(f"Доступ запрещен. Необходима одна из ролей: {', '.join(allowed_roles)}")
                    
            except CompanyMember.DoesNotExist:
                raise PermissionDenied("Вы не числитесь в этой компании.")
                
            # Если проверки пройдены, пускаем к выполнению функции
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator