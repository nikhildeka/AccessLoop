import pytest
from extensions import db
from models import User, AuditLog


def test_password_is_hashed(app):
    u = User(email="a@b.demo", full_name="A", role="student")
    u.set_password("Str0ng!Pass")
    assert u.password_hash != "Str0ng!Pass" and u.check_password("Str0ng!Pass")


def test_audit_log_is_append_only(app):
    log = AuditLog(action="TEST", entity_type="x")
    db.session.add(log); db.session.commit()
    log.reason = "tamper"
    with pytest.raises(RuntimeError):
        db.session.commit()
    db.session.rollback()


def test_index_runs(client):
    assert client.get("/").status_code == 200
