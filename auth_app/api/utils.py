from rest_framework_simplejwt.tokens import RefreshToken


def build_login_response_data(serializer):
    data = {
        "detail": "Login successful",
        "user": {
            "id": serializer.user.id,
            "email": serializer.user.email,
        }
    }

    return data


def set_auth_cookies(response, access, refresh):
    response.set_cookie(
        key='access_token',
        value=access,
        httponly=True,
        secure=True,
        samesite='Lax'
    )

    response.set_cookie(
        key='refresh_token',
        value=refresh,
        httponly=True,
        secure=True,
        samesite='Lax'
    )

    return response


def blacklist_refresh_token(refresh_token_string):
    refresh_token = RefreshToken(refresh_token_string)
    refresh_token.blacklist()


def clear_auth_cookies(response):
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')


def generate_new_access_token(refresh_token_string):
    refresh_token = RefreshToken(refresh_token_string)
    new_access_token = str(refresh_token.access_token)
    return new_access_token


def set_access_cookie(response, new_access_token):
    response.set_cookie(
        key='access_token',
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite='Lax'
    )
