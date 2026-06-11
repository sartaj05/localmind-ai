from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    path("api/auth/", include("accounts.urls")),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),

    # Frontend uses this URL
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Optional old URL support, keep it so nothing breaks
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh_old"),

    path("api/ai/", include("ai_engine.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)