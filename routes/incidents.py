from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models import Booking, Incident, Resource

bp = Blueprint("incidents", __name__)


@bp.route("/incidents", methods=["GET", "POST"])
@login_required
def incidents_page():

    if request.method == "POST":
        booking_id = request.form.get("booking_id", type=int)
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()

        booking = Booking.query.filter_by(
            id=booking_id,
            user_id=current_user.id
        ).first()

        if not booking:
            flash("Invalid booking selected.", "danger")
            return redirect(url_for("incidents.incidents_page"))

        if booking.status not in ["CHECKED_IN", "RETURNED"]:
            flash("You can report incidents only for active or completed bookings.", "danger")
            return redirect(url_for("incidents.incidents_page"))

        if not category or not description:
            flash("Please complete all fields.", "danger")
            return redirect(url_for("incidents.incidents_page"))

        incident = Incident(
            booking_id=booking.id,
            resource_id=booking.resource_id,
            reported_by=current_user.id,
            category=category,
            description=description,
            status="REPORTED"
        )

        db.session.add(incident)
        db.session.commit()

        flash("Incident reported successfully.", "success")
        return redirect(url_for("incidents.incidents_page"))

    if current_user.role == "student":
        bookings = Booking.query.filter_by(
            user_id=current_user.id
        ).filter(
            Booking.status.in_(["CHECKED_IN", "RETURNED"])
        ).all()

        reports = Incident.query.filter_by(
            reported_by=current_user.id
        ).order_by(Incident.created_at.desc()).all()

    elif current_user.role == "owner":
        reports = Incident.query.join(
            Resource, Incident.resource_id == Resource.id
        ).filter(
            Resource.owner_id == current_user.id
        ).order_by(Incident.created_at.desc()).all()
        bookings = []

    else:
        reports = Incident.query.join(
            Resource, Incident.resource_id == Resource.id
        ).filter(
            Resource.institution_id == current_user.institution_id
        ).order_by(Incident.created_at.desc()).all()
        bookings = []

    return render_template(
        "incidents.html",
        bookings=bookings,
        reports=reports
    )


@bp.route("/incidents/<int:incident_id>/resolve", methods=["POST"])
@login_required
def resolve_incident(incident_id):

    if current_user.role not in ["owner", "manager", "admin"]:
        flash("You are not authorized to resolve incidents.", "danger")
        return redirect(url_for("incidents.incidents_page"))

    incident = db.session.get(Incident, incident_id)

    if not incident:
        flash("Incident not found.", "danger")
        return redirect(url_for("incidents.incidents_page"))

    resource = db.session.get(Resource, incident.resource_id)

    if current_user.role == "owner" and resource.owner_id != current_user.id:
        flash("You cannot resolve this incident.", "danger")
        return redirect(url_for("incidents.incidents_page"))

    if resource.institution_id != current_user.institution_id:
        flash("You cannot access this incident.", "danger")
        return redirect(url_for("incidents.incidents_page"))

    incident.status = "RESOLVED"
    incident.reviewed_by = current_user.id

    from datetime import datetime
    incident.resolved_at = datetime.utcnow()

    db.session.commit()

    flash("Incident marked as resolved.", "success")
    return redirect(url_for("incidents.incidents_page"))