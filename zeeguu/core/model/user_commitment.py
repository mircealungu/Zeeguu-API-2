from zeeguu.core.model import db, User
from sqlalchemy import Column, Integer, DateTime


class UserCommitment(db.Model):
    """
    This class keeps track of the user's commitment.
    It shows how much time users choose to commit to on a weekly basis, 
    how many consecutive weeks they have sticked to their commitment, 
    and the last date the number of consecutive weeks was udated.
    """
    __table_args__ = dict(mysql_collate="utf8_bin")
    __tablename__ = "user_commitment"
    user_id = Column(Integer, db.ForeignKey(User.id), primary_key=True)
    user_minutes = Column(Integer)
    user_days = Column(Integer)
    consecutive_weeks = Column(Integer)
    commitment_last_updated = Column(DateTime)