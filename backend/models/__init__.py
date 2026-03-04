"""
Database models for SynapseLink
"""

from .user import User, Role
from .profile import StudentProfile
from .project import Project, Hackathon
from .team import Team, TeamMember
from .matching import SimilarityScore, MatchExplanation
from .analytics import SystemLog
from .message import Message
from .group_chat import GroupChat, GroupChatMember, GroupMessage
from .group_chat_read_state import GroupChatReadState
# New assessment models will be added here
from .assessment_models import SkillAssessment, AssessmentQuestion, AssessmentAttempt
from .project_task import ProjectTask
from .team_file import TeamFile
from .invitation import Invitation

__all__ = [
    'User', 'Role',
    'StudentProfile',
    'Project', 'Hackathon',
    'Team', 'TeamMember',
    'SimilarityScore', 'MatchExplanation',
    'SystemLog',
    'Message',
    'GroupChat', 'GroupChatMember', 'GroupMessage',
    'GroupChatReadState',
    'SkillAssessment', 'AssessmentQuestion', 'AssessmentAttempt',
    'ProjectTask', 'TeamFile', 'Invitation'
]
