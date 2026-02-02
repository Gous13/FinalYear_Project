import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../services/api'
import Layout from '../components/Layout'
import SkillsInput from '../components/SkillsInput'
import toast from 'react-hot-toast'
import { 
  User, Plus, Search, Sparkles, Users, Briefcase, 
  TrendingUp, Info, CheckCircle, XCircle 
} from 'lucide-react'

const AVAILABILITY_OPTIONS = [
  { value: '', label: 'Select availability' },
  { value: '5-10 hours per week', label: '5-10 hours per week' },
  { value: '10-20 hours per week', label: '10-20 hours per week' },
  { value: '30-40 hours per week', label: '30-40 hours per week' },
  { value: '40-50 hours per week', label: '40-50 hours per week' },
  { value: '50-60 hours per week', label: '50-60 hours per week' },
  { value: '60-70 hours per week', label: '60-70 hours per week' },
  { value: '70-80 hours per week', label: '70-80 hours per week' },
  { value: '80-90 hours per week', label: '80-90 hours per week' },
  { value: '90-100 hours per week', label: '90-100 hours per week' }
]

const DEPARTMENT_OPTIONS = ['CSE', 'CAD', 'CSM', 'CIV', 'EEE', 'ECE', 'MEC']

const StudentDashboard = () => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [showProfileModal, setShowProfileModal] = useState(false)
  const [rejectedProjects, setRejectedProjects] = useState(() => {
    // Load rejected projects from localStorage
    const stored = localStorage.getItem('rejectedProjects')
    return stored ? JSON.parse(stored) : []
  })
  const [profileData, setProfileData] = useState({
    skills_description: '',
    interests_description: '',
    experience_description: '',
    availability_description: '',
    year_of_study: '',
    department: '',
    gpa: ''
  })

  // Fetch profile
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const res = await api.get('/profiles')
      return res.data.profile
    },
    retry: false
  })

  // Fetch recommendations
  const { data: recommendations, isLoading: recLoading } = useQuery({
    queryKey: ['recommendations'],
    queryFn: async () => {
      const res = await api.get('/matching/recommendations')
      return res.data.recommendations || []
    },
    enabled: !!profile
  })

  // Fetch teams
  const { data: teamsData } = useQuery({
    queryKey: ['teams'],
    queryFn: async () => {
      const res = await api.get('/teams')
      return res.data.teams || []
    }
  })

  // Create/Update profile mutation
  const profileMutation = useMutation({
    mutationFn: async (data) => {
      try {
        if (profile) {
          return await api.put('/profiles', data)
        } else {
          return await api.post('/profiles', data)
        }
      } catch (error) {
        console.error('Profile save error:', error)
        console.error('Error response:', error.response?.data)
        throw error
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['profile'])
      setShowProfileModal(false)
      toast.success('Profile saved successfully!')
    },
    onError: (error) => {
      const errorMessage = error.response?.data?.error || error.message || 'Failed to save profile'
      console.error('Profile mutation error:', errorMessage)
      toast.error(errorMessage)
    }
  })

  useEffect(() => {
    if (profile) {
      setProfileData({
        skills_description: profile.skills_description || '',
        interests_description: profile.interests_description || '',
        experience_description: profile.experience_description || '',
        availability_description: profile.availability_description || '',
        year_of_study: profile.year_of_study || '',
        department: profile.department || '',
        gpa: profile.gpa || ''
      })
    }
  }, [profile])

  const handleProfileSubmit = (e) => {
    e.preventDefault()
    if (!profileData.skills_description?.trim()) {
      toast.error('Please add at least one skill')
      return
    }
    profileMutation.mutate(profileData)
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Welcome back, {user?.first_name}!</h1>
              <p className="mt-2 text-gray-600">Manage your profile and discover team opportunities</p>
            </div>
            <button
              onClick={() => setShowProfileModal(true)}
              className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              <User className="w-5 h-5 mr-2" />
              {profile ? 'Edit Profile' : 'Create Profile'}
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-3 bg-primary-100 rounded-lg">
                <Users className="w-6 h-6 text-primary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">My Teams</p>
                <p className="text-2xl font-bold text-gray-900">{teamsData?.length || 0}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-3 bg-accent-100 rounded-lg">
                <Briefcase className="w-6 h-6 text-accent-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Recommendations</p>
                <p className="text-2xl font-bold text-gray-900">{recommendations?.length || 0}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-3 bg-purple-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Profile Status</p>
                <p className="text-2xl font-bold text-gray-900">
                  {profile?.is_complete ? 'Complete' : 'Incomplete'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Profile Modal */}
        {showProfileModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b">
                <h2 className="text-2xl font-bold text-gray-900">Create/Edit Profile</h2>
                <p className="text-sm text-gray-600 mt-1">Fill in your details to get better matches</p>
              </div>
              <form onSubmit={handleProfileSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Skills *
                  </label>
                  <SkillsInput
                    value={profileData.skills_description}
                    onChange={(val) => setProfileData({...profileData, skills_description: val})}
                    placeholder="Type to search (e.g., sql, react, python)..."
                  />
                  <p className="text-xs text-gray-500 mt-1">Type a skill to see related suggestions from all domains</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Interests
                  </label>
                  <textarea
                    value={profileData.interests_description}
                    onChange={(e) => setProfileData({...profileData, interests_description: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    rows="2"
                    placeholder="e.g., AI, Web Development, Data Science"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Experience
                  </label>
                  <textarea
                    value={profileData.experience_description}
                    onChange={(e) => setProfileData({...profileData, experience_description: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    rows="2"
                    placeholder="e.g., 2 years of web development, 1 hackathon win"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Availability
                  </label>
                  <select
                    value={profileData.availability_description}
                    onChange={(e) => setProfileData({...profileData, availability_description: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  >
                    {(() => {
                      const hasCustom = profileData.availability_description && !AVAILABILITY_OPTIONS.find(o => o.value === profileData.availability_description)
                      return (
                        <>
                          {AVAILABILITY_OPTIONS.map((opt) => (
                            <option key={opt.value || 'empty'} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                          {hasCustom && (
                            <option value={profileData.availability_description}>
                              Current: {profileData.availability_description}
                            </option>
                          )}
                        </>
                      )
                    })()}
                  </select>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                    <input
                      type="number"
                      min="1"
                      max="4"
                      value={profileData.year_of_study}
                      onChange={(e) => setProfileData({...profileData, year_of_study: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                    <select
                      value={profileData.department}
                      onChange={(e) => setProfileData({...profileData, department: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">Select department</option>
                      {DEPARTMENT_OPTIONS.map((dept) => (
                        <option key={dept} value={dept}>{dept}</option>
                      ))}
                      {profileData.department && !DEPARTMENT_OPTIONS.includes(profileData.department) && (
                        <option value={profileData.department}>{profileData.department}</option>
                      )}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">GPA</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="10"
                      value={profileData.gpa}
                      onChange={(e) => setProfileData({...profileData, gpa: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowProfileModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={profileMutation.isLoading}
                    className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
                  >
                    {profileMutation.isLoading ? 'Saving...' : 'Save Profile'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Recommendations */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 flex items-center">
              <Sparkles className="w-5 h-5 mr-2 text-primary-600" />
              AI Recommendations
            </h2>
          </div>
          {recLoading ? (
            <div className="text-center py-8">Loading recommendations...</div>
          ) : recommendations?.length > 0 ? (
            <div className="space-y-4">
              {recommendations
                .filter(rec => !rejectedProjects.includes(rec.project.id))
                .slice(0, 5)
                .map((rec) => (
                  <ProjectCard 
                    key={rec.project.id} 
                    recommendation={rec}
                    onReject={(projectId) => {
                      setRejectedProjects(prev => {
                        const updated = [...prev, projectId]
                        localStorage.setItem('rejectedProjects', JSON.stringify(updated))
                        return updated
                      })
                    }}
                  />
                ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No recommendations available. Complete your profile to get matches!
            </div>
          )}
        </div>

        {/* My Teams */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2 text-primary-600" />
            My Teams
          </h2>
          {teamsData?.length > 0 ? (
            <div className="space-y-4">
              {teamsData.map((team) => (
                <TeamCard key={team.id} team={team} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              You're not part of any teams yet. Check recommendations above!
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}

const ProjectCard = ({ recommendation, onReject }) => {
  const { project, similarity, similarity_id } = recommendation
  const [showExplanation, setShowExplanation] = useState(false)
  const [explanation, setExplanation] = useState(null)
  const [isJoining, setIsJoining] = useState(false)
  const queryClient = useQueryClient()

  const fetchExplanation = async () => {
    try {
      let res
      if (similarity_id) {
        res = await api.get(`/matching/explanation/${similarity_id}`)
        setExplanation(res.data.explanation)
      } else {
        // If no similarity_id, use project-based explanation
        res = await api.get(`/matching/explanation/project/${project.id}`)
        setExplanation(res.data.explanation)
      }
      setShowExplanation(true)
    } catch (error) {
      toast.error('Failed to load explanation')
    }
  }

  const handleJoin = async () => {
    setIsJoining(true)
    try {
      // First compute similarities if not done
      if (!similarity_id) {
        await api.post(`/matching/compute-similarities/${project.id}`)
      }
      
      // Create or join a team for this project
      const res = await api.post('/teams', {
        name: `${project.title} - My Team`,
        project_id: project.id,
        description: `Team for ${project.title}`
      })
      
      toast.success('Successfully joined the project!')
      queryClient.invalidateQueries(['teams'])
      queryClient.invalidateQueries(['recommendations'])
      // Remove from recommendations immediately
      if (onReject) {
        onReject(project.id)
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to join project')
    } finally {
      setIsJoining(false)
    }
  }

  const handleReject = () => {
    if (onReject) {
      onReject(project.id)
    }
    toast.success('Recommendation dismissed')
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{project.title}</h3>
          <p className="text-sm text-gray-600 mt-1 line-clamp-2">{project.description}</p>
          <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
            <span>Team Size: {project.min_team_size}-{project.max_team_size}</span>
            <span>Status: {project.status}</span>
            {recommendation.matching_skills && recommendation.matching_skills.length > 0 && (
              <span className="text-accent-600">
                {recommendation.skill_overlap_count} matching skill{recommendation.skill_overlap_count !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          {recommendation.matching_skills && recommendation.matching_skills.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {recommendation.matching_skills.slice(0, 5).map((skill, idx) => (
                <span key={idx} className="px-2 py-1 bg-accent-100 text-accent-700 rounded text-xs">
                  {skill}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="ml-4 text-right">
          <div className="inline-flex items-center px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
            <TrendingUp className="w-4 h-4 mr-1" />
            {(similarity * 100).toFixed(0)}% Match
          </div>
        </div>
      </div>
      <div className="mt-4 flex items-center space-x-2">
        <button
          onClick={fetchExplanation}
          className="text-sm text-primary-600 hover:text-primary-700 flex items-center"
        >
          <Info className="w-4 h-4 mr-1" />
          Why this match?
        </button>
        <button
          onClick={handleJoin}
          disabled={isJoining || project.status !== 'open'}
          className="ml-auto px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
        >
          {isJoining ? 'Joining...' : 'Join Project'}
        </button>
        <button
          onClick={handleReject}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium"
        >
          Reject
        </button>
      </div>
      {showExplanation && explanation && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-sm text-gray-800 whitespace-pre-line">
            {explanation.explanation_text}
          </div>
          {explanation.overlapping_skills?.length > 0 && (
            <div className="mt-3 pt-3 border-t border-blue-200">
              <p className="text-xs font-semibold text-gray-700 mb-2">Matching Skills:</p>
              <div className="flex flex-wrap gap-2">
                {explanation.overlapping_skills.map((skill, idx) => (
                  <span key={idx} className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-xs font-medium">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
          {explanation.strengths?.length > 0 && (
            <div className="mt-2">
              <p className="text-xs font-semibold text-gray-700">Your Strengths:</p>
              <ul className="text-xs text-gray-600 mt-1 list-disc list-inside">
                {explanation.strengths.map((strength, idx) => (
                  <li key={idx}>{strength}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const TeamCard = ({ team }) => {
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{team.name}</h3>
          <p className="text-sm text-gray-600 mt-1">
            {team.project_title || team.hackathon_title}
          </p>
          <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
            <span>{team.member_count} members</span>
            <span className="px-2 py-1 bg-gray-100 rounded">{team.status}</span>
          </div>
        </div>
        <a
          href={`/team/${team.id}`}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          View Workspace
        </a>
      </div>
    </div>
  )
}

export default StudentDashboard
