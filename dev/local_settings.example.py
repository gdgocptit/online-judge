# Copy to dmoj/local_settings.py. Loaded inside dmoj/settings.py.
# Local development only; never deploy these credentials.
from pathlib import Path

SECRET_KEY = 'local-development-only-do-not-deploy-this-key-to-production'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
SITE_NAME = 'GDG on Campus: PTIT Online Judge'
SITE_LONG_NAME = 'GDG on Campus: PTIT Online Judge'
TIME_ZONE = DEFAULT_USER_TIME_ZONE = 'Asia/Ho_Chi_Minh'
DEFAULT_USER_LANGUAGE = 'CPP17'
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'dmoj', 'USER': 'dmoj', 'PASSWORD': 'local-development-only',
    'HOST': '127.0.0.1', 'PORT': '13306',
    'OPTIONS': {'charset': 'utf8mb4', 'sql_mode': 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'},
}}
CACHES = {'default': {
    'BACKEND': 'django.core.cache.backends.redis.RedisCache',
    'LOCATION': 'redis://127.0.0.1:16379/1',
}}
STATIC_ROOT = str(Path(BASE_DIR) / '.local/static')
STATICFILES_FINDERS += ('compressor.finders.CompressorFinder',)
MEDIA_ROOT = str(Path(BASE_DIR) / '.local/media')
MEDIA_URL = '/media/'
DMOJ_PROBLEM_DATA_ROOT = str(Path(BASE_DIR) / '.local/problems')
ENABLE_FTS = True
EVENT_DAEMON_USE = False
CELERY_BROKER_URL = 'redis://127.0.0.1:16379/0'
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
REGISTRATION_OPEN = False
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
