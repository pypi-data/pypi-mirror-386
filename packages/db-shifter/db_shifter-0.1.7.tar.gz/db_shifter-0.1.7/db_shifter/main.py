import psycopg2
from psycopg2.extras import RealDictCursor, Json
from importlib.metadata import version as _pkg_version, PackageNotFoundError as _PkgNotFound
import sys
import argparse
from collections import defaultdict

# ===================== CLI OPTIONS ===================== #
parser = argparse.ArgumentParser(description="Move missing rows from old Postgres DB to new one.")
parser.add_argument("--old-db-url", required=True, help="Old DB connection string")
parser.add_argument("--new-db-url", required=True, help="New DB connection string")
parser.add_argument("--dry-run", action="store_true", help="Don't insert, just show what would happen")
parser.add_argument("--verbose", action="store_true", help="Print all operations in detail")
parser.add_argument("--table", help="Sync just one table")
parser.add_argument("--skip-fk", action="store_true", help="Ignore foreign key errors")
# Version flag
def _resolve_version():
    try:
        return _pkg_version("db-shifter")
    except _PkgNotFound:
        return "unknown"
parser.add_argument("--version", action="version", version=f"%(prog)s {_resolve_version()}")
args = parser.parse_args()

# === A log of all table activities to generate final summary === #
sync_log = defaultdict(lambda: {"existing_new": 0, "existing_old": 0, "inserted": 0, "inserted_pks": []})


def quote_table(name: str) -> str:
    """Safely quote a table name with double quotes."""
    return f'"{name}"'


def quote_ident(name: str) -> str:
    """Safely quote a column name or identifier."""
    return f'"{name}"'


def get_all_tablez(conn):
    """Fetch all tables in the public schema."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname='public'
        """)
        return [row[0] for row in cur.fetchall()]


def sniff_primary_key(conn, table_name):
    """Identify the primary key column of a table."""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid
                                 AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = '{quote_table(table_name)}'::regclass
              AND i.indisprimary;
        """)
        res = cur.fetchone()
        return res[0] if res else None


def count_rows(conn, table_name):
    """Count number of rows in a table."""
    with conn.cursor() as cur:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {quote_table(table_name)}")
            return cur.fetchone()[0]
        except Exception:
            return 0


def pull_existing_ids(conn, table_name, pk):
    """Pull primary key values already in the new DB."""
    with conn.cursor() as cur:
        try:
            cur.execute(f"SELECT {quote_ident(pk)} FROM {quote_table(table_name)}")
            return set(row[0] for row in cur.fetchall())
        except Exception:
            return set()


def get_table_columns(conn, table_name):
    """Get column names, types, and constraints for a table."""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT 
                column_name, 
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        return {
            row[0]: {
                'type': row[1], 
                'nullable': row[2] == 'YES',
                'default': row[3]
            } 
            for row in cur.fetchall()
        }


def get_common_columns(source_conn, dest_conn, table_name):
    """Get columns that exist in both source and destination tables."""
    source_cols = get_table_columns(source_conn, table_name)
    dest_cols = get_table_columns(dest_conn, table_name)
    
    common_cols = set(source_cols.keys()) & set(dest_cols.keys())
    missing_in_dest = set(source_cols.keys()) - set(dest_cols.keys())
    missing_in_source = set(dest_cols.keys()) - set(source_cols.keys())
    
    if missing_in_dest:
        print(f"  📋 Columns in source but not destination: {sorted(missing_in_dest)}")
    if missing_in_source:
        print(f"  📋 Columns in destination but not source: {sorted(missing_in_source)}")
    
    # Check for NOT NULL constraints that might cause issues
    not_null_issues = []
    for col in common_cols:
        if not dest_cols[col]['nullable'] and col not in source_cols:
            not_null_issues.append(col)
    
    if not_null_issues:
        print(f"  ⚠️  NOT NULL columns missing from source: {not_null_issues}")
    
    return sorted(common_cols), missing_in_dest, missing_in_source, dest_cols


def pull_missing_rows(conn, table_name, pk, existing_ids, columns=None):
    """Get rows from old DB that are NOT present in new DB."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if columns:
            # Only select common columns
            column_list = ','.join([quote_ident(col) for col in columns])
            if not existing_ids:
                cur.execute(f"SELECT {column_list} FROM {quote_table(table_name)}")
            else:
                ids_tuple = tuple(existing_ids)
                cur.execute(
                    f"SELECT {column_list} FROM {quote_table(table_name)} WHERE {quote_ident(pk)} NOT IN %s", 
                    (ids_tuple,)
                )
        else:
            # Original behavior - select all columns
            if not existing_ids:
                cur.execute(f"SELECT * FROM {quote_table(table_name)}")
            else:
                ids_tuple = tuple(existing_ids)
                cur.execute(
                    f"SELECT * FROM {quote_table(table_name)} WHERE {quote_ident(pk)} NOT IN %s", 
                    (ids_tuple,)
                )
        return cur.fetchall()


def push_rows_to_new(conn, table_name, rows, pk, dry_run=False, verbose=False):
    """Insert missing rows into the new DB, optionally as dry-run."""
    if not rows:
        return
    keys = rows[0].keys()

    with conn.cursor() as cur:
        for row in rows:
            if verbose:
                print(f"  🧬 {row}")
            if dry_run:
                continue
            # Adapt Python dict/list values (e.g., JSON/JSONB columns) for psycopg2
            def _adapt_value(value):
                if isinstance(value, (dict, list)):
                    return Json(value)
                return value

            vals = [_adapt_value(row[k]) for k in keys]
            placeholders = ','.join(['%s'] * len(vals))
            columns = ','.join([quote_ident(k) for k in keys])
            try:
                cur.execute(
                    f"INSERT INTO {quote_table(table_name)} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                    vals
                )
                sync_log[table_name]["inserted_pks"].append(row.get(pk))
                sync_log[table_name]["inserted"] += 1
            except Exception as e:
                if args.skip_fk:
                    print(f"  ⚠️  FK error skipped: {e}")
                else:
                    raise e

    if not dry_run:
        conn.commit()


def sync_em_all(conn_old, conn_new):
    """Main sync function for all or specified tables."""
    tables = [args.table] if args.table else get_all_tablez(conn_old)
    print(f"🗃️ Found {len(tables)} tables to process")

    for table in tables:
        print(f"\n🚀 Syncing: {table}")
        pk = sniff_primary_key(conn_old, table)
        if not pk:
            print(f"⚠️ Skipping {table} (no PK found)")
            continue

        existing_old = count_rows(conn_old, table)
        existing_new_ids = pull_existing_ids(conn_new, table, pk)
        existing_new = len(existing_new_ids)

        # Detect schema differences and get common columns
        print(f"🔍 Analyzing schema for {table}...")
        common_cols, missing_in_dest, missing_in_source, dest_cols = get_common_columns(conn_old, conn_new, table)
        
        if not common_cols:
            print(f"⚠️  No common columns found between source and destination for {table}")
            continue
            
        if pk not in common_cols:
            print(f"⚠️  Primary key '{pk}' not found in common columns for {table}")
            continue

        rows = pull_missing_rows(conn_old, table, pk, existing_new_ids, common_cols)
        
        # Add default values for NOT NULL columns that are missing from source
        if rows:
            for row in rows:
                for col_name, col_info in dest_cols.items():
                    if col_name in common_cols and not col_info['nullable'] and col_name not in row:
                        # Provide smart defaults based on column type
                        if 'varchar' in col_info['type'] or 'text' in col_info['type']:
                            row[col_name] = f"migrated_{col_name}"
                        elif 'int' in col_info['type'] or 'numeric' in col_info['type']:
                            row[col_name] = 0
                        elif 'bool' in col_info['type']:
                            row[col_name] = False
                        else:
                            row[col_name] = col_info['default'] if col_info['default'] else f"migrated_{col_name}"
                        print(f"  🔧 Added default value for {col_name}: {row[col_name]}")

        sync_log[table]["existing_old"] = existing_old
        sync_log[table]["existing_new"] = existing_new

        print(f"📊 Old DB Rows: {existing_old} | New DB Rows (before): {existing_new}")
        print(f"📥 {len(rows)} new rows to insert")

        try:
            push_rows_to_new(conn_new, table, rows, pk, dry_run=args.dry_run, verbose=args.verbose)
            print(f"✅ Done with {table}")
        except Exception as e:
            print(f"❌ Error syncing {table}: {str(e)}")
            # Rollback the failed transaction to prevent "aborted transaction" errors
            try:
                conn_new.rollback()
                print(f"🔄 Rolled back transaction for {table}")
            except Exception as rollback_error:
                print(f"⚠️  Rollback failed for {table}: {rollback_error}")
                # If rollback fails, we need to start a new connection
                try:
                    conn_new.close()
                    conn_new = psycopg2.connect(args.new_db_url)
                    print(f"🔄 Created new connection after rollback failure")
                except Exception as reconnect_error:
                    print(f"💥 Failed to reconnect: {reconnect_error}")
                    break

    # === FINAL TOXIC REPORT === #
    print("\n📦 Final Sync Report:")
    for table, stats in sync_log.items():
        status = "✅ CHANGED" if stats["inserted"] else "❌ UNCHANGED"
        print(f"\n🧾 Table: {table} --- {status}")
        print(f"   🔢 Old DB Rows: {stats['existing_old']}")
        print(f"   🔢 New DB Rows (before): {stats['existing_new']}")
        print(f"   ➕ Rows Added: {stats['inserted']}")
        if stats["inserted_pks"]:
            print(f"   🧬 PKs Added: {stats['inserted_pks']}")


# ===================== BOOM 💣 ===================== #
def main():
    conn_old = psycopg2.connect(args.old_db_url)
    conn_new = psycopg2.connect(args.new_db_url)

    try:
        sync_em_all(conn_old, conn_new)
    finally:
        conn_old.close()
        conn_new.close()
