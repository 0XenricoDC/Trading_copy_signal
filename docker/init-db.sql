-- Initialize TradeCopy Database with Row-Level Security

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create app user for RLS
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'tradecopy_app') THEN
        CREATE ROLE tradecopy_app LOGIN PASSWORD 'tradecopy_app_secret';
    END IF;
END
$$;

-- Grant basic privileges
GRANT CONNECT ON DATABASE tradecopy TO tradecopy_app;
GRANT USAGE ON SCHEMA public TO tradecopy_app;

-- Note: Tables will be created by Alembic migrations
-- This file sets up the foundation for RLS

-- Function to get current tenant from session
CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_tenant_id', true), '')::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to set current tenant
CREATE OR REPLACE FUNCTION set_current_tenant(tenant_id UUID) RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', tenant_id::text, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
