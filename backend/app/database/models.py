from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import date, datetime, timezone
from backend.app.database.connection import Base

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False)
    workout_history = relationship("WorkoutHistory", back_populates="user")
    meal_history = relationship("MealHistory", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")
    progress = relationship("Progress", back_populates="user")

class Profile(Base):
    __tablename__ = "profiles"

    profile_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True)
    age = Column(Integer)
    gender = Column(String)
    height = Column(Float)
    weight = Column(Float)
    goal = Column(String)
    experience = Column(String)
    training_days = Column(Integer)
    equipment = Column(JSONB) # Maps to PostgreSQL JSONB
    diet_preference = Column(String)
    allergies = Column(JSONB)
    restrictions = Column(JSONB)
    injuries = Column(JSONB)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="profile")

class WorkoutHistory(Base):
    __tablename__ = "workout_history"

    history_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    template_id = Column(String)
    muscle_group = Column(String)
    workout_date = Column(Date, default=date.today)
    status = Column(String)
    difficulty_felt = Column(String)
    performance = Column(JSONB)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="workout_history")

class MealHistory(Base):
    __tablename__ = "meal_history"

    meal_log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    meal_id = Column(String)
    meal_type = Column(String)
    meal_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="meal_history")

class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    item_id = Column(String)
    item_type = Column(String)
    feedback_type = Column(String)
    comments = Column(Text)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="feedback")

class Progress(Base):
    __tablename__ = "progress"

    progress_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    metric_date = Column(Date, default=date.today)
    weight = Column(Float)
    metric_type = Column(String)
    notes = Column(Text)

    user = relationship("User", back_populates="progress")
