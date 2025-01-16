import flask_sqlalchemy

db = flask_sqlalchemy.SQLAlchemy()

import zeeguu

# If zeeguu.core.app is already defined we use that object
# as the app for the db_init that we do later. If not,
# we create the app here and load the corresponding configuration
# if not hasattr(zeeguu.core, "app"):
#     zeeguu.core.app = Flask("Zeeguu-Core")
#     load_configuration_or_abort(
#         zeeguu.core.app,
#         "ZEEGUU_CONFIG",
#         ["MAX_SESSION", "SQLALCHEMY_DATABASE_URI", "SQLALCHEMY_TRACK_MODIFICATIONS"],
#     )


# Create the zeeguu.core.db object, which will be the superclass
# of all the model classes
# zeeguu.core.db = flask_sqlalchemy.SQLAlchemy(zeeguu.core.app)
# Note, that if we pass the app here, then we don't need later
# to push the app context


# the core model
from .article_url_keyword_map import ArticleUrlKeywordMap
from .article_topic_map import ArticleTopicMap
from .user_cohort_map import UserCohortMap
from .language import Language
from .url import Url
from .domain_name import DomainName
from .article import Article
from .bookmark import Bookmark
from .text import Text
from .user_word import UserWord
from .user_preference import UserPreference
from .session import Session
from .unique_code import UniqueCode
from .article_broken_code_map import ArticleBrokenMap, LowQualityTypes

from .user import User
from .cohort import Cohort

from .user_language import UserLanguage

from .user_article import UserArticle
from .article_difficulty_feedback import ArticleDifficultyFeedback

from .feed import Feed
from .url_keyword import UrlKeyword

from .search import Search
from .search_filter import SearchFilter
from .search_subscription import SearchSubscription

# exercises
from .exercise import Exercise
from .exercise_outcome import ExerciseOutcome
from .exercise_source import ExerciseSource

# user logging
from .user_activitiy_data import UserActivityData
from .user_commitment import UserCommitment

# teachers and cohorts


from .teacher_cohort_map import TeacherCohortMap
from .teacher import Teacher
from .cohort_article_map import CohortArticleMap

# New topic features
from .topic import Topic
from .topic_subscription import TopicSubscription
from .topic_filter import TopicFilter

from .user_reading_session import UserReadingSession
from .user_exercise_session import UserExerciseSession


# bookmark scheduling
from .word_to_study import WordToStudy
from ..word_scheduling.basicSR.basicSR import BasicSRSchedule

from .personal_copy import PersonalCopy

from .difficulty_lingo_rank import DifficultyLingoRank
