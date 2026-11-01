from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import event
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager

ROLES = ("student", "owner", "manager", "admin")
BOOKING_STATES = ("PENDING", "APPROVED", "REJECTED", "WAITLISTED",
                  "CHECKED_IN", "RETURNED", "CANCELLED")
INCIDENT_STATES = ("REPORTED", "UNDER_REVIEW", "RESOLVED", "ESCALATED")
CONDITIONS = ("EXCELLENT", "GOOD", "FAIR", "DAMAGED", "MISSING_COMPONENTS")


def utcnow():
    return datetime.now(timezone.utc)


class Institution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student", index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey("institution.id"))
    is_verified = db.Column(db.Boolean, default=False)   # institutional membership
    is_suspended = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    institution = db.relationship("Institution")
    __table_args__ = (db.CheckConstraint(
        "role IN ('student','owner','manager','admin')", name="ck_user_role"),)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))


class Qualification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class UserQualification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    qualification_id = db.Column(db.Integer, db.ForeignKey("qualification.id"), nullable=False)
    verified_by = db.Column(db.Integer, db.ForeignKey("user.id"))  # manager
    verified_at = db.Column(db.DateTime)
    __table_args__ = (db.UniqueConstraint("user_id", "qualification_id"),)
    qualification = db.relationship("Qualification")


class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey("institution.id"))
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False, index=True)
    location = db.Column(db.String(120), index=True)
    image_filename = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=1, nullable=False)
    condition = db.Column(db.String(20), default="GOOD")
    usage_instructions = db.Column(db.Text)
    restrictions = db.Column(db.Text)
    required_qualification_id = db.Column(db.Integer, db.ForeignKey("qualification.id"))
    max_booking_hours = db.Column(db.Integer, default=24)
    requires_manager_approval = db.Column(db.Boolean, default=False)  # mandatory human safety approval
    maintenance_status = db.Column(db.String(20), default="OK")  # OK / MAINTENANCE / SUSPENDED
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    owner = db.relationship("User", foreign_keys=[owner_id])
    required_qualification = db.relationship("Qualification")


class ResourceAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resource.id"), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_blackout = db.Column(db.Boolean, default=False)  # temporary unavailability
    note = db.Column(db.String(200))


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resource.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False)
    purpose = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="PENDING", index=True)
    decision_reason = db.Column(db.String(500))
    decided_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    checked_in_at = db.Column(db.DateTime)
    returned_at = db.Column(db.DateTime)
    handover_token = db.Column(db.String(64), unique=True)  # for QR (P2)
    created_at = db.Column(db.DateTime, default=utcnow)
    resource = db.relationship("Resource")
    user = db.relationship("User", foreign_keys=[user_id])
    __table_args__ = (db.CheckConstraint("end_time > start_time", name="ck_booking_time"),)


class WaitlistEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resource.id"), nullable=False, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    priority_reason = db.Column(db.String(300))  # transparent explanation
    created_at = db.Column(db.DateTime, default=utcnow)


class ConditionReport(db.Model):
    """Never updated; one row per report so history is preserved."""
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=False, index=True)
    report_type = db.Column(db.String(10), nullable=False)  # INITIAL / FINAL
    condition = db.Column(db.String(20), nullable=False)
    accessories = db.Column(db.String(500))
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(100))
    reported_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)


class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"))
    resource_id = db.Column(db.Integer, db.ForeignKey("resource.id"), nullable=False)
    reported_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="REPORTED", index=True)
    findings = db.Column(db.Text)
    resolution_notes = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=utcnow)
    resolved_at = db.Column(db.DateTime)


class AuditLog(db.Model):
    """Append-only: updates/deletes through the ORM are blocked below."""
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    action = db.Column(db.String(60), nullable=False, index=True)
    entity_type = db.Column(db.String(40), nullable=False)
    entity_id = db.Column(db.Integer)
    previous_state = db.Column(db.String(60))
    new_state = db.Column(db.String(60))
    reason = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=utcnow, index=True)


@event.listens_for(AuditLog, "before_update")
@event.listens_for(AuditLog, "before_delete")
def _audit_is_append_only(mapper, connection, target):
    raise RuntimeError("AuditLog is append-only")


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    message = db.Column(db.String(300), nullable=False)
    link = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
