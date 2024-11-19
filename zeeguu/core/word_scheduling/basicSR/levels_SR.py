from .basicSR import ONE_DAY, BasicSRSchedule
from zeeguu.core.model import db, ExerciseOutcome
from datetime import datetime, timedelta

MAX_LEVEL = 4

# We are mapping cooling intervals to levels for users that migrate to LevelsSR, so their progress won't get lost.
COOLING_INTERVAL_TO_LEVEL_MAPPING = {
    0: 1,
    ONE_DAY: 1,
    2 * ONE_DAY: 2,
    4 * ONE_DAY: 3,
    8 * ONE_DAY: 4,
}

class LevelsSR(BasicSRSchedule):

    MAX_INTERVAL = 2 * ONE_DAY

    NEXT_COOLING_INTERVAL_ON_SUCCESS = {
        0: ONE_DAY,
        ONE_DAY: 2 * ONE_DAY,
    }

    # Reverse the process
    DECREASE_COOLING_INTERVAL_ON_FAIL = {
        v: k for k, v in NEXT_COOLING_INTERVAL_ON_SUCCESS.items()
    }
    # If at 0, we don't decrease it further.
    DECREASE_COOLING_INTERVAL_ON_FAIL[0] = 0

    def __init__(self, bookmark=None, bookmark_id=None):
        super(LevelsSR, self).__init__(bookmark, bookmark_id)

    def update_schedule(self, db_session, correctness):
        level = self.bookmark.level
        is_migrated = False
        if level == 0:
            level = COOLING_INTERVAL_TO_LEVEL_MAPPING.get(
                self.cooling_interval, 1
            )
            is_migrated = True

        if correctness:
            if self.cooling_interval >= self.MAX_INTERVAL:
                if (level < MAX_LEVEL or (level == MAX_LEVEL and is_migrated)):
                    # Bookmark will move to the next level
                    self.bookmark.level = level + 1 if not is_migrated else level 
                    self.cooling_interval = 0
                    db_session.add(self.bookmark)
                    return
                else:
                    self.set_bookmark_as_learned(db_session)
                    return

            # Use the same logic as when selecting bookmarks
            # Avoid case where if schedule at 01-01-2024 11:00 and user does it at
            # 01-01-2024 10:00 the status is not updated.
            if self.get_end_of_today() < self.next_practice_time:
                # a user might have arrived here by doing the
                # bookmarks in a text for a second time...
                # in general, as long as they didn't wait for the
                # cooldown period, they might have arrived to do
                # the exercise again; but it should not count
                return
            new_cooling_interval = self.NEXT_COOLING_INTERVAL_ON_SUCCESS.get(
                self.cooling_interval, self.MAX_INTERVAL
            )
            self.consecutive_correct_answers += 1
        else:
            # Decrease the cooling interval to the previous bucket
            new_cooling_interval = self.DECREASE_COOLING_INTERVAL_ON_FAIL[
                self.cooling_interval
            ]
            # Should we allow the user to "recover" their schedule
            # in the same day?
            # next_practice_date = datetime.now()
            self.consecutive_correct_answers = 0
        self.bookmark.level = level
        db_session.add(self.bookmark)
        self.cooling_interval = new_cooling_interval
        next_practice_date = datetime.now() + timedelta(minutes=new_cooling_interval)
        self.next_practice_time = next_practice_date

    @classmethod
    def get_max_interval(cls, in_days: bool = False):
        """
        in_days:bool False, use true if you want the interval in days, rather than
        minutes.
        :returns:int, total number of minutes the schedule can have as a maximum.
        """
        return cls.MAX_INTERVAL if not in_days else cls.MAX_INTERVAL // ONE_DAY

    @classmethod
    def get_next_cooling_interval(cls):
        return cls.NEXT_COOLING_INTERVAL_ON_SUCCESS

    @classmethod
    def get_learning_cycle_length(cls):
        return len(cls.NEXT_COOLING_INTERVAL_ON_SUCCESS)

    @classmethod
    def update(cls, db_session, bookmark, outcome):

        if outcome == ExerciseOutcome.OTHER_FEEDBACK:
            from zeeguu.core.model.bookmark_user_preference import UserWordExPreference

            schedule = cls.find_or_create(db_session, bookmark)
            bookmark.fit_for_study = 0
            ## Since the user has explicitly given feedback, this should
            # be recorded as a user preference.
            bookmark.user_preference = UserWordExPreference.DONT_USE_IN_EXERCISES
            db_session.add(bookmark)
            db_session.delete(schedule)
            return

        correctness = ExerciseOutcome.is_correct(outcome)
        schedule = cls.find_or_create(db_session, bookmark)
        if schedule.next_practice_time > cls.get_end_of_today():
            # The user is doing the word before it was scheduled.
            # We do not update the schedule if that's the case.
            # This can happen when they practice words from the
            # Article.
            return
        schedule.update_schedule(db_session, correctness)

    @classmethod
    def find_or_create(cls, db_session, bookmark):

        results = cls.query.filter_by(bookmark=bookmark).all()
        print(results)
        if len(results) == 1:
            print(len(results))
            print("getting the first element in results")
            return results[0]

        if len(results) > 1:
            raise Exception(
                f"More than one Bookmark schedule entry found for {bookmark.id}"
            )

        # create a new one
        schedule = cls(bookmark)
        bookmark.level = 1
        db_session.add_all([schedule, bookmark])
        db_session.commit()
        return schedule
