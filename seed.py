from backend.app.database.connection import SessionLocal
from backend.app.database.models import User, Profile

def seed_database():
    """
    Creates the test user and profile if they do not already exist.
    """
    db = SessionLocal()
    try:
        test_user = db.query(User).filter(User.username == "testuser").first()
        if test_user is None:
            test_user = User(
                username="testuser",
                email="test@example.com",
                password_hash="pass123",
            )
            db.add(test_user)
            db.flush()

        test_profile = db.query(Profile).filter(Profile.user_id == test_user.user_id).first()
        if test_profile is None:
            test_profile = Profile(
                user_id=test_user.user_id,
                age=25,
                gender="male",
                goal="muscle_gain",
                experience="intermediate",
                training_days=4,
                equipment=["dumbbells", "bench"],
                diet_preference="omnivore",
                allergies=[],
                restrictions=[],
                injuries=["shoulder"],
            )
            db.add(test_profile)
        else:
            if test_profile.training_days is None:
                test_profile.training_days = 4
            if test_profile.allergies is None:
                test_profile.allergies = []
            if test_profile.restrictions is None:
                test_profile.restrictions = []

        db.commit()
        print(f"Success: Test user is ready with ID {test_user.user_id}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()