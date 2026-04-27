from users.models import Company, CompanyMember

def get_active_company(request):
    company_id = request.session.get('active_company_id')
    
    if company_id:
        try:
            return Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            pass
            
    # Фолбэк: если в сессии ничего нет (например, юзер зашел по прямой ссылке в дашборд), 
    # берем его первую попавшуюся компанию
    first_membership = CompanyMember.objects.filter(user=request.user).first()
    if first_membership:
        request.session['active_company_id'] = first_membership.company.id
        return first_membership.company
        
    return None