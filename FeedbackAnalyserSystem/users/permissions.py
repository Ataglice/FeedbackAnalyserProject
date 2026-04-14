from rest_framework_api_key.permissions import BaseHasAPIKey
from .models import CompanyAPIKey

class HasCompanyAPIKey(BaseHasAPIKey):
    model = CompanyAPIKey