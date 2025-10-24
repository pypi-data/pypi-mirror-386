# Dockerfile para instancia de Keycloak preconfigurada
FROM quay.io/keycloak/keycloak:24.0.0

# Metadatos
LABEL maintainer="MateoSaezMata <msaez@triplealpha.in>"
LABEL description="Keycloak instance with preconfigured environment"
LABEL version="0.1.0"

# Definir argumentos de construcción
# Variables para URLs que serán parseadas automáticamente
ARG MAIN_DATABASE_URL
ARG MAIN_KEYCLOAK_URL

# Establecer variables de entorno base
ENV KC_HTTP_ENABLED=true
# ENV KC_HOSTNAME=localhost
ENV KC_HOSTNAME_STRICT=false
ENV KC_HOSTNAME_STRICT_HTTPS=false
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_HTTP_PORT=80
ENV KC_LOG_LEVEL=INFO

# Copiar realm preconfigurado y script de parseo de BD
COPY main-realm.json /opt/keycloak/data/import/
COPY parser.sh /opt/keycloak/bin/

# Crear directorio para logs y configurar permisos
USER root
RUN mkdir -p /opt/keycloak/logs && chown keycloak:keycloak /opt/keycloak/logs

# Hacer ejecutable el script de parseo
RUN chmod +x /opt/keycloak/bin/parser.sh

# Crear archivo de variables por defecto (el parsing se hará en runtime)
RUN echo "# Configuration variables will be parsed at runtime" > /opt/keycloak/db_vars.env && \
    echo "# Default values for Keycloak" >> /opt/keycloak/db_vars.env

# Copiar y configurar script de entrada (como root)
COPY start-keycloak.sh /opt/keycloak/bin/start-keycloak.sh
RUN chmod +x /opt/keycloak/bin/start-keycloak.sh && \
    chown keycloak:keycloak /opt/keycloak/bin/start-keycloak.sh && \
    chown keycloak:keycloak /opt/keycloak/bin/parser.sh && \
    chown keycloak:keycloak /opt/keycloak/db_vars.env

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