# Паролі
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# Імена
FIRST_NAME_MAX_LENGTH = 50
LAST_NAME_MAX_LENGTH = 50
USERNAME_MAX_LENGTH = 150

# Телефон
PHONE_MAX_LENGTH = 20

# Біографія
BIO_MAX_LENGTH = 500

# Фото профілю
PROFILE_PHOTO_MAX_SIZE_MB = 5
PROFILE_PHOTO_MAX_SIZE_BYTES = PROFILE_PHOTO_MAX_SIZE_MB * 1024 * 1024

# ============================================
# ОГОЛОШЕННЯ (LISTINGS)
# ============================================

# Заголовок та опис
LISTING_TITLE_MIN_LENGTH = 10
LISTING_TITLE_MAX_LENGTH = 255
LISTING_DESCRIPTION_MIN_LENGTH = 50
LISTING_DESCRIPTION_MAX_LENGTH = 2000

# Адреса
ADDRESS_MAX_LENGTH = 255
CITY_MAX_LENGTH = 100
COUNTRY_MAX_LENGTH = 100

# Координати
LATITUDE_MAX_DIGITS = 9
LATITUDE_DECIMAL_PLACES = 6
LONGITUDE_MAX_DIGITS = 9
LONGITUDE_DECIMAL_PLACES = 6

# Характеристики
MIN_ROOMS = 1
MAX_ROOMS = 20
MIN_BEDROOMS = 0
MAX_BEDROOMS = 20
MIN_BATHROOMS = 1
MAX_BATHROOMS = 10
MIN_GUESTS = 1
MAX_GUESTS = 50

# Площа (кв.м.)
MIN_AREA = 10
MAX_AREA = 10000
AREA_MAX_DIGITS = 10
AREA_DECIMAL_PLACES = 2

# Ціна (за ніч)
MIN_PRICE = 10
MAX_PRICE = 1000000
PRICE_MAX_DIGITS = 10
PRICE_DECIMAL_PLACES = 2

# Фото оголошення
LISTING_PHOTOS_MAX_COUNT = 20
LISTING_PHOTO_MAX_SIZE_MB = 10
LISTING_PHOTO_MAX_SIZE_BYTES = LISTING_PHOTO_MAX_SIZE_MB * 1024 * 1024

# Зручності (amenities)
AMENITY_NAME_MAX_LENGTH = 100
AMENITY_ICON_MAX_LENGTH = 50
MAX_AMENITIES_PER_LISTING = 50

# ============================================
# БРОНЮВАННЯ (BOOKINGS)
# ============================================

# Мінімальна/максимальна тривалість бронювання (днів)
MIN_BOOKING_DURATION_DAYS = 1
MAX_BOOKING_DURATION_DAYS = 365

# Мінімальний час до заїзду (днів)
MIN_DAYS_BEFORE_CHECKIN = 0  # Можна бронювати на сьогодні

# Максимальний час до заїзду (днів)
MAX_DAYS_BEFORE_CHECKIN = 730  # 2 роки вперед

# Скасування
CANCELLATION_FLEXIBLE_HOURS = 24
CANCELLATION_MODERATE_DAYS = 5
CANCELLATION_STRICT_DAYS = 7
CANCELLATION_SUPER_STRICT_DAYS = 30

# Спеціальні запити
SPECIAL_REQUESTS_MAX_LENGTH = 1000

# ============================================
# ВІДГУКИ (REVIEWS)
# ============================================

# Рейтинг
MIN_RATING = 1
MAX_RATING = 5

# Коментар
REVIEW_COMMENT_MIN_LENGTH = 10
REVIEW_COMMENT_MAX_LENGTH = 2000

# Відповідь власника
OWNER_RESPONSE_MAX_LENGTH = 1000

# Фото відгуків
REVIEW_PHOTOS_MAX_COUNT = 10
REVIEW_PHOTO_MAX_SIZE_MB = 5
REVIEW_PHOTO_MAX_SIZE_BYTES = REVIEW_PHOTO_MAX_SIZE_MB * 1024 * 1024

# ============================================
# ПОВІДОМЛЕННЯ (MESSAGES)
# ============================================

# Текст повідомлення
MESSAGE_TEXT_MIN_LENGTH = 1
MESSAGE_TEXT_MAX_LENGTH = 2000

# Тема повідомлення
MESSAGE_SUBJECT_MAX_LENGTH = 200

# Вкладення
MESSAGE_ATTACHMENTS_MAX_COUNT = 5
MESSAGE_ATTACHMENT_MAX_SIZE_MB = 10
MESSAGE_ATTACHMENT_MAX_SIZE_BYTES = MESSAGE_ATTACHMENT_MAX_SIZE_MB * 1024 * 1024

# ============================================
# ОПЛАТА (PAYMENTS)
# ============================================

# Сума
MIN_PAYMENT_AMOUNT = 1
MAX_PAYMENT_AMOUNT = 1000000
PAYMENT_AMOUNT_MAX_DIGITS = 10
PAYMENT_AMOUNT_DECIMAL_PLACES = 2

# Комісія платформи (%)
PLATFORM_FEE_PERCENTAGE = 10

# Податок (%)
TAX_PERCENTAGE = 20

# Прибиральний збір
DEFAULT_CLEANING_FEE = 50

# ID транзакції
TRANSACTION_ID_MAX_LENGTH = 255

# ============================================
# СПОВІЩЕННЯ (NOTIFICATIONS)
# ============================================

# Заголовок та текст
NOTIFICATION_TITLE_MAX_LENGTH = 255
NOTIFICATION_MESSAGE_MAX_LENGTH = 1000

# Час життя непрочитаних сповіщень (днів)
NOTIFICATION_RETENTION_DAYS = 90

# ============================================
# ПАГІНАЦІЯ (PAGINATION)
# ============================================

# API пагінація
DEFAULT_PAGE_SIZE = 20
MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 100

# Списки
LISTINGS_PER_PAGE = 24
BOOKINGS_PER_PAGE = 20
REVIEWS_PER_PAGE = 10
MESSAGES_PER_PAGE = 20
NOTIFICATIONS_PER_PAGE = 20

# ============================================
# ПОШУК (SEARCH)
# ============================================

# Довжина пошукового запиту
SEARCH_QUERY_MIN_LENGTH = 2
SEARCH_QUERY_MAX_LENGTH = 200

# Результати пошуку
MAX_SEARCH_RESULTS = 100

# Радіус пошуку (км)
DEFAULT_SEARCH_RADIUS_KM = 10
MAX_SEARCH_RADIUS_KM = 100

# ============================================
# ФАЙЛИ (FILES)
# ============================================

# Загальні обмеження для файлів
MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Дозволені розширення
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
ALLOWED_DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'txt']
ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'avi', 'mov']

# ============================================
# БЕЗПЕКА (SECURITY)
# ============================================

# JWT токени
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = 60  # 1 година
JWT_REFRESH_TOKEN_LIFETIME_DAYS = 7  # 7 днів

# OTP коди
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10

# Спроби входу
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION_MINUTES = 30

# Сесії
SESSION_COOKIE_AGE_SECONDS = 3600 * 24 * 7  # 7 днів

# ============================================
# EMAIL
# ============================================

# Довжина email
EMAIL_MAX_LENGTH = 255

# Теми листів
EMAIL_SUBJECT_MAX_LENGTH = 200

# ============================================
# РЕЙТИНГИ ТА СТАТИСТИКА
# ============================================

# Мінімальна кількість відгуків для рейтингу
MIN_REVIEWS_FOR_RATING = 3

# Рейтинг за замовчуванням
DEFAULT_RATING = 0

# TOP списки
TOP_LISTINGS_COUNT = 10
TOP_OWNERS_COUNT = 10
FEATURED_LISTINGS_COUNT = 20

# ============================================
# КЕШУВАННЯ (CACHE)
# ============================================

# Час життя кешу (секунди)
CACHE_TTL_SHORT = 60  # 1 хвилина
CACHE_TTL_MEDIUM = 300  # 5 хвилин
CACHE_TTL_LONG = 3600  # 1 година
CACHE_TTL_VERY_LONG = 86400  # 1 день

# ============================================
# RATE LIMITING
# ============================================

# API запити на хвилину
API_RATE_LIMIT_PER_MINUTE = 60

# API запити на годину
API_RATE_LIMIT_PER_HOUR = 1000

# API запити на день
API_RATE_LIMIT_PER_DAY = 10000

# ============================================
# КООРДИНАТИ ЗА ЗАМОВЧУВАННЯМ
# ============================================

# Київ, Україна
DEFAULT_LATITUDE = 50.4501
DEFAULT_LONGITUDE = 30.5234

# ============================================
# ВАЛЮТИ
# ============================================

DEFAULT_CURRENCY = 'UAH'

# ============================================
# МОВИ
# ============================================

DEFAULT_LANGUAGE = 'uk'

# ============================================
# ЗОБРАЖЕННЯ
# ============================================

# Розміри thumbnail
THUMBNAIL_SMALL_WIDTH = 150
THUMBNAIL_SMALL_HEIGHT = 150

THUMBNAIL_MEDIUM_WIDTH = 400
THUMBNAIL_MEDIUM_HEIGHT = 300

THUMBNAIL_LARGE_WIDTH = 800
THUMBNAIL_LARGE_HEIGHT = 600

# Якість зображення (1-100)
IMAGE_QUALITY = 85

# ============================================
# ГОТЕЛЬНІ КВАРТИРИ (HOTEL APARTMENTS)
# ============================================

# Максимальна кількість кімнат на одну адресу
MAX_HOTEL_ROOMS_PER_ADDRESS = 20

# ============================================
# ВЕРИФІКАЦІЯ
# ============================================

# Документи для верифікації
VERIFICATION_DOCUMENT_MAX_SIZE_MB = 10
VERIFICATION_DOCUMENT_MAX_SIZE_BYTES = VERIFICATION_DOCUMENT_MAX_SIZE_MB * 1024 * 1024

# ============================================
# STRIPE/PAYMENT PROVIDERS
# ============================================

# Мінімальна сума для Stripe (центи)
STRIPE_MINIMUM_AMOUNT_CENTS = 50


# ============================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ============================================

def bytes_to_mb(bytes_value):
    """Конвертує байти в мегабайти"""
    return bytes_value / (1024 * 1024)


def mb_to_bytes(mb_value):
    """Конвертує мегабайти в байти"""
    return int(mb_value * 1024 * 1024)


def get_max_file_size_display(bytes_value):
    """Повертає розмір файлу в читабельному форматі"""
    mb = bytes_to_mb(bytes_value)
    if mb < 1:
        kb = bytes_value / 1024
        return f"{kb:.1f} KB"
    return f"{mb:.1f} MB"


# ============================================
# ЕКСПОРТ КОНСТАНТ ДЛЯ FRONTEND
# ============================================

# Константи які потрібні на frontend
FRONTEND_CONSTANTS = {
    'listings': {
        'title_min_length': LISTING_TITLE_MIN_LENGTH,
        'title_max_length': LISTING_TITLE_MAX_LENGTH,
        'description_min_length': LISTING_DESCRIPTION_MIN_LENGTH,
        'description_max_length': LISTING_DESCRIPTION_MAX_LENGTH,
        'photos_max_count': LISTING_PHOTOS_MAX_COUNT,
        'photo_max_size_mb': LISTING_PHOTO_MAX_SIZE_MB,
        'min_rooms': MIN_ROOMS,
        'max_rooms': MAX_ROOMS,
        'min_guests': MIN_GUESTS,
        'max_guests': MAX_GUESTS,
        'min_price': MIN_PRICE,
        'max_price': MAX_PRICE,
    },
    'bookings': {
        'min_duration_days': MIN_BOOKING_DURATION_DAYS,
        'max_duration_days': MAX_BOOKING_DURATION_DAYS,
        'max_days_before_checkin': MAX_DAYS_BEFORE_CHECKIN,
    },
    'reviews': {
        'min_rating': MIN_RATING,
        'max_rating': MAX_RATING,
        'comment_min_length': REVIEW_COMMENT_MIN_LENGTH,
        'comment_max_length': REVIEW_COMMENT_MAX_LENGTH,
        'photos_max_count': REVIEW_PHOTOS_MAX_COUNT,
        'photo_max_size_mb': REVIEW_PHOTO_MAX_SIZE_MB,
    },
    'messages': {
        'text_max_length': MESSAGE_TEXT_MAX_LENGTH,
        'attachments_max_count': MESSAGE_ATTACHMENTS_MAX_COUNT,
        'attachment_max_size_mb': MESSAGE_ATTACHMENT_MAX_SIZE_MB,
    },
    'pagination': {
        'default_page_size': DEFAULT_PAGE_SIZE,
        'max_page_size': MAX_PAGE_SIZE,
    },
    'files': {
        'allowed_image_extensions': ALLOWED_IMAGE_EXTENSIONS,
        'max_upload_size_mb': MAX_UPLOAD_SIZE_MB,
    }
}

# ============================================
# ВАЛІДАЦІЙНІ ПОВІДОМЛЕННЯ
# ============================================

VALIDATION_MESSAGES = {
    'min_length': 'Мінімальна довжина: {min_length} символів',
    'max_length': 'Максимальна довжина: {max_length} символів',
    'min_value': 'Мінімальне значення: {min_value}',
    'max_value': 'Максимальне значення: {max_value}',
    'file_too_large': 'Файл занадто великий. Максимум: {max_size} MB',
    'too_many_files': 'Занадто багато файлів. Максимум: {max_count}',
    'invalid_extension': 'Недопустиме розширення файлу. Дозволені: {extensions}',
}


