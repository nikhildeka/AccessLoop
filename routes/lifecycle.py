from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models import Booking, ConditionReport, AuditLog

bp = Blueprint("lifecycle", __name__)


def verify_owner(booking):
    if current_user.role not in ("owner", "manager", "admin"):
        abort(403)

    if booking.resource.institution_id != current_user.institution_id:
        abort(403)

    if current_user.role == "owner":
        if booking.resource.owner_id != current_user.id:
            abort(403)

    if current_user.role == "manager":
        if not booking.resource.requires_manager_approval:
            abort(403)


@bp.route("/owner/lifecycle")
@login_required
def lifecycle_dashboard():

    if current_user.role not in ("owner", "manager", "admin"):
        abort(403)

    query = Booking.query.join(
        Booking.resource
    ).filter(
        Booking.status.in_(["APPROVED", "CHECKED_IN"])
    )

    if current_user.role == "owner":
        query = query.filter(
            Booking.resource.has(owner_id=current_user.id)
        )

    elif current_user.role == "manager":
        query = query.filter(
            Booking.resource.has(
                requires_manager_approval=True,
                institution_id=current_user.institution_id
            )
        )

    else:
        query = query.filter(
            Booking.resource.has(
                institution_id=current_user.institution_id
            )
        )

    bookings = query.order_by(Booking.start_time).all()

    return render_template(
        "lifecycle.html",
        bookings=bookings
    )


@bp.route("/owner/lifecycle/<int:booking_id>", methods=["POST"])
@login_required
def update_lifecycle(booking_id):

    booking = Booking.query.get_or_404(booking_id)
    verify_owner(booking)

    action = request.form.get("action")
    condition = request.form.get("condition")
    accessories = request.form.get("accessories", "").strip()
    description = request.form.get("description", "").strip()

    if condition not in (
        "EXCELLENT", "GOOD", "FAIR",
        "DAMAGED", "MISSING_COMPONENTS"
    ):
        abort(400)

    if len(accessories) > 500 or len(description) > 2000:
        abort(400)

    if action == "handover" and booking.status == "APPROVED":

        booking.status = "CHECKED_IN"
        booking.checked_in_at = datetime.now()

        report_type = "INITIAL"
        audit_action = "EQUIPMENT_HANDED_OVER"

    elif action == "return" and booking.status == "CHECKED_IN":

        booking.status = "RETURNED"
        booking.returned_at = datetime.now()

        report_type = "FINAL"
        audit_action = "EQUIPMENT_RETURNED"

    else:
        flash("This booking cannot undergo that operation.")
        return redirect(url_for("lifecycle.lifecycle_dashboard"))

    db.session.add(ConditionReport(
        booking_id=booking.id,
        report_type=report_type,
        condition=condition,
        accessories=accessories,
        description=description,
        reported_by=current_user.id
    ))

    db.session.add(AuditLog(
        actor_id=current_user.id,
        action=audit_action,
        entity_type="Booking",
        entity_id=booking.id,
        previous_state="APPROVED" if action == "handover" else "CHECKED_IN",
        new_state=booking.status,
        reason=description
    ))

    db.session.commit()

    flash("Equipment transaction recorded successfully!", "success")

    return redirect(url_for("lifecycle.lifecycle_dashboard"))