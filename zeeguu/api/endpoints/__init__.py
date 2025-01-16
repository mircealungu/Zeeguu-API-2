import flask
import zeeguu.core

api = flask.Blueprint("endpoints", __name__)
db_session = zeeguu.core.model.db.session

print("loading endpoints...")

# These files have to be imported after this line;
# They enrich the endpoints object
from . import feature_toggles
from . import exercises
from . import exercise_sessions
from . import sessions
from . import system_languages
from . import translation
from . import activity_tracking
from . import bookmarks_and_words
from . import user
from . import user_statistics
from . import user_preferences
from . import user_article
from . import user_articles
from . import user_languages
from .teacher_dashboard import *
from . import topics
from . import search
from . import article
from . import accounts
from . import speech
from . import own_texts
from . import user_notifications
from .student import *
from .nlp import *
from .reading_sessions import *
from .user_activity_and_commitment import *

