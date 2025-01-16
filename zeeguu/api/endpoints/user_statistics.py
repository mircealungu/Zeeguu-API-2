import flask

from zeeguu.api.utils import json_result
from zeeguu.core.user_statistics.activity import activity_duration_by_day
from . import api
from zeeguu.api.utils.route_wrappers import cross_domain, requires_session
from zeeguu.core.model import User


@api.route("/bookmark_counts_by_date", methods=("GET",))
@cross_domain
@requires_session
def bookmark_counts_by_date():
    """
    Words that have been translated in texts
    """
    user = User.find_by_id(flask.g.user_id)
    return user.bookmark_counts_by_date()

#routing. any HTTP GET to /acticity_by_day trigger the function below
#
@api.route("/activity_by_day", methods=("GET",))
@cross_domain
@requires_session #user needs to be logged for this endpoint to trigger the function
def activity_by_day():
    """
    User sessions by day
    """
    user = User.find_by_id(flask.g.user_id) #Probably finds the user with the mathing id
    return json_result(activity_duration_by_day(user)) #another function
