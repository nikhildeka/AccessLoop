from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import or_

from extensions import db
from models import Booking, Resource, AuditLog, Notification

bp = Blueprint("approvals", __name__)


@bp.route("/owner/requests")
@login_required
def pending_requests():

    if current_user.role not in ("owner", "manager", "admin"):
        abort(403)

    query = Booking.query.join(Resource).filter(
        Booking.status == "PENDING"
    )

    if current_user.role == "owner":
        query = query.filter(Resource.owner_id == current_user.id)

    elif current_user.role == "manager":
        query = query.filter(
            or_(
                Resource.requires_manager_approval.is_(True),
                Resource.institution_id == current_user.institution_id
            )
        )

    else:
        query = query.filter(
            Resource.institution_id == current_user.institution_id
        )

    bookings = query.order_by(Booking.created_at.asc()).all()

    return render_template(
        "owner_requests.html",
        bookings=bookings
    )


@bp.route("/owner/requests/<int:booking_id>/decision", methods=["POST"])
@login_required
def decide_booking(booking_id):

    if current_user.role not in ("owner", "manager", "admin"):
        abort(403)

    booking = Booking.query.get_or_404(booking_id)
    resource = booking.resource

    if resource.institution_id != current_user.institution_id:
        abort(403)

    if current_user.role == "owner" and resource.owner_id != current_user.id:
        abort(403)

    if current_user.role == "manager" and not resource.requires_manager_approval:
        abort(403)

    if current_user.role == "admin":
        pass

    decision = request.form.get("decision")
    reason = request.form.get("reason", "").strip()

    if decision not in ("APPROVED", "REJECTED"):
        abort(400)

    if not reason or len(reason) > 500:
        flash("Please provide a decision reason (maximum 500 characters).")
        return redirect(url_for("approvals.pending_requests"))

    if booking.status != "PENDING":
        flash("This booking has already been processed.")
        return redirect(url_for("approvals.pending_requests"))

    if decision == "APPROVED":

        conflict = Booking.query.filter(
            Booking.resource_id == resource.id,
            Booking.id != booking.id,
            Booking.status.in_(["APPROVED", "CHECKED_IN"]),
            Booking.start_time < booking.end_time,
            Booking.end_time > booking.start_time
        ).first()

        if conflict:
            flash("This resource has already been booked during that period.")
            return redirect(url_for("approvals.pending_requests"))

    old_status = booking.status

    booking.status = decision
    booking.decided_by = current_user.id
    booking.decision_reason = reason

    db.session.add(AuditLog(
        actor_id=current_user.id,
        action="BOOKING_DECISION",
        entity_type="Booking",
        entity_id=booking.id,
        previous_state=old_status,
        new_state=decision,
        reason=reason
    ))

    db.session.add(Notification(
        user_id=booking.user_id,
        message=f"Your request for {resource.name} was {decision.lower()}."
    ))

    db.session.commit()

    flash(f"Booking successfully {decision.lower()}!", "success")

    return redirect(url_for("approvals.pending_requests"))