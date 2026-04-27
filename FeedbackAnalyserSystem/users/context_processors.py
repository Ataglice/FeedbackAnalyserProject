from .models import CompanyMember

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