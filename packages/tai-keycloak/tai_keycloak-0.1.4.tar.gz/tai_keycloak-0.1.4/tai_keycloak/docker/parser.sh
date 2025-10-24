#!/bin/bash

# Script para parsear MAIN_DATABASE_URL y MAIN_KEYCLOAK_URL y crear archivo .env con variables de Keycloak
# Convierte URLs de base de datos y Keycloak en un archivo .env para Keycloak

set -euo pipefail

# Función para mostrar ayuda
show_help() {
    cat << EOF
Uso: $0 [archivo_salida]

Este script parsea las variables de entorno MAIN_DATABASE_URL y MAIN_KEYCLOAK_URL 
y crea un archivo .env con las variables de entorno necesarias para Keycloak.

Argumentos:
    archivo_salida    Archivo donde escribir las variables (por defecto: db_vars.env)

Opciones:
    -h, --help        Muestra esta ayuda

Variables generadas en el archivo:
    KC_DB               - Tipo de base de datos (postgres, mysql, etc.)
    KC_DB_URL           - URL JDBC para Keycloak
    KC_DB_USERNAME      - Usuario de la base de datos
    KC_DB_PASSWORD      - Contraseña de la base de datos
    KC_DB_URL_DATABASE  - Nombre de la base de datos (siempre 'keycloak')
    KEYCLOAK_ADMIN      - Usuario administrador de Keycloak
    KEYCLOAK_ADMIN_PASSWORD - Contraseña del administrador

Formato esperado de MAIN_DATABASE_URL:
    driver://username:password@host:port/database

Formato esperado de MAIN_KEYCLOAK_URL:
    [protocol://][username[:password]@]host[:port]

Ejemplos:
    $0                          # Crea db_vars.env
    $0 keycloak.env            # Crea keycloak.env
    
    export MAIN_DATABASE_URL='postgresql://user:pass@localhost:5432/mydb'
    export MAIN_KEYCLOAK_URL='admin:secret@localhost:8080'
    $0

Nota: El nombre de la base de datos siempre se fuerza a 'keycloak'
EOF
}

# Archivo de salida por defecto
OUTPUT_FILE="db_vars.env"

# Procesar argumentos de línea de comandos
if [[ $# -gt 0 ]]; then
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            OUTPUT_FILE="$1"
            ;;
    esac
fi

# Función para logging
log_info() {
    echo "[INFO] $*" >&2
}

# Función para URL decode
url_decode() {
    local url_encoded="${1//+/ }"
    printf '%b' "${url_encoded//%/\\x}"
}

# Función para parsear MAIN_KEYCLOAK_URL y extraer credenciales de admin
parse_keycloak_url() {
    local url="$1"
    
    log_info "Parseando URL de Keycloak..."
    
    # Patrón: [protocol://][user[:password]@]host[:port]
    local pattern='^([^:]+://)?(?:([^:@]+)(?::([^@]+))?@)?([^:/]+)(?::([0-9]+))?$'
    
    # Usar regex más simple para bash
    if [[ "$url" =~ ^(([^:]+)://)?((([^:@]+)(:([^@]+))?@)?([^:/]+)(:([0-9]+))?)$ ]]; then
        local protocol="${BASH_REMATCH[2]}"
        local username="${BASH_REMATCH[5]}"
        local password="${BASH_REMATCH[7]}"
        local host="${BASH_REMATCH[8]}"
        local port="${BASH_REMATCH[10]}"
        
        # Validar que al menos tengamos host
        if [[ -z "$host" ]]; then
            echo "Error: Host no especificado en MAIN_KEYCLOAK_URL" >&2
            return 1
        fi
        
        # Decodificar credenciales si existen
        if [[ -n "$username" ]]; then
            username=$(url_decode "$username")
        fi
        
        if [[ -n "$password" ]]; then
            password=$(url_decode "$password")
        fi
        
        # Exportar variables encontradas
        if [[ -n "$username" ]]; then
            export PARSED_KEYCLOAK_ADMIN="$username"
            log_info "Usuario administrador extraído de MAIN_KEYCLOAK_URL"
        fi
        
        if [[ -n "$password" ]]; then
            export PARSED_KEYCLOAK_ADMIN_PASSWORD="$password"
            log_info "Contraseña de administrador extraída de MAIN_KEYCLOAK_URL"
        fi
        
        return 0
    else
        echo "Error: No se pudo parsear MAIN_KEYCLOAK_URL: $url" >&2
        return 1
    fi
}

# Función para parsear la URL de base de datos y escribir archivo .env
parse_database_url() {
    local url="$1"
    local output_file="$2"
    
    log_info "Parseando URL de base de datos..."
    
    # Verificar formato básico
    if [[ ! "$url" =~ :// ]]; then
        echo "Error: URL debe tener el formato driver://user:pass@host:port/db" >&2
        return 1
    fi
    
    # Extraer componentes usando regex
    if [[ "$url" =~ ^([^:]+)://((([^:@]+)(:([^@]*))?@)?([^:/]+)(:([0-9]+))?)?(/(.*))?(\?(.*))?$ ]]; then
        local driver="${BASH_REMATCH[1]}"
        local username="${BASH_REMATCH[4]}"
        local password="${BASH_REMATCH[6]}"
        local host="${BASH_REMATCH[7]}"
        local port="${BASH_REMATCH[9]}"
        local database_part="${BASH_REMATCH[11]}"
        local query_params="${BASH_REMATCH[13]}"
        
        # Validar componentes esenciales
        if [[ -z "$driver" ]]; then
            echo "Error: Driver no especificado en la URL" >&2
            return 1
        fi
        
        if [[ -z "$host" ]]; then
            echo "Error: Host no especificado en la URL" >&2
            return 1
        fi
        
        # Decodificar URL para username y password si existen
        if [[ -n "$username" ]]; then
            username=$(url_decode "$username")
        fi
        
        if [[ -n "$password" ]]; then
            password=$(url_decode "$password")
        fi
        
        # Asignar puertos por defecto si no se especifica
        if [[ -z "$port" ]]; then
            case "$driver" in
                postgresql|postgres)
                    port=5432
                    ;;
                mysql)
                    port=3306
                    ;;
                sqlite)
                    port=""
                    ;;
                mssql)
                    port=1433
                    ;;
                oracle)
                    port=1521
                    ;;
            esac
        fi
        
        # Mapear driver a tipo de KC_DB
        local kc_db_type=""
        case "$driver" in
            postgresql|postgres)
                kc_db_type="postgres"
                ;;
            mysql)
                kc_db_type="mysql"
                ;;
            sqlite)
                kc_db_type="sqlite"
                ;;
            *)
                echo "Advertencia: Driver '$driver' no soportado, archivo vacío generado" >&2
                echo "# Driver '$driver' no soportado - usando H2 por defecto" > "$output_file"
                return 0
                ;;
        esac
        
        # Construir URL JDBC para Keycloak (siempre usa database 'keycloak')
        local jdbc_url=""
        if [[ -n "$kc_db_type" && "$kc_db_type" != "sqlite" ]]; then
            jdbc_url="jdbc:${driver}://${host}"
            if [[ -n "$port" ]]; then
                jdbc_url="${jdbc_url}:${port}"
            fi
            jdbc_url="${jdbc_url}/keycloak"
            
            # Agregar parámetros de query si existen
            if [[ -n "$query_params" ]]; then
                jdbc_url="${jdbc_url}?${query_params}"
            fi
        fi
        
        # Escribir variables de base de datos al archivo
        cat > "$output_file" << EOF
# Configuración de base de datos para Keycloak
# Generado automáticamente desde MAIN_DATABASE_URL
export KC_DB='$kc_db_type'
export KC_DB_URL='$jdbc_url'
export KC_DB_USERNAME='$username'
export KC_DB_PASSWORD='$password'
export KC_DB_URL_DATABASE='keycloak'
EOF
        
        log_info "Variables de base de datos configuradas para driver: $driver"
        
        return 0
    else
        echo "Error: No se pudo parsear la URL de base de datos" >&2
        return 1
    fi
}

# Función para agregar variables de administrador de Keycloak al archivo
append_keycloak_admin_vars() {
    local output_file="$1"
    local from_url="$2"  # true si viene de MAIN_KEYCLOAK_URL, false si son valores por defecto
    
    # Determinar valores a usar (parseados o por defecto)
    local admin_user="${PARSED_KEYCLOAK_ADMIN:-admin}"
    local admin_password="${PARSED_KEYCLOAK_ADMIN_PASSWORD:-admin}"
    
    # Determinar el origen de la configuración para el comentario
    local source_comment=""
    if [[ "$from_url" == "true" ]]; then
        source_comment="# Generado automáticamente desde MAIN_KEYCLOAK_URL"
    else
        source_comment="# Valores por defecto (no se encontró MAIN_KEYCLOAK_URL)"
    fi
    
    # Agregar configuración de administrador al archivo
    cat >> "$output_file" << EOF

# Configuración de administrador de Keycloak
$source_comment
export KEYCLOAK_ADMIN='$admin_user'
export KEYCLOAK_ADMIN_PASSWORD='$admin_password'
EOF
    
    if [[ "$from_url" == "true" ]]; then
        log_info "Credenciales de administrador agregadas desde MAIN_KEYCLOAK_URL"
    else
        log_info "Credenciales de administrador configuradas con valores por defecto"
    fi
}

# Función principal
main() {
    local has_database_url=false
    local has_keycloak_url=false
    
    # Verificar qué variables están disponibles
    if [[ -n "${MAIN_DATABASE_URL:-}" ]]; then
        has_database_url=true
        log_info "MAIN_DATABASE_URL encontrada"
    fi
    
    if [[ -n "${MAIN_KEYCLOAK_URL:-}" ]]; then
        has_keycloak_url=true
        log_info "MAIN_KEYCLOAK_URL encontrada"
    fi
    
    # Nota: Ya no es necesario que alguna variable esté definida, 
    # ya que siempre generaremos al menos las credenciales por defecto
    
    # Crear archivo base o vacío
    if [[ "$has_database_url" == true ]]; then
        log_info "Procesando MAIN_DATABASE_URL..."
        if ! parse_database_url "$MAIN_DATABASE_URL" "$OUTPUT_FILE"; then
            echo "Error: No se pudo procesar MAIN_DATABASE_URL" >&2
            exit 1
        fi
    else
        # Crear archivo con encabezado si solo tenemos MAIN_KEYCLOAK_URL
        cat > "$OUTPUT_FILE" << EOF
# Configuración para Keycloak
# Generado automáticamente
EOF
    fi
    
    # Procesar MAIN_KEYCLOAK_URL si está disponible, o usar valores por defecto
    if [[ "$has_keycloak_url" == true ]]; then
        log_info "Procesando MAIN_KEYCLOAK_URL..."
        if parse_keycloak_url "$MAIN_KEYCLOAK_URL"; then
            append_keycloak_admin_vars "$OUTPUT_FILE" "true"
        else
            echo "Advertencia: No se pudo procesar MAIN_KEYCLOAK_URL, usando valores por defecto" >&2
            append_keycloak_admin_vars "$OUTPUT_FILE" "false"
        fi
    else
        log_info "MAIN_KEYCLOAK_URL no encontrada, usando credenciales por defecto"
        append_keycloak_admin_vars "$OUTPUT_FILE" "false"
    fi
    
    log_info "¡Archivo .env creado exitosamente!"
    echo "📁 Archivo generado: $OUTPUT_FILE"
    echo "🔧 Variables de Keycloak listas para usar"
}

# Ejecutar función principal
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi