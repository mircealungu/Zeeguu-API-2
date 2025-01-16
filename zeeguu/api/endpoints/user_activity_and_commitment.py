import flask
from flask import request

from zeeguu.api.utils import json_result
from . import api, db_session
from zeeguu.api.utils.route_wrappers import cross_domain, requires_session
from datetime import datetime, timedelta

from zeeguu.core.model import User
from zeeguu.core.model import UserCommitment
import zeeguu.core.model

from zeeguu.core.user_statistics.activity import activity_duration_by_day

@api.route("/user_activity_and_commitment", methods=("GET",))
@cross_domain
@requires_session
def user_activity_and_commitment():
    """
    Returns all the user activity and commitment data 
    """
    user = User.find_by_id(flask.g.user_id)
    user_commitment = UserCommitment.query.filter_by(user_id=user.id).first()
    user_activities = activity_duration_by_day(user)
    return json_result({
        "user_minutes": user_commitment.user_minutes,
        "user_days": user_commitment.user_days,
        "consecutive_weeks": user_commitment.consecutive_weeks,
        "commitment_last_updated": user_commitment.commitment_last_updated,
        "user_activities": user_activities,
    })


@api.route("/user_commitment", methods=("GET",))
@cross_domain
@requires_session
def user_commitment():
    """
    Returns all user commitment data
    """
    user = User.find_by_id(flask.g.user_id)
    user_commitment = UserCommitment.query.filter_by(user_id=user.id).first()
    print(user_commitment.user_minutes)
    return json_result({
        "user_minutes": user_commitment.user_minutes,
        "user_days": user_commitment.user_days,
    })
    
 
#Sends the minutes and days that the user chooses to the database 
@api.route("/user_commitment_create", methods=["POST"])
@cross_domain
@requires_session
def user_commitment_create():
    """
    Creates new user commitment record
    during registration
    """
    user = User.find_by_id(flask.g.user_id)
    data = flask.request.form
    submitted_minutes = data.get("user_minutes")
    submitted_days = data.get("user_days")
    default_commitment_date = (datetime.now() - timedelta(days=14))

    user_commitment = UserCommitment(
        user_id=user.id,
        user_minutes = int(submitted_minutes),
        user_days = int(submitted_days),
        consecutive_weeks = 0, 
        commitment_last_updated = default_commitment_date,
    ) 
  
    zeeguu.core.model.db.session.add(user_commitment)
    zeeguu.core.model.db.session.commit()
    return "OK"


# When the user meets their weekly goal, this method updates the consecutive weeks count in database
@api.route("/user_commitment_update", methods=["POST"])
@cross_domain
@requires_session
def user_commitment_update():
    user = User.find_by_id(flask.g.user_id)
    data = flask.request.form
    consecutives_weeks = data.get("commitment_and_activity_data")
    commitment_last_update = data.get("last_commitment_update")
    user_commitment = UserCommitment.query.filter_by(user_id=user.id).first()
    user_commitment.consecutive_weeks = int(consecutives_weeks)
    user_commitment.commitment_last_updated = datetime.fromisoformat(commitment_last_update)
    zeeguu.core.model.db.session.commit()
    return "OK"

@api.route("/user_commitment_info", methods=["POST"])
@cross_domain
@requires_session
def user_commitment_info():
    """
    Updates the number of days and minutes the user wants to practice
    under settings
    """
    user = User.find_by_id(flask.g.user_id)
    data = flask.request.form
    user_minutes = data.get("user_minutes")
    user_days = data.get("user_days")
    commitment = UserCommitment.query.filter_by(user_id=user.id).first()
    commitment.user_minutes = int(user_minutes)
    commitment.user_days = int(user_days)
    zeeguu.core.model.db.session.commit()
    return "OK"