import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent  # rental_projekt/

# Директорія для логів
LOGS_DIR = BASE_DIR / 'logs'

# Створити директорію якщо не існує
LOGS_DIR.mkdir(exist_ok=True)

# ============================================
# НАЛАШТУВАННЯ ЛОГУВАННЯ
# ============================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    # ============================================
    # FORMATTERS - Формати логів
    # ============================================
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} | {name} | {module}.{funcName}:{lineno} | {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {asctime} | {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },

    # ============================================
    # HANDLERS - Обробники логів
    # ============================================
    'handlers': {
        # Console - виводить в консоль
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },

        # ALL LOGS - всі логи (info, warning, error, critical)
        'file_all': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'all.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },

        # ERROR LOGS - тільки помилки (error, critical)
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'error.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },

        # WARNING LOGS - тільки попередження
        'file_warning': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'warning.log',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },

        # DEBUG LOGS - детальні логи для розробки
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'debug.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 3,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },

        # DATABASE LOGS - запити до БД
        'file_db': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'database.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },

        # SECURITY LOGS - безпека
        'file_security': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },

        # API LOGS - API запити
        'file_api': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'api.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 7,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },

        # CELERY LOGS - асинхронні задачі
        'file_celery': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'celery.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },

    # ============================================
    # LOGGERS - Логери
    # ============================================
    'loggers': {
        # Django root logger
        'django': {
            'handlers': ['console', 'file_all', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },

        # Django request logger
        'django.request': {
            'handlers': ['console', 'file_error'],
            'level': 'ERROR',
            'propagate': False,
        },

        # Django server logger
        'django.server': {
            'handlers': ['console', 'file_all'],
            'level': 'INFO',
            'propagate': False,
        },

        # Django database queries
        'django.db.backends': {
            'handlers': ['file_db'],
            'level': 'DEBUG',
            'propagate': False,
        },

        # Django security
        'django.security': {
            'handlers': ['file_security'],
            'level': 'INFO',
            'propagate': False,
        },

        # ==========================================
        # APPLICATION LOGGERS
        # ==========================================

        # Listings app
        'apps.listings': {
            'handlers': ['console', 'file_all', 'file_error', 'file_warning'],
            'level': 'INFO',
            'propagate': False,
        },

        # Bookings app
        'apps.bookings': {
            'handlers': ['console', 'file_all', 'file_error', 'file_warning'],
            'level': 'INFO',
            'propagate': False,
        },

        # Reviews app
        'apps.reviews': {
            'handlers': ['console', 'file_all', 'file_error', 'file_warning'],
            'level': 'INFO',
            'propagate': False,
        },

        # Users app
        'apps.users': {
            'handlers': ['console', 'file_all', 'file_error', 'file_security'],
            'level': 'INFO',
            'propagate': False,
        },

        # API logger
        'api': {
            'handlers': ['console', 'file_api', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },

        # Celery logger
        'celery': {
            'handlers': ['console', 'file_celery', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },

        # Custom app logger
        'app': {
            'handlers': ['console', 'file_all', 'file_error', 'file_warning'],
            'level': 'INFO',
            'propagate': False,
        },
    },

    # Root logger
    'root': {
        'handlers': ['console', 'file_all', 'file_error'],
        'level': 'INFO',
    },
}


# ============================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ============================================

def get_logger(name=None):
    """
    Отримати logger для використання в коді

    Usage:
        from rental_projekt_final.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info('Something happened')
    """
    import logging
    return logging.getLogger(name or 'app')


def log_exception(logger, exception, extra_data=None):
    """
    Логувати виняток з додатковою інформацією

    Usage:
        try:
            # some code
        except Exception as e:
            log_exception(logger, e, {'user_id': user.id})
    """
    extra_info = extra_data or {}
    logger.exception(
        f"Exception occurred: {str(exception)}",
        extra=extra_info,
        exc_info=True
    )


def log_api_request(logger, request, response=None):
    """
    Логувати API запит

    Usage:
        log_api_request(logger, request, response)
    """
    logger.info(
        f"API Request: {request.method} {request.path}",
        extra={
            'method': request.method,
            'path': request.path,
            'user': getattr(request.user, 'id', None),
            'status_code': response.status_code if response else None,
        }
    )


# ============================================
# НАЛАШТУВАННЯ ДЛЯ РІЗНИХ СЕРЕДОВИЩ
# ============================================

def get_logging_config(environment='development'):
    """
    Отримати конфігурацію логування для певного середовища

    Args:
        environment: 'development', 'staging', 'production'

    Returns:
        dict: Конфігурація логування
    """
    config = LOGGING.copy()

    if environment == 'development':
        # Development - більше деталей, console output
        config['handlers']['console']['level'] = 'DEBUG'
        config['loggers']['django.db.backends']['level'] = 'DEBUG'
        config['root']['level'] = 'DEBUG'

    elif environment == 'staging':
        # Staging - середній рівень деталізації
        config['handlers']['console']['level'] = 'INFO'
        config['loggers']['django.db.backends']['level'] = 'INFO'
        config['root']['level'] = 'INFO'

    elif environment == 'production':
        # Production - мінімум в консоль, все в файли
        config['handlers']['console']['level'] = 'WARNING'
        config['loggers']['django.db.backends']['level'] = 'WARNING'
        config['root']['level'] = 'INFO'

    return config


# ============================================
# ПРИКЛАДИ ВИКОРИСТАННЯ
# ============================================

"""
В VIEWS:
────────────────────────────────────────────────────────────────────────
from rental_projekt_final.logging_config import get_logger

logger = get_logger(__name__)

def my_view(request):
    logger.info('View called')

    try:
        # some code
        logger.debug('Processing data...')
    except Exception as e:
        logger.error(f'Error in view: {e}', exc_info=True)


В MODELS:
────────────────────────────────────────────────────────────────────────
from rental_projekt_final.logging_config import get_logger

logger = get_logger('apps.listings')

class Listing(models.Model):
    def save(self, *args, **kwargs):
        logger.info(f'Saving listing: {self.title}')
        try:
            super().save(*args, **kwargs)
            logger.debug(f'Listing saved: {self.id}')
        except Exception as e:
            logger.error(f'Error saving listing: {e}', exc_info=True)
            raise


В SERIALIZERS:
────────────────────────────────────────────────────────────────────────
from rental_projekt_final.logging_config import get_logger

logger = get_logger('api')

class ListingSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        logger.debug(f'Validating data: {attrs}')
        try:
            # validation logic
            return attrs
        except ValidationError as e:
            logger.warning(f'Validation error: {e}')
            raise
"""
