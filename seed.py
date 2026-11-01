import secrets
from pathlib import Path
from flask import current_app
from extensions import db
from models import (Institution, User, Qualification, UserQualification, Resource)


def seed_demo():
    inst = Institution(name="Demo Institute of Technology (fictional)")
    q_laser = Qualification(name="Equipment Safety Training")
    db.session.add_all([inst, q_laser])
    db.session.flush()

    accounts = [("student", "Sam Student"), ("owner", "Olive Owner"),
                ("manager", "Max Manager"), ("admin", "Ada Admin")]
    creds, users = [], {}
    for role, name in accounts:
        pw = secrets.token_urlsafe(9)
        u = User(email=f"{role}@accessloop.demo", full_name=name, role=role,
                 institution_id=inst.id, is_verified=True)
        u.set_password(pw)
        db.session.add(u)
        users[role] = u
        creds.append(f"{u.email}  |  {pw}")
    db.session.flush()

    owner = users["owner"]
    items = [
        ("DSLR Camera", "Photography", "Media Lab", False, None),
        ("Arduino Development Kit", "Electronics", "Electronics Lab", False, None),
        ("Laptop", "Computing", "IT Store", False, None),
        ("Projector", "AV Equipment", "Room 101", False, None),
        ("Seminar Room", "Room", "Block B", True, q_laser.id),
    ]
    for n, cat, loc, approval, qual in items:
        db.session.add(Resource(
            owner_id=owner.id, institution_id=inst.id, name=n, category=cat,
            location=loc, description=f"Fictional demo {n.lower()}.",
            requires_manager_approval=approval, required_qualification_id=qual,
            max_booking_hours=48))
    db.session.commit()

    out = Path(current_app.instance_path) / "demo_credentials.txt"
    out.write_text("email  |  password\n" + "\n".join(creds) + "\n")
    print(f"Demo credentials written to {out}")
