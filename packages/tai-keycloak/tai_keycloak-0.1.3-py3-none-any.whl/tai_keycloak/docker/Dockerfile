# Dockerfile para instancia de Keycloak preconfigurada con tai-keycloak
FROM quay.io/keycloak/keycloak:24.0.0

# Metadatos
LABEL maintainer="MateoSaezMata <msaez@triplealpha.in>"
LABEL description="Keycloak instance with tai-keycloak preconfigured environment"
LABEL version="0.1.0"

# Definir argumentos de construcción con valores por defecto
# Variables de BD solo se definen si se pasan explícitamente
ARG KC_DB
ARG KC_DB_URL
ARG KC_DB_USERNAME
ARG KC_DB_PASSWORD
ARG KC_DB_URL_DATABASE
# Variables base con valores por defecto
ARG KEYCLOAK_ADMIN=admin
ARG KEYCLOAK_ADMIN_PASSWORD=admin
ARG KC_HTTP_ENABLED=true
ARG KC_HOSTNAME
ARG KC_HOSTNAME_STRICT=false
ARG KC_HOSTNAME_STRICT_HTTPS=false
ARG KC_PROXY_HEADERS=xforwarded
ARG KC_HTTP_PORT=80
ARG KC_LOG_LEVEL=DEBUG

# Establecer variables de entorno solo para las que siempre tienen valor
ENV KEYCLOAK_ADMIN=${KEYCLOAK_ADMIN}
ENV KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}
ENV KC_HTTP_ENABLED=${KC_HTTP_ENABLED}
ENV KC_HOSTNAME=${KC_HOSTNAME}
ENV KC_HOSTNAME_STRICT=${KC_HOSTNAME_STRICT}
ENV KC_HOSTNAME_STRICT_HTTPS=${KC_HOSTNAME_STRICT_HTTPS}
ENV KC_PROXY_HEADERS=${KC_PROXY_HEADERS}
ENV KC_HTTP_PORT=${KC_HTTP_PORT}
ENV KC_LOG_LEVEL=${KC_LOG_LEVEL}

# Las variables de BD se configurarán en el script de inicio solo si tienen valor
# Pasamos los argumentos al contenedor para que el script pueda verificarlos
ENV KC_DB_ARG=${KC_DB}
ENV KC_DB_URL_ARG=${KC_DB_URL}
ENV KC_DB_USERNAME_ARG=${KC_DB_USERNAME}
ENV KC_DB_PASSWORD_ARG=${KC_DB_PASSWORD}
ENV KC_DB_URL_DATABASE_ARG=${KC_DB_URL_DATABASE}

# Copiar realm preconfigurado
COPY main-realm.json /opt/keycloak/data/import/

# Crear directorio para logs y configurar script de entrada
USER root
RUN mkdir -p /opt/keycloak/logs && chown keycloak:keycloak /opt/keycloak/logs

# Copiar y configurar script de entrada (como root)
COPY start-keycloak.sh /opt/keycloak/bin/start-keycloak.sh
RUN chmod +x /opt/keycloak/bin/start-keycloak.sh && \
    chown keycloak:keycloak /opt/keycloak/bin/start-keycloak.sh

# Volver al usuario keycloak
USER keycloak

# Exponer puerto configurado (por defecto 80 para Azure Web Apps)
EXPOSE ${KC_HTTP_PORT}

# Sobrescribir ENTRYPOINT y usar nuestro script
ENTRYPOINT []
CMD ["/opt/keycloak/bin/start-keycloak.sh"]

# Healthcheck adaptativo según el puerto configurado
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:${KC_HTTP_PORT:-80}/realms/master || exit 1