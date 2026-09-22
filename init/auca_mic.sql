-- Bootstrap the auca_mic database on the SHARED postgres service.
--
-- This host uses ONE shared postgres role (from global.env) for every app —
-- no per-app role, just a per-app database owned by that shared user. The
-- ./init dir only runs on a FRESH (empty) pgdata volume; on the existing
-- volume, run this by hand instead:
--
--   docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE auca_mic;"'

CREATE DATABASE auca_mic;
