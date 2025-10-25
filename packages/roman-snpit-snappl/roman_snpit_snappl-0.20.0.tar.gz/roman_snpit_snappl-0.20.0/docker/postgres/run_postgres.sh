#!/bin/bash

if [ ! -f $POSTGRES_DATA_DIR/PG_VERSION ]; then
    echo "Running initdb in $POSTGRES_DATA_DIR"
    /usr/lib/postgresql/15/bin/initdb -U postgres --pwfile=${PGPASSWDFILE:-/secrets/pgpasswd} $POSTGRES_DATA_DIR
    /usr/lib/postgresql/15/bin/pg_ctl -D $POSTGRES_DATA_DIR start
    psql --command "CREATE DATABASE roman_snpit OWNER postgres"
    psql --command "CREATE EXTENSION q3c" roman_snpit
    psql --command "CREATE EXTENSION pgcrypto" roman_snpit
    psql --command "CREATE EXTENSION pg_hint_plan" roman_snpit
    # psql --command "CREATE EXTENSION pg_parquet" roman_snpit
    ropasswd=`cat ${PGPASSWDFILE_RO:-/secrets/postgres_ro_password}`
    psql --command "CREATE USER postgres_ro PASSWORD '${ropasswd}'"
    psql --command "GRANT CONNECT ON DATABASE roman_snpit TO postgres_ro"
    psql --command "GRANT USAGE ON SCHEMA public TO postgres_ro" roman_snpit
    psql --command "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO postgres_ro" roman_snpit
    /usr/lib/postgresql/15/bin/pg_ctl -D $POSTGRES_DATA_DIR stop
fi
exec /usr/lib/postgresql/15/bin/postgres -c config_file=/etc/postgresql/15/main/postgresql.conf
