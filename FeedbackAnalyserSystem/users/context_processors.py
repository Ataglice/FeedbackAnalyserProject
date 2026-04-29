from .models import CompanyMember
from .models import Notification

def active_company_role(request):
    if not request.user.is_authenticated:
        return {'is_company_admin': False, 'current_role': None}

    company_id = request.session.get('active_company_id')
    if not company_id:
        return {'is_company_admin': False, 'current_role': None}

    try:
        membership = CompanyMember.objects.get(user=request.user, company_id=company_id)
        
        is_admin = membership.role in ['owner', 'admin']
        
        return {
            'is_company_admin': is_admin,
            'current_role': membership.role
        }
    except CompanyMember.DoesNotExist:
        return {'is_company_admin': False, 'current_role': None}
    
def global_notifications(request):
    if request.user.is_authenticated:
        # Достаем 5 последних непрочитанных уведомлений
        unread_notifs = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
        # Считаем их общее количество для бейджика
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        return {
            'unread_notifs': unread_notifs,
            'unread_notifs_count': unread_count
        }
    return {}