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