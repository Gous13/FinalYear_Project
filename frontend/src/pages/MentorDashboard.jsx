import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import Layout from '../components/Layout'
import toast from 'react-hot-toast'
import {
  Plus, Briefcase, Users, Sparkles, Settings,
  CheckCircle, XCircle, Play, Eye, UsersRound
} from 'lucide-react'

const MentorDashboard = () => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [projectData, setProjectData] = useState({
    title: '',
    description: '',
    required_skills: '',
    min_team_size: 3,
    max_team_size: 5,
    preferred_team_size: 4,
    deadline: ''
  })

  // Fetch projects
  const { data: projectsData } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const res = await api.get('/projects/projects')
      return res.data.projects || []
    }
  })

  // Fetch hackathons
  const { data: hackathonsData } = useQuery({
    queryKey: ['hackathons'],
    queryFn: async () => {
      const res = await api.get('/projects/hackathons')
      return res.data.hackathons || []
    }
  })

  // Create project mutation
  const projectMutation = useMutation({
    mutationFn: async (data) => {
      return api.post('/projects/projects', data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['projects'])
      setShowProjectModal(false)
      toast.success('Project created successfully!')
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to create project')
    }
  })

  const handleProjectSubmit = (e) => {
    e.preventDefault()
    projectMutation.mutate(projectData)
  }


  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Mentor Dashboard</h1>
              <p className="mt-2 text-gray-600">Manage projects, hackathons, and team formation</p>
            </div>
            <button
              onClick={() => setShowProjectModal(true)}
              className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              <Plus className="w-5 h-5 mr-2" />
              Create Project
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-3 bg-primary-100 rounded-lg">
                <Briefcase className="w-6 h-6 text-primary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Projects</p>
                <p className="text-2xl font-bold text-gray-900">{projectsData?.length || 0}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-3 bg-accent-100 rounded-lg">
                <Users className="w-6 h-6 text-accent-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Hackathons</p>
                <p className="text-2xl font-bold text-gray-900">{hackathonsData?.length || 0}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Sparkles className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Teams Formed</p>
                <p className="text-2xl font-bold text-gray-900">
                  {projectsData?.reduce((acc, p) => acc + (p.teams?.length || 0), 0) || 0}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Create Project Modal */}
        {showProjectModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b">
                <h2 className="text-2xl font-bold text-gray-900">Create New Project</h2>
              </div>
              <form onSubmit={handleProjectSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Project Title *
                  </label>
                  <input
                    type="text"
                    value={projectData.title}
                    onChange={(e) => setProjectData({ ...projectData, title: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description *
                  </label>
                  <textarea
                    value={projectData.description}
                    onChange={(e) => setProjectData({ ...projectData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    rows="4"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Required Skills
                  </label>
                  <textarea
                    value={projectData.required_skills}
                    onChange={(e) => setProjectData({ ...projectData, required_skills: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    rows="2"
                    placeholder="e.g., Python, React, Machine Learning"
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Min Team Size</label>
                    <input
                      type="number"
                      min="2"
                      max="10"
                      value={projectData.min_team_size}
                      onChange={(e) => setProjectData({ ...projectData, min_team_size: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Team Size</label>
                    <input
                      type="number"
                      min="2"
                      max="10"
                      value={projectData.max_team_size}
                      onChange={(e) => setProjectData({ ...projectData, max_team_size: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Size</label>
                    <input
                      type="number"
                      min="2"
                      max="10"
                      value={projectData.preferred_team_size}
                      onChange={(e) => setProjectData({ ...projectData, preferred_team_size: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Deadline</label>
                  <input
                    type="datetime-local"
                    value={projectData.deadline}
                    onChange={(e) => setProjectData({ ...projectData, deadline: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowProjectModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={projectMutation.isLoading}
                    className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
                  >
                    {projectMutation.isLoading ? 'Creating...' : 'Create Project'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Projects List */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Projects</h2>
          {projectsData?.length > 0 ? (
            <div className="space-y-4">
              {projectsData.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  navigate={navigate}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No projects yet. Create one to get started!
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}

const ProjectCard = ({ project, navigate }) => {
  const queryClient = useQueryClient()
  const [showRecs, setShowRecs] = useState(false)
  const { data: recs, isLoading: recsLoading } = useQuery({
    queryKey: ['recommendations', project.id],
    queryFn: async () => {
      const res = await api.get(`/invitations/recommendations/${project.id}`)
      return res.data.recommendations || []
    },
    enabled: showRecs
  })

  const inviteMutation = useMutation({
    mutationFn: async (studentId) => {
      return api.post('/invitations/invite', {
        project_id: project.id,
        student_id: studentId
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['recommendations', project.id])
      toast.success('Invitation sent!')
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to send invite')
    }
  })

  // Count total students who have joined this project
  const totalJoined = project.teams?.reduce((sum, team) => sum + (team.member_count || 0), 0) || 0

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-gray-900">{project.title}</h3>
            <div className="flex gap-2">
              {totalJoined > 0 && (
                <button
                  onClick={() => navigate(`/project/${project.id}/workspace`)}
                  className="inline-flex items-center gap-1 px-2 py-1 text-sm text-primary-600 hover:bg-primary-50 rounded transition-colors"
                  title="View team members"
                >
                  <UsersRound className="w-4 h-4" />
                  View Team
                </button>
              )}
              <button
                onClick={() => setShowRecs(!showRecs)}
                className="inline-flex items-center gap-1 px-2 py-1 text-sm text-purple-600 hover:bg-purple-50 rounded transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                {showRecs ? 'Hide Eligible Students' : 'Eligible Students'}
              </button>
            </div>
          </div>
          <p className="text-sm text-gray-600 mt-1 line-clamp-2">{project.description}</p>
          <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
            <span>Team Size: {project.min_team_size}-{project.max_team_size}</span>
            <span className="px-2 py-1 bg-gray-100 rounded">{project.status}</span>
            <span className="font-medium text-primary-600">
              {project.teams?.length || 0} team{project.teams?.length !== 1 ? 's' : ''} formed
            </span>
            <span className="text-gray-600">
              {totalJoined} student{totalJoined !== 1 ? 's' : ''} joined
            </span>
          </div>
        </div>
      </div>

      {/* Eligible Students Section */}
      {showRecs && (
        <div className="mt-4 pt-4 border-t bg-purple-50 -mx-4 px-4 pb-4 rounded-b-lg">
          <h4 className="text-sm font-bold text-purple-900 mb-3 flex items-center">
            <Sparkles className="w-4 h-4 mr-2" />
            AI Recommended Students (Ranked by Verified Score)
          </h4>
          {recsLoading ? (
            <div className="text-sm text-purple-600 py-2">Loading recommendations...</div>
          ) : recs?.length > 0 ? (
            <div className="space-y-2">
              {recs.map((rec) => (
                <div key={rec.student_id} className="bg-white p-3 rounded-md border border-purple-100 flex items-center justify-between shadow-sm">
                  <div>
                    <p className="font-semibold text-gray-900">{rec.student_name}</p>
                    <p className="text-xs text-gray-500">
                      Verified Skill: <span className="font-medium text-purple-700">{rec.skill_name}</span>
                      (Score: <span className="font-bold text-primary-600">{rec.skill_score}</span>)
                    </p>
                  </div>
                  <button
                    onClick={() => inviteMutation.mutate(rec.student_id)}
                    disabled={inviteMutation.isLoading || rec.invitation_sent}
                    className={`px-3 py-1.5 rounded-md text-xs font-bold transition-colors ${rec.invitation_sent
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-primary-600 text-white hover:bg-primary-700'
                      }`}
                  >
                    {rec.invitation_sent ? 'Invite Sent' : inviteMutation.isLoading ? 'Sending...' : 'Send Invite'}
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-purple-600 py-2 italic text-center">
              No verified students found for the required skills yet.
            </div>
          )}
        </div>
      )}

      {project.teams && project.teams.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-sm font-medium text-gray-700 mb-2">Formed Teams:</p>
          <div className="space-y-2">
            {project.teams.map((team) => (
              <div key={team.id} className="flex items-center justify-between text-sm bg-gray-50 p-2 rounded">
                <span className="text-gray-700 font-medium">{team.name}</span>
                <span className="text-gray-500">{team.member_count} member{team.member_count !== 1 ? 's' : ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {totalJoined > 0 && (!project.teams || project.teams.length === 0) && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-sm text-gray-600">
            {totalJoined} student{totalJoined !== 1 ? 's' : ''} joined.
            {totalJoined < project.preferred_team_size
              ? ` Need ${project.preferred_team_size - totalJoined} more to auto-form teams.`
              : ' Teams will be auto-formed when enough students join.'}
          </p>
        </div>
      )}
    </div>
  )
}

export default MentorDashboard
