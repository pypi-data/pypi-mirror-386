#!/bin/bash

# Función para logging
log_info() {
    echo "[INFO] $*" >&2
}

# Parsear configuración siempre (URLs si están disponibles, o valores por defecto)
log_info "🔧 Parsing configuration at runtime..."

# Ejecutar parser para generar variables de entorno (siempre)
if [ -f "/opt/keycloak/bin/parser.sh" ]; then
    if /opt/keycloak/bin/parser.sh /opt/keycloak/db_vars.env; then
        log_info "📝 Successfully generated configuration file"
        if [ -n "${MAIN_DATABASE_URL:-}" ]; then
            log_info "📊 Database configuration from MAIN_DATABASE_URL"
        fi
        if [ -n "${MAIN_KEYCLOAK_URL:-}" ]; then
            log_info "👤 Admin credentials from MAIN_KEYCLOAK_URL"
        else
            log_info "👤 Admin credentials using defaults (admin/admin)"
        fi
    else
        log_info "⚠️  Parser failed, creating minimal defaults"
        cat > /opt/keycloak/db_vars.env << 'EOF'
# Parser failed - minimal defaults
export KEYCLOAK_ADMIN='admin'
export KEYCLOAK_ADMIN_PASSWORD='admin'
EOF
    fi
else
    log_info "⚠️  Parser script not found, creating minimal defaults"
    cat > /opt/keycloak/db_vars.env << 'EOF'
# Parser script not found - minimal defaults
export KEYCLOAK_ADMIN='admin'
export KEYCLOAK_ADMIN_PASSWORD='admin'
EOF
fi

# Cargar variables de base de datos parseadas
if [ -f "/opt/keycloak/db_vars.env" ]; then
    log_info "🔧 Loading database configuration..."
    source /opt/keycloak/db_vars.env
fi

echo "🔍 Database configuration check:"
echo "  KC_DB: ${KC_DB:-'not set'}"
echo "  KC_DB_URL: ${KC_DB_URL:-'not set'}"
echo ""

if [ -z "${KC_DB}" ]; then
    echo "🏃 Starting Keycloak in development mode (H2 database)..."
    
    # Intentar con import primero, si falla, continuar sin import
    if [ -f "/opt/keycloak/data/import/main-realm.json" ]; then
        echo "📥 Attempting to import realm configuration..."
        if ! /opt/keycloak/bin/kc.sh start-dev --import-realm --http-port=${KC_HTTP_PORT}; then
            echo "⚠️  Import failed, starting without import..."
            # exec /opt/keycloak/bin/kc.sh start-dev --http-port=${KC_HTTP_PORT}
            /opt/keycloak/bin/kc.sh start-dev --import-realm --http-port=${KC_HTTP_PORT} --verbose
        fi
    else
        echo "ℹ️  No realm configuration found, starting clean..."
        exec /opt/keycloak/bin/kc.sh start-dev --http-port=${KC_HTTP_PORT}
    fi
else
    echo "🏭 Starting Keycloak in production mode with external database..."
    echo "🔧 Building configuration for ${KC_DB}..."
    
    if ! /opt/keycloak/bin/kc.sh build --db=${KC_DB}; then
        echo "❌ Failed to build configuration for ${KC_DB}"
        exit 1
    fi
    
    if [ -f "/opt/keycloak/data/import/main-realm.json" ]; then
        echo "📥 Starting with realm import..."
        if ! /opt/keycloak/bin/kc.sh start --import-realm --http-port=${KC_HTTP_PORT}; then
            echo "⚠️  Import failed, starting without import..."  
            exec /opt/keycloak/bin/kc.sh start --http-port=${KC_HTTP_PORT}
        fi
    else
        echo "ℹ️  No realm configuration found, starting clean..."
        exec /opt/keycloak/bin/kc.sh start --http-port=${KC_HTTP_PORT}
    fi
fi