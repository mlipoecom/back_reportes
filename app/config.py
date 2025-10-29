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
    "SENDER_EMAIL": "martin.liporace@gmail.com",
    "SENDER_PASSWORD": "lsefeqmutyblycri",
    "RECEIVER_EMAIL": "martin.liporace@ecom.com.uy"
}

TOKEN_CONFIG = {
    "SECRET_KEY": "clave_ecom_2025",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
    "REFRESH_TOKEN_EXPIRE_DAYS": 7
}