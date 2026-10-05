"""Consistent SQLite backup for a host-admin supplied protected destination.

Uses SQLite's backup API, including committed WAL data. Never replaces a file
or opens the source for writing. This is not a Firebird backup tool.
"""
import argparse
import json
from pathlib import Path
import sqlite3
import time


def backup_store(source, destination, timeout=60):
    source = Path(source).resolve(strict=True)
    destination = Path(destination).absolute()
    if not source.is_file() or source == destination.resolve():
        raise ValueError('Source and destination must be distinct files')
    if not destination.parent.is_dir():
        raise ValueError('Create a protected backup directory first')
    if timeout <= 0:
        raise ValueError('Backup timeout must be positive')
    # Exclusive creation protects previous backups, including symlink targets.
    with destination.open('xb'):
        pass
    started = time.monotonic()
    reader = writer = None
    try:
        reader = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=10)
        writer = sqlite3.connect(destination, timeout=10)

        def progress(status, remaining, total):
            if time.monotonic() - started > timeout:
                raise TimeoutError('Backup exceeded its deadline')

        reader.backup(writer, pages=128, progress=progress, sleep=0.1)
        if writer.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Backup integrity verification failed')
        writer.close()
        writer = None
        return {'backup_complete': True, 'integrity_check': 'ok'}
    except BaseException:
        if writer is not None:
            writer.close()
            writer = None
        destination.unlink(missing_ok=True)
        raise
    finally:
        if reader is not None:
            reader.close()
        if writer is not None:
            writer.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    config = json.loads((Path(__file__).resolve().parents[1] / 'config/api.local.json')
                        .read_text(encoding='utf-8-sig'))
    source = Path(config.get('approval_store_path') or '')
    destination = Path(args.destination)
    if not source.is_absolute() or not destination.is_absolute():
        raise SystemExit('Explicit absolute store and backup paths are required')
    try:
        print(json.dumps(backup_store(source, destination)))
    except (OSError, sqlite3.Error, ValueError) as error:
        # Avoid echoing local paths or database content into captured logs.
        raise SystemExit('Backup failed: ' + type(error).__name__) from None


if __name__ == '__main__':
    main()
