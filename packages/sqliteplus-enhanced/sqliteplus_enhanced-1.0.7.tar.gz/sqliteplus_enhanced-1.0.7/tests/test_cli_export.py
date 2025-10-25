import sqlite3
from pathlib import Path

from click.testing import CliRunner

from sqliteplus.cli import cli
from sqliteplus.utils import replication_sync
from sqliteplus.utils.constants import DEFAULT_DB_PATH
from sqliteplus.utils.replication_sync import SQLiteReplication

import pytest


def _prepare_database(db_path: Path):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE valid_table (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
        )
        conn.executemany(
            "INSERT INTO valid_table (name) VALUES (?)",
            [("Alice",), ("Bob",)],
        )


def test_export_csv_cli_success(tmp_path):
    db_path = tmp_path / "test.db"
    output_path = tmp_path / "out.csv"
    _prepare_database(db_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "export-csv",
            "valid_table",
            str(output_path),
            "--db-path",
            str(db_path),
        ],
    )

    assert result.exit_code == 0, result.output
    content = output_path.read_text(encoding="utf-8").splitlines()
    assert content[0] == "id,name"
    assert content[1].endswith(",Alice")
    assert content[2].endswith(",Bob")


def test_export_csv_cli_rejects_invalid_table_name(tmp_path):
    db_path = tmp_path / "test.db"
    output_path = tmp_path / "out.csv"
    _prepare_database(db_path)

    runner = CliRunner()
    malicious_name = "valid_table; DROP TABLE logs;--"
    result = runner.invoke(
        cli,
        [
            "export-csv",
            malicious_name,
            str(output_path),
            "--db-path",
            str(db_path),
        ],
    )

    assert result.exit_code != 0
    assert "Nombre de tabla inválido" in result.output
    assert not output_path.exists()


def test_backup_cli_creates_backup_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        db_path = Path(DEFAULT_DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY)")
            conn.execute("INSERT INTO demo DEFAULT VALUES")

        result = runner.invoke(cli, ["backup"])

        assert result.exit_code == 0, result.output
        backups_dir = Path("backups")
        backups = sorted(backups_dir.glob("backup_*.db"))
        assert backups, "No se creó ningún archivo de respaldo"
        assert backups[0].stat().st_size > 0


def test_backup_cli_reports_missing_source_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["backup"])

        assert result.exit_code != 0
        assert "Error al realizar la copia de seguridad" in result.output
        assert "Copia de seguridad creada correctamente." not in result.output
        backups_dir = Path("backups")
        assert not list(backups_dir.glob("backup_*.db"))


def test_replicate_database_raises_runtime_error(tmp_path):
    replicator = SQLiteReplication(db_path=tmp_path / "missing.db")
    target_path = tmp_path / "replica.db"

    with pytest.raises(RuntimeError) as excinfo:
        replicator.replicate_database(str(target_path))

    assert "Error en la replicación" in str(excinfo.value)
    assert not target_path.exists()


def test_backup_and_replication_preserve_wal_changes(tmp_path):
    db_path = tmp_path / "wal_source.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;").fetchone()
        conn.execute(
            "CREATE TABLE data (id INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT)"
        )
        conn.execute("INSERT INTO data (value) VALUES (?)", ("desde_wal",))
        conn.commit()

    wal_path = Path(str(db_path) + "-wal")
    assert wal_path.exists(), "Se esperaba la creación del archivo WAL"

    replicator = SQLiteReplication(
        db_path=str(db_path), backup_dir=str(tmp_path / "backups")
    )

    backup_file = Path(replicator.backup_database())
    with sqlite3.connect(backup_file) as conn:
        values = conn.execute("SELECT value FROM data").fetchall()
    assert values == [("desde_wal",)]

    replica_path = tmp_path / "replicas" / "replica.db"
    replicated_file = Path(replicator.replicate_database(str(replica_path)))
    with sqlite3.connect(replicated_file) as conn:
        values = conn.execute("SELECT value FROM data").fetchall()
    assert values == [("desde_wal",)]


def test_backup_database_reuses_cipher_key(tmp_path, monkeypatch):
    key = "clave-secreta"
    calls = []

    def record_cipher(conn, cipher):
        calls.append(cipher)

    monkeypatch.setattr(replication_sync, "apply_cipher_key", record_cipher)

    db_path = tmp_path / "cipher.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE ejemplo (id INTEGER PRIMARY KEY)")

    replicator = SQLiteReplication(
        db_path=str(db_path), backup_dir=str(tmp_path / "backups"), cipher_key=key
    )

    backup_path = replicator.backup_database()

    assert Path(backup_path).exists()
    assert calls == [key, key]


def test_export_uses_cipher_key(tmp_path, monkeypatch):
    key = "otra-clave"
    calls = []

    def record_cipher(conn, cipher):
        calls.append(cipher)

    monkeypatch.setattr(replication_sync, "apply_cipher_key", record_cipher)

    db_path = tmp_path / "cipher.db"
    _prepare_database(db_path)
    output = tmp_path / "out.csv"

    replicator = SQLiteReplication(
        db_path=str(db_path), backup_dir=str(tmp_path / "backups"), cipher_key=key
    )

    replicator.export_to_csv("valid_table", str(output))

    assert output.exists()
    assert calls == [key]
