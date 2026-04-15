def get_active_company(request):
    active_company_id = request.session.get('active_company_id')
    
    if active_company_id:
        company = request.user.companies.filter(id=active_company_id).first()
        if company:
            return company
            
    first_company = request.user.companies.first()
    if first_company:
        request.session['active_company_id'] = first_company.id
        
    return first_company