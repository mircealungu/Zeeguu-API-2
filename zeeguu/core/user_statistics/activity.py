import json

from sqlalchemy import text

import zeeguu.core
from zeeguu.core.constants import SIMPLE_DATE_FORMAT

#leading to another function 
def reading_duration_by_day(user):
    return _time_by_day(user, "user_reading_session", "start_time", "duration")


def exercises_duration_by_day(user):
    return _time_by_day(user, "user_exercise_session", "start_time", "duration")
#user_exercise_session = table 
#start_time = field in table
#duration = field in table

#further calls other helper functions
def activity_duration_by_day(user):
    return {
        "reading": convert_to_date_seconds(reading_duration_by_day(user)), #probably another function
        "exercises": convert_to_date_seconds(exercises_duration_by_day(user)),
    }


def convert_to_date_seconds(result_raw):
    result_array = [
        {
            "date": (each._mapping["date"]).strftime(SIMPLE_DATE_FORMAT),
            "seconds": (int(each._mapping["duration"])),
        }
        for each in result_raw
    ]

    return result_array

#performs a database query
def _time_by_day(user, table_name, date_field, duration_field):
    query = (
            f" SELECT date({date_field}) as date, "
            + f" SUM({duration_field}) / 1000 as duration "
            + f" FROM {table_name}"
            + " WHERE user_id = :uid GROUP BY date;"
    )
    result_raw = zeeguu.core.model.db.session.execute(
        text(query),
        {"uid": user.id, "table_name": table_name},
    )

    return result_raw
#if the query results in several rows from the table the output would be several entries.
#text function is a SQLAlchemy function that makes it possible to work with raw data.
