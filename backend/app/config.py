"""Configuración de la aplicación (carga desde .env o variables de entorno)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="RITECH_", extra="ignore"
    )

    app_name: str = "RiTech · Sistema de Exportación"
    company: str = "RiTech SAS"
    api_prefix: str = "/api"

    # RR-003 · La base de datos transaccicial es PostgreSQL.
    # Para desarrollo local sin servidor Postgres se puede usar SQLite:
    #   RITECH_DB_URL=sqlite:///./ritch_dev.db
    db_url: str = "sqlite:///./ritch_dev.db"
    sql_echo: bool = False

    # Autenticación (HU-01, HU-02, RNF-001)
    jwt_secret: str = "cambia-esta-clave-en-produccion"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8

    # Credenciales de las cuentas de demostración. En producción, Render
    # genera estos valores como secretos y no se muestran en el frontend.
    demo_password: str = "RiTech2026*"
    buyer_password: str = "ClienteUE2026*"

    # Almacenamiento documental (RR: AWS S3 o Azure Blob Storage).
    # En esta versión los documentos se guardan en disco local bajo
    # RITECH_UPLOAD_DIR; la capa de servicios permite sustituirla por S3/Azure.
    upload_dir: str = "./uploads"
    max_upload_mb: int = 15

    # HU-22 · copias de seguridad
    backup_dir: str = "./respaldos"
    backup_auto_horas: int = 24

    # HU-20 · integraciones externas. Por defecto trabajan en modo local
    # (respaldo determinista) para que la demostración no dependa de internet;
    # con RITECH_INTEGRACIONES_RED=1 se consulta el servicio público de tipos
    # de cambio y, si falla, se usa el respaldo local.
    integraciones_red: bool = False
    integraciones_timeout: int = 4

    # CORS para el frontend
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
