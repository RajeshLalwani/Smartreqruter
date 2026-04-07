from django import template

register = template.Library()

@register.filter
def anonymize(candidate, user):
    """
    Returns 'Candidate #ID' if user has blind_hiring enabled, else returns candidate's full name.
    Usage: {{ candidate|anonymize:request.user }}
    """
    if not user or not user.is_authenticated:
         # Fallback if something is wrong with user context
        if hasattr(candidate, 'full_name'):
             return candidate.full_name
        return str(candidate)

    # Check if user has blind_hiring enabled
    if getattr(user, 'blind_hiring', False):
        # We assume 'candidate' is a Candidate object or similar
        # If it's just a string, we can't do much but maybe masking? 
        # But we expect a model instance usually.
        if hasattr(candidate, 'id'):
            return f"Candidate #{candidate.id}"
        return "Anonymous Candidate"
    
    # Return normal name
    if hasattr(candidate, 'full_name'):
        return candidate.full_name
    return str(candidate)

@register.filter
def anonymize_photo(photo_url, user):
    """
    Returns default avatar URL if blind hiring is on.
    Usage: {{ candidate.user.profile_pic.url|anonymize_photo:request.user }}
    """
    if getattr(user, 'blind_hiring', False):
        return "/static/images/default_avatar.png" # ensure this exists or use a placeholder
    return photo_url
