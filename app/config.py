DB_CONFIG = { # Cambiar en AWS secrets
    "user": "neondb_owner",
    "password": "npg_N9Awt6rgVxqX",
    "host": "ep-square-wave-adh9c715-pooler.c-2.us-east-1.aws.neon.tech",
    "port": 5432,
    "database": "gestion_informes"
}

SMTP_CONFIG = {
    "SMTP_SERVER": "smtp.gmail.com", 
    "SMTP_PORT": 587,
    "SENDER_EMAIL": "desarrolloecom2025@gmail.com",
    "SENDER_PASSWORD": "ldsfccrlmfpvwegi",
    "RECEIVER_EMAIL": "martin.liporace@ecom.com.uy"
}

TOKEN_CONFIG = {
    "SECRET_KEY": "clave_ecom_2025",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
    "REFRESH_TOKEN_EXPIRE_DAYS": 7
}


S3_CONFIG = {
    "S3_ENDPOINT": "https://s3.localhost.localstack.cloud:4566",
    # "S3_ENDPOINT": "http://localhost:4566",
    "S3_BUCKET": "portal-reportes"
}