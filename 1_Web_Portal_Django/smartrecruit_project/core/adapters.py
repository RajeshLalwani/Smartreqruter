from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to restrict SSO registration to specific corporate domains
    and automatically assign permissions/groups to new recruiter accounts.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Hook that is called after a user successfully authenticates via a 
        social provider, but before the login is actually processed.
        """
        email = sociallogin.user.email
        if not email:
            return 

        # Domain Enforcement
        domain = email.split('@')[-1].lower()
        allowed_domains = getattr(settings, 'SOCIALACCOUNT_DOMAIN_WHITELIST', [])
        
        if allowed_domains and domain not in [d.lower() for d in allowed_domains]:
            raise PermissionDenied("Access Denied: Corporate email required.")

    def save_user(self, request, sociallogin, form=None):
        """
        Saves a newly created social user and performs post-creation setup.
        """
        user = super().save_user(request, sociallogin, form)
        
        # 1. Attribute Mapping (Microsoft/Okta)
        extra_data = sociallogin.account.extra_data
        
        # Map Name if not present
        if not user.first_name and 'displayName' in extra_data:
            name_parts = extra_data.get('displayName', '').split(' ')
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = ' '.join(name_parts[1:])
        
        # 2. Auto-assign to 'Recruiters' group
        try:
            recruiter_group, _ = Group.objects.get_or_create(name='Recruiters')
            user.groups.add(recruiter_group)
            user.save()
        except Exception as e:
            print(f"Error assigning group to SSO user: {e}")
            
        return user
