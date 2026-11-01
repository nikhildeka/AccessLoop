from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models import Resource, Booking, AuditLog, Notification

bp = Blueprint("bookings", __name__)


@bp.route("/resources/<int:resource_id>/request", methods=["GET", "POST"])
@login_required
def request_booking(resource_id):

    resource = Resource.query.filter_by(
        id=resource_id,
        institution_id=current_user.institution_id,
        is_active=True
    ).first_or_404()

    if request.method == "POST":

        try:
            start_time = datetime.fromisoformat(
                request.form.get("start_time", "")
            )
            end_time = datetime.fromisoformat(
                request.form.get("end_time", "")
            )
        except ValueError:
            flash("Please enter valid dates and times.", "danger")
            return redirect(url_for(
                "bookings.request_booking", resource_id=resource.id
            ))

        purpose = request.form.get("purpose", "").strip()

        if not purpose or len(purpose) > 500:
            flash("Please provide a valid purpose (maximum 500 characters).")
            return redirect(url_for(
                "bookings.request_booking", resource_id=resource.id
            ))

        now = datetime.now()

        print("DEBUG - Server time:", now)
        print("DEBUG - Selected start:", start_time)
        print("DEBUG - Selected end:", end_time)

        if start_time <= now or end_time <= start_time:
            flash(
                f"Invalid period. Server time: {now}. "
                f"Selected start: {start_time}. "
                f"Selected end: {end_time}."
            )
            return redirect(url_for(
                "bookings.request_booking", resource_id=resource.id
            ))
                  
        duration = (end_time - start_time).total_seconds() / 3600

        if duration > resource.max_booking_hours:
            flash(
                f"Maximum booking duration is "
                f"{resource.max_booking_hours} hours."
            )
            return redirect(url_for(
                "bookings.request_booking", resource_id=resource.id
            ))

        if resource.maintenance_status != "OK":
            flash("This resource is currently unavailable.")
            return redirect(url_for("resources.resource_list"))

        if not current_user.is_verified:
            flash("Your institutional account must be verified.")
            return redirect(url_for("resources.resource_list"))

        if resource.required_qualification_id:
            from models import UserQualification

            qualified = UserQualification.query.filter_by(
                user_id=current_user.id,
                qualification_id=resource.required_qualification_id
            ).first()

            if not qualified:
                flash("You do not have the required verified qualification.")
                return redirect(url_for("resources.resource_list"))

        conflict = Booking.query.filter(
            Booking.resource_id == resource.id,
            Booking.status.in_(["APPROVED", "CHECKED_IN"]),
            Booking.start_time < end_time,
            Booking.end_time > start_time
        ).first()

        if conflict:
            flash("This resource is already booked during that period.")
            return redirect(url_for("resources.resource_list"))

        booking = Booking(
            resource_id=resource.id,
            user_id=current_user.id,
            start_time=start_time,
            end_time=end_time,
            purpose=purpose,
            status="PENDING"
        )

        db.session.add(booking)
        db.session.flush()

        db.session.add(AuditLog(
            actor_id=current_user.id,
            action="BOOKING_REQUESTED",
            entity_type="Booking",
            entity_id=booking.id,
            new_state="PENDING",
            reason=purpose
        ))

        db.session.add(Notification(
            user_id=resource.owner_id,
            message=f"New booking request for {resource.name}."
        ))

        db.session.commit()

        flash("Booking request submitted successfully!", "success")

        return redirect(url_for("bookings.my_bookings"))

    return render_template(
        "booking_request.html",
        resource=resource
    )


@bp.route("/my-bookings")
@login_required
def my_bookings():

    bookings = Booking.query.filter_by(
        user_id=current_user.id
    ).order_by(Booking.created_at.desc()).all()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )