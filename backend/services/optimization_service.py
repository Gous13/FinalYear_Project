"""
Optimization Service using Google OR-Tools for team formation
"""

from ortools.sat.python import cp_model
import json
import numpy as np

class OptimizationService:
    """Service for constraint-based team formation optimization"""
    
    def __init__(self):
        """Initialize optimization service"""
        pass
    
    def form_teams(self, profiles, project, similarity_scores, constraints=None):
        """
        Form optimal teams using constraint programming
        
        Args:
            profiles: List of student profiles
            project: Project or Hackathon object
            similarity_scores: Dict mapping profile_id -> similarity_score
            constraints: Optional dict with custom constraints
            
        Returns:
            List of team assignments (list of profile IDs per team)
        """
        if constraints is None:
            constraints = {}
        
        num_students = len(profiles)
        if num_students == 0:
            return []
        
        # Get team size constraints
        min_size = constraints.get('min_team_size', project.min_team_size if hasattr(project, 'min_team_size') else 3)
        max_size = constraints.get('max_team_size', project.max_team_size if hasattr(project, 'max_team_size') else 5)
        preferred_size = constraints.get('preferred_team_size', project.preferred_team_size if hasattr(project, 'preferred_team_size') else 4)
        
        # Calculate number of teams needed
        num_teams = (num_students + preferred_size - 1) // preferred_size  # Ceiling division
        
        # Create model
        model = cp_model.CpModel()
        
        # Decision variables: x[i][t] = 1 if student i is assigned to team t
        x = {}
        for i in range(num_students):
            for t in range(num_teams):
                x[i, t] = model.NewBoolVar(f'student_{i}_team_{t}')
        
        # Constraints
        
        # 1. Each student assigned to exactly one team
        for i in range(num_students):
            model.Add(sum(x[i, t] for t in range(num_teams)) == 1)
        
        # 2. Team size constraints
        for t in range(num_teams):
            team_size = sum(x[i, t] for i in range(num_students))
            model.Add(team_size >= min_size)
            model.Add(team_size <= max_size)
        
        # 3. Objective: Maximize total similarity score AND skill diversity
        # Also minimize team size variance for balance
        objective_terms = []
        
        # Extract skills for diversity calculation
        from services.nlp_service import get_nlp_service
        nlp = get_nlp_service()
        profile_skills_dict = {}
        for i, profile in enumerate(profiles):
            profile_skills_dict[i] = set(nlp.extract_keywords(profile.skills_description or '', top_n=10))
        
        # Maximize similarity
        for i in range(num_students):
            profile_id = profiles[i].id
            similarity = similarity_scores.get(profile_id, 0.5)
            for t in range(num_teams):
                objective_terms.append(similarity * 100 * x[i, t])  # Weight similarity heavily
        
        # Maximize skill diversity within teams
        # Penalize teams where students have very similar skills (>80% overlap)
        for t in range(num_teams):
            for i in range(num_students):
                for j in range(i + 1, num_students):
                    # Check if these two students have very similar skills
                    skills_i = profile_skills_dict[i]
                    skills_j = profile_skills_dict[j]
                    if len(skills_i) > 0 and len(skills_j) > 0:
                        overlap_ratio = len(skills_i & skills_j) / max(len(skills_i | skills_j), 1)
                        
                        # If overlap is very high (>80%), add penalty if both in same team
                        if overlap_ratio > 0.8:
                            # Create indicator: both_in_team = x[i,t] AND x[j,t]
                            both_in_team = model.NewBoolVar(f'both_{i}_{j}_team_{t}')
                            # both_in_team == 1 if and only if both x[i,t] == 1 and x[j,t] == 1
                            model.Add(both_in_team <= x[i, t])
                            model.Add(both_in_team <= x[j, t])
                            model.Add(both_in_team >= x[i, t] + x[j, t] - 1)
                            # Penalty for low diversity
                            objective_terms.append(-30 * both_in_team)
        
        # Minimize variance in team sizes (encourage balanced teams)
        team_sizes = [sum(x[i, t] for i in range(num_students)) for t in range(num_teams)]
        # Use sum of squared differences from preferred size
        for t in range(num_teams):
            diff = model.NewIntVar(0, max_size, f'diff_team_{t}')
            model.Add(diff == abs(team_sizes[t] - preferred_size))
            objective_terms.append(-diff * 10)  # Penalty for deviation (negative because we maximize)
        
        # Maximize objective
        model.Maximize(sum(objective_terms))
        
        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0  # Time limit for academic use
        status = solver.Solve(model)
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Extract team assignments
            teams = [[] for _ in range(num_teams)]
            for i in range(num_students):
                for t in range(num_teams):
                    if solver.Value(x[i, t]) == 1:
                        teams[t].append(profiles[i].id)
                        break
            
            # Filter out empty teams
            teams = [team for team in teams if len(team) > 0]
            return teams
        else:
            # Fallback: Simple greedy assignment
            return self._greedy_team_formation(profiles, project, similarity_scores, constraints)
    
    def _greedy_team_formation(self, profiles, project, similarity_scores, constraints):
        """
        Fallback greedy team formation algorithm
        """
        min_size = constraints.get('min_team_size', project.min_team_size if hasattr(project, 'min_team_size') else 3)
        max_size = constraints.get('max_team_size', project.max_team_size if hasattr(project, 'max_team_size') else 5)
        preferred_size = constraints.get('preferred_team_size', project.preferred_team_size if hasattr(project, 'preferred_team_size') else 4)
        
        # Sort profiles by similarity (descending)
        sorted_profiles = sorted(
            profiles,
            key=lambda p: similarity_scores.get(p.id, 0.5),
            reverse=True
        )
        
        # Extract skills for diversity checking
        from services.nlp_service import get_nlp_service
        nlp = get_nlp_service()
        profile_skills = {}
        for profile in sorted_profiles:
            profile_skills[profile.id] = set(nlp.extract_keywords(profile.skills_description or '', top_n=10))
        
        teams = []
        current_team = []
        current_team_skills = set()
        
        for profile in sorted_profiles:
            profile_id = profile.id
            skills = profile_skills[profile_id]
            
            # Check skill diversity: avoid putting students with >80% skill overlap together
            if current_team and len(current_team) >= min_size:
                # Check overlap with existing team members
                max_overlap = 0
                for member_id in current_team:
                    member_skills = profile_skills.get(member_id, set())
                    if len(member_skills) > 0 and len(skills) > 0:
                        overlap = len(member_skills & skills) / len(member_skills | skills)
                        max_overlap = max(max_overlap, overlap)
                
                # If overlap is too high (>80%), start new team for diversity
                if max_overlap > 0.8:
                    teams.append(current_team)
                    current_team = [profile_id]
                    current_team_skills = skills
                    continue
            
            if len(current_team) < preferred_size:
                current_team.append(profile_id)
                current_team_skills.update(skills)
            else:
                teams.append(current_team)
                current_team = [profile_id]
                current_team_skills = skills
        
        if current_team:
            # Merge small teams or add to existing
            if len(teams) > 0 and len(current_team) < min_size:
                # Try to merge with last team if possible
                if len(teams[-1]) + len(current_team) <= max_size:
                    teams[-1].extend(current_team)
                else:
                    teams.append(current_team)
            else:
                teams.append(current_team)
        
        return teams
    
    def compute_team_diversity_score(self, team_profile_ids, profiles_dict):
        """
        Compute diversity score for a team based on skills/background
        
        Args:
            team_profile_ids: List of profile IDs in team
            profiles_dict: Dict mapping profile_id -> profile object
            
        Returns:
            float: Diversity score (0-1)
        """
        if len(team_profile_ids) < 2:
            return 0.0
        
        # Extract skills from each profile
        all_skills = []
        for profile_id in team_profile_ids:
            profile = profiles_dict.get(profile_id)
            if profile and profile.skills_description:
                # Simple keyword extraction
                skills = [s.strip() for s in profile.skills_description.lower().split(',')]
                all_skills.append(set(skills))
        
        # Compute Jaccard similarity between all pairs
        similarities = []
        for i in range(len(all_skills)):
            for j in range(i + 1, len(all_skills)):
                intersection = len(all_skills[i] & all_skills[j])
                union = len(all_skills[i] | all_skills[j])
                if union > 0:
                    jaccard = intersection / union
                    similarities.append(jaccard)
        
        if not similarities:
            return 1.0  # Maximum diversity if no overlap
        
        # Diversity = 1 - average similarity
        avg_similarity = sum(similarities) / len(similarities)
        diversity = 1.0 - avg_similarity
        
        return diversity
