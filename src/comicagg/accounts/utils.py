from comicagg.accounts.models import UserProfile

def get_profile(user):
    return UserProfile.objects.get(user=user)
