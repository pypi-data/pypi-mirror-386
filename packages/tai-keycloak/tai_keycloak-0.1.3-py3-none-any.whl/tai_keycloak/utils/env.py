import os
import tai_keycloak.config as config
from .provider import DatabaseProvider  # noqa: F401


class EnvironmentVariables:
    """ 
    Utility class to manage Keycloak environment variables.
    """

    # Variables base que siempre se configuran
    BASE_VARIABLES = [
        'KEYCLOAK_ADMIN', 'KEYCLOAK_ADMIN_PASSWORD',
        'KC_HTTP_ENABLED', 'KC_HOSTNAME_STRICT', 'KC_HOSTNAME_STRICT_HTTPS', 
        'KC_PROXY_HEADERS', 'KC_HTTP_PORT', 'KC_LOG_LEVEL'
    ]
    
    # Variables de BD que solo se configuran si existe MAIN_DATABASE_URL
    DB_VARIABLES = [
        'KC_DB', 'KC_DB_URL', 'KC_DB_USERNAME', 'KC_DB_PASSWORD', 'KC_DB_URL_DATABASE'
    ]

    def __init__(self):
        """Initialize with fresh database provider check."""
        self.db_provider = DatabaseProvider.from_environment()

    def set(self) -> None:
        """
        Set the necessary environment variables for Keycloak based on the
        current configuration and database provider.
        
        Only sets database variables if MAIN_DATABASE_URL exists and is valid.
        """
        # Only set database-related environment variables if we have a valid database provider
        if self.db_provider and self.db_provider.drivername in self.db_provider.ALLOWED_DRIVERS:
            os.environ['KC_DB'] = self.db_provider.type
            os.environ['KC_DB_URL'] = self.db_provider.url
            if self.db_provider.username:
                os.environ['KC_DB_USERNAME'] = self.db_provider.username
            if self.db_provider.password:
                os.environ['KC_DB_PASSWORD'] = self.db_provider.password
            os.environ['KC_DB_URL_DATABASE'] = self.db_provider.database

        # Set admin user and password if not already set
        os.environ.setdefault('KEYCLOAK_ADMIN', config.KEYCLOAK_DEFAULT_ADMIN_USER)
        os.environ.setdefault('KEYCLOAK_ADMIN_PASSWORD', config.KEYCLOAK_DEFAULT_ADMIN_PASSWORD)

        # Set HTTP settings
        # No configurar hostname para permitir acceso desde localhost
        # os.environ.setdefault('KC_HOSTNAME', config.KEYCLOAK_DEFAULT_HOSTNAME)
        os.environ.setdefault('KC_HTTP_ENABLED', 'true')
        os.environ.setdefault('KC_HOSTNAME_STRICT', 'false')
        # Usar proxy-headers en lugar de proxy (deprecado)
        os.environ.setdefault('KC_PROXY_HEADERS', 'xforwarded')
        # Deshabilitar HTTPS estricto para desarrollo local
        os.environ.setdefault('KC_HOSTNAME_STRICT_HTTPS', 'false')

        # Set HTTP port based on protocol
        if os.environ.get('KC_HTTP_PORT') is None:
            if os.environ.get('KC_HTTPS_ENABLED', 'false').lower() == 'true':
                os.environ['KC_HTTP_PORT'] = str(config.KEYCLOAK_DEFAULT_HTTPS_PORT)
            else:
                os.environ['KC_HTTP_PORT'] = str(config.KEYCLOAK_DEFAULT_HTTP_PORT)
        
        # Set log level
        os.environ.setdefault('KC_LOG_LEVEL', config.KEYCLOAK_DEFAULT_LOGLEVEL)

    def default_variables(self) -> dict:
        """
        Returns a dictionary of the default environment variables
        that would be set for Keycloak.
        """
        all_variables = self.BASE_VARIABLES.copy()
        
        # Solo incluir variables de BD si tenemos un provider válido
        if self.db_provider and self.db_provider.drivername in self.db_provider.ALLOWED_DRIVERS:
            all_variables.extend(self.DB_VARIABLES)
            
        return {var: os.getenv(var) for var in all_variables if os.getenv(var) is not None}