"""Read-only metadata evidence for OBJOBJ triggers and declared dependencies.

Run from the Medicus repository root on the DB host. No patient rows queried.
Metadata is evidence of possible effects, not proof that a GUI path executes them.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / 'scripts'))
import fdb
from db import _load_db_config


def rows(cursor, query, args=()):
    cursor.execute(query, args)
    names = [c[0].strip().lower() for c in cursor.description]
    result = []
    for values in cursor.fetchall():
        row = {}
        for key, value in zip(names, values):
            if hasattr(value, 'read'):
                value = value.read()
            row[key] = value.strip() if isinstance(value, str) else value
        result.append(row)
    return result


def main():
    config = _load_db_config()
    laser = json.loads(Path('config/laser_calendar.local.json').read_text(encoding='utf-8-sig'))
    result = {'captured_at_utc': datetime.now(timezone.utc).isoformat(), 'databases': {}}
    for namespace, database in [('MAIN', config['database']), ('LASER', laser['database'])]:
        con = fdb.connect(host=config['host'], port=config['port'], database=database,
                          user=config['username'], password=config['password'],
                          charset=config.get('charset', 'UTF8'))
        try:
            con.default_tpb = (fdb.isc_tpb_version3, fdb.isc_tpb_read,
                               fdb.isc_tpb_concurrency, fdb.isc_tpb_nowait)
            cursor = con.cursor()
            triggers = rows(cursor, 'SELECT RDB$TRIGGER_NAME AS NAME, RDB$TRIGGER_TYPE AS TYPE, '
                'RDB$TRIGGER_INACTIVE AS INACTIVE, RDB$TRIGGER_SEQUENCE AS SEQUENCE, '
                'RDB$SYSTEM_FLAG AS SYSTEM_FLAG, RDB$TRIGGER_SOURCE AS SOURCE FROM RDB$TRIGGERS '
                'WHERE RDB$RELATION_NAME=? ORDER BY RDB$TRIGGER_SEQUENCE,RDB$TRIGGER_NAME', ('OBJOBJ',))
            dependencies, procedures, visited = [], [], set()
            queue = [(t['name'], 2) for t in triggers]
            while queue:
                name, kind = queue.pop(0)
                if (name, kind) in visited:
                    continue
                visited.add((name, kind))
                deps = rows(cursor, 'SELECT RDB$DEPENDENT_NAME AS DEPENDENT_NAME, '
                    'RDB$DEPENDENT_TYPE AS DEPENDENT_TYPE, RDB$DEPENDED_ON_NAME AS TARGET_NAME, '
                    'RDB$DEPENDED_ON_TYPE AS TARGET_TYPE, RDB$FIELD_NAME AS FIELD_NAME '
                    'FROM RDB$DEPENDENCIES WHERE RDB$DEPENDENT_NAME=? AND RDB$DEPENDENT_TYPE=?',
                    (name, kind))
                dependencies.extend(deps)
                for dep in deps:
                    if dep['target_type'] == 5 and (dep['target_name'], 5) not in visited:
                        queue.append((dep['target_name'], 5))
                if kind == 5:
                    procedures.extend(rows(cursor, 'SELECT RDB$PROCEDURE_NAME AS NAME, '
                        'RDB$PROCEDURE_SOURCE AS SOURCE FROM RDB$PROCEDURES WHERE RDB$PROCEDURE_NAME=?', (name,)))
            incoming = rows(cursor, 'SELECT RDB$DEPENDENT_NAME AS NAME, RDB$DEPENDENT_TYPE AS TYPE, '
                'RDB$FIELD_NAME AS FIELD_NAME FROM RDB$DEPENDENCIES WHERE RDB$DEPENDED_ON_NAME=?', ('OBJOBJ',))
            constraints = rows(cursor, 'SELECT C.RDB$CONSTRAINT_NAME AS NAME, '
                'C.RDB$CONSTRAINT_TYPE AS TYPE, R.RDB$CONST_NAME_UQ AS REFERENCED_CONSTRAINT, '
                'R.RDB$UPDATE_RULE AS UPDATE_RULE, R.RDB$DELETE_RULE AS DELETE_RULE '
                'FROM RDB$RELATION_CONSTRAINTS C LEFT JOIN RDB$REF_CONSTRAINTS R '
                'ON R.RDB$CONSTRAINT_NAME=C.RDB$CONSTRAINT_NAME WHERE C.RDB$RELATION_NAME=?', ('OBJOBJ',))
            incoming_keys = rows(cursor,
                'SELECT CHILD.RDB$RELATION_NAME AS CHILD_TABLE, CHILD.RDB$CONSTRAINT_NAME AS NAME, '
                'CS.RDB$FIELD_NAME AS CHILD_FIELD, PS.RDB$FIELD_NAME AS PARENT_FIELD, '
                'RC.RDB$UPDATE_RULE AS UPDATE_RULE, RC.RDB$DELETE_RULE AS DELETE_RULE '
                'FROM RDB$REF_CONSTRAINTS RC '
                'JOIN RDB$RELATION_CONSTRAINTS CHILD ON CHILD.RDB$CONSTRAINT_NAME=RC.RDB$CONSTRAINT_NAME '
                'JOIN RDB$RELATION_CONSTRAINTS PARENT ON PARENT.RDB$CONSTRAINT_NAME=RC.RDB$CONST_NAME_UQ '
                'JOIN RDB$INDEX_SEGMENTS CS ON CS.RDB$INDEX_NAME=CHILD.RDB$INDEX_NAME '
                'JOIN RDB$INDEX_SEGMENTS PS ON PS.RDB$INDEX_NAME=PARENT.RDB$INDEX_NAME '
                'AND PS.RDB$FIELD_POSITION=CS.RDB$FIELD_POSITION '
                'WHERE PARENT.RDB$RELATION_NAME=?', ('OBJOBJ',))
            child_triggers = {}
            child_fields = {}
            for table in sorted({key['child_table'] for key in incoming_keys}):
                child_triggers[table] = rows(cursor,
                    'SELECT RDB$TRIGGER_NAME AS NAME, RDB$TRIGGER_TYPE AS TYPE, '
                    'RDB$TRIGGER_INACTIVE AS INACTIVE, RDB$TRIGGER_SOURCE AS SOURCE '
                    'FROM RDB$TRIGGERS WHERE RDB$RELATION_NAME=? AND COALESCE(RDB$SYSTEM_FLAG,0)=0', (table,))
                child_fields[table] = rows(cursor,
                    'SELECT RDB$FIELD_NAME AS NAME, RDB$FIELD_POSITION AS FIELD_ORDINAL, '
                    'RDB$NULL_FLAG AS NOT_NULL FROM RDB$RELATION_FIELDS '
                    'WHERE RDB$RELATION_NAME=? ORDER BY RDB$FIELD_POSITION', (table,))
            # Known discovered relation only: count links, never export patient rows.
            procedure_links = rows(cursor,
                'SELECT COUNT(*) AS LINKS, COUNT(DISTINCT P.IDOBJ) AS APPOINTMENTS '
                'FROM OBJPROC P JOIN OBJOBJ O ON O.IDOBJ=P.IDOBJ '
                'WHERE O.DATUM BETWEEN ? AND ?', ('2026-09-01', '2026-11-30')) if 'OBJPROC' in child_fields else []
            result['databases'][namespace] = {'triggers': triggers, 'dependencies': dependencies,
                'incoming_foreign_keys': incoming_keys, 'child_table_triggers': child_triggers,
                'child_fields': child_fields, 'objproc_links_sep_nov_2026': procedure_links,
                'procedures': procedures, 'incoming_dependencies': incoming, 'constraints': constraints}
        finally:
            con.rollback()
            con.close()
    print(json.dumps(result, ensure_ascii=True, default=str, indent=2))


if __name__ == '__main__':
    main()
