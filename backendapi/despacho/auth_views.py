from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response

class CustomLoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.get("refresh")
        if refresh_token:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False,  # True si usas HTTPS
                samesite="Lax",
                path="/api/token/refresh/"
            )
            del response.data["refresh"]
        return response
