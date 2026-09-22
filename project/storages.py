from django.conf import settings
from django.core.files.storage import FileSystemStorage

# Mirrors the presale/cashway/vigil-bot/realty convention: static + media on
# the S3-compatible object storage in STAGING/PRODUCTION. Unlike those apps,
# this one also needs a *local* fallback for PublicMediaStorage/
# PrivateMediaStorage (stimulus images + result XLSX) so `default_storage`
# and the explicit PrivateMediaStorage() calls work in dev/tests too — not
# just when S3 is configured.
if settings.STAGING or settings.PRODUCTION:
    from storages.backends.s3boto3 import S3Boto3Storage

    class StaticStorage(S3Boto3Storage):
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        location = settings.AWS_STATIC_LOCATION
        default_acl = 'public-read'

    class PublicMediaStorage(S3Boto3Storage):
        """Stimulus images — fine to serve directly, no participant data in them."""
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        location = settings.AWS_MEDIA_LOCATION
        default_acl = 'public-read'
        file_overwrite = False

    class PrivateMediaStorage(S3Boto3Storage):
        """Result XLSX exports — contain participant data, so private + signed URLs
        (BRD 4.7/6.2: researcher downloads via a presigned URL, 24h expiry)."""
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        location = settings.AWS_MEDIA_LOCATION
        default_acl = 'private'
        file_overwrite = False
        querystring_auth = True
        querystring_expire = settings.RESULT_DOWNLOAD_URL_EXPIRY_SECONDS
else:
    class PublicMediaStorage(FileSystemStorage):
        pass

    class PrivateMediaStorage(FileSystemStorage):
        """No real signing locally — `.url()` just serves it from MEDIA_URL,
        good enough for dev since nothing outside localhost can reach it."""
        pass
