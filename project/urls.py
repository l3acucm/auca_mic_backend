from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from moses import urls as moses_urls
from moses.admin import OTPAdminAuthenticationForm

from project.experiments import urls as experiments_urls
from project.experiments.views.public_session import public_urlpatterns

admin.site.site_header = 'AUCA Mic Admin'
admin.site.index_title = 'Психолингвистический эксперимент'
admin.site.login_form = OTPAdminAuthenticationForm

urlpatterns = [
    path('ping/', lambda request: JsonResponse({'status': 'ok'})),
    path('admin/', admin.site.urls),
    path('moses/', include(moses_urls, namespace='moses')),
    path('experiments/', include(experiments_urls, namespace='experiments')),
    # Unauthenticated participant-facing endpoints (session by URL, no login).
    # No namespace: PublicSessionViewSet's route names (PublicSession-detail,
    # etc.) are reversed bare, same as if this were the root urlconf.
    path('public/', include(public_urlpatterns)),
]

if settings.DEBUG:
    # Stimulus images / result XLSX live under MEDIA_ROOT in dev (S3 only in
    # STAGING/PRODUCTION) — serve them so the frontend can actually load them.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
