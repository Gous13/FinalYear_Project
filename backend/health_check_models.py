
from app import create_app
from extensions import db
from models.user import User
from models.assessment_models import SkillAssessment, AssessmentQuestion, AssessmentAttempt

app = create_app()
with app.app_context():
    models_to_test = [User, SkillAssessment, AssessmentQuestion, AssessmentAttempt]
    for model in models_to_test:
        try:
            count = model.query.count()
            print(f"✅ {model.__name__}: {count} records")
        except Exception as e:
            print(f"❌ {model.__name__} failed: {e}")

    # Test the specific query that failed for the user
    try:
        # Example user_id 5, skill 'HTML'
        res = SkillAssessment.query.filter_by(user_id=5, skill_name='HTML').first()
        print(f"✅ SkillAssessment specific query passed.")
    except Exception as e:
        print(f"❌ SkillAssessment specific query failed: {e}")
