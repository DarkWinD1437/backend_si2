-- Script para configurar PostgreSQL para la Cooperativa SI2
-- Ejecutar como usuario postgres

-- 1. Crear la base de datos
DROP DATABASE IF EXISTS cooperativa_si2;
CREATE DATABASE cooperativa_si2
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Spanish_Bolivia.1252'
    LC_CTYPE = 'Spanish_Bolivia.1252'
    TEMPLATE = template0
    CONNECTION LIMIT = -1;

-- 2. Conectar a la nueva base de datos
\c cooperativa_si2;

-- 3. Crear extensiones útiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- 4. Crear esquemas si son necesarios
-- CREATE SCHEMA IF NOT EXISTS auditoria;
-- CREATE SCHEMA IF NOT EXISTS usuarios;
-- CREATE SCHEMA IF NOT EXISTS socios;

-- 5. Configurar parámetros específicos para auditoría
ALTER DATABASE cooperativa_si2 SET timezone TO 'America/La_Paz';
ALTER DATABASE cooperativa_si2 SET default_text_search_config TO 'spanish';

-- 6. Crear usuario específico para la aplicación (opcional)
-- DROP USER IF EXISTS cooperativa_user;
-- CREATE USER cooperativa_user WITH PASSWORD 'cooperativa_password123';
-- GRANT ALL PRIVILEGES ON DATABASE cooperativa_si2 TO cooperativa_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cooperativa_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cooperativa_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO cooperativa_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO cooperativa_user;

-- 7. Verificar la configuración
SELECT 
    datname as database_name,
    encoding,
    datcollate as collation,
    datctype as character_type
FROM pg_database 
WHERE datname = 'cooperativa_si2';

-- 8. Mostrar extensiones instaladas
SELECT extname as extension_name, extversion as version
FROM pg_extension
ORDER BY extname;
