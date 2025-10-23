from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

def jwt_access_token(request):
    context = {}
    
    if request.user.is_authenticated:
        try:
            # Generate a new access token for the user
            access_token = AccessToken.for_user(request.user)
            context['jwt_access_token'] = str(access_token)
            
            # You might also want to include the expiration time
            context['jwt_access_token_exp'] = access_token.payload['exp']
            
        except Exception as e:
            # Handle any potential errors gracefully
            if settings.DEBUG:
                print(f"Error generating JWT token: {e}")
    
    return context



def debug(request):
    print("Is Live =", settings.LIVE)
    return {
        'debug': settings.DEBUG,
        'live': settings.LIVE
    }