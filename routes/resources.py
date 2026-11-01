from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import or_

from models import Resource

bp = Blueprint("resources", __name__)


@bp.route("/resources")
@login_required
def resource_list():

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    query = Resource.query.filter_by(
        institution_id=current_user.institution_id,
        is_active=True
    )

    if search:
        query = query.filter(
            or_(
                Resource.name.ilike(f"%{search}%"),
                Resource.description.ilike(f"%{search}%"),
                Resource.location.ilike(f"%{search}%")
            )
        )

    if category:
        query = query.filter_by(category=category)

    resources = query.order_by(Resource.name).all()

    categories = [
        row[0] for row in
        Resource.query.with_entities(Resource.category)
        .filter_by(
            institution_id=current_user.institution_id,
            is_active=True
        )
        .distinct()
        .order_by(Resource.category)
        .all()
    ]

    return render_template(
        "resources.html",
        resources=resources,
        categories=categories,
        search=search,
        selected_category=category
    )