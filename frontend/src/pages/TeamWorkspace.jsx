import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../services/api'
import Layout from '../components/Layout'
import toast from 'react-hot-toast'
import { Users, MessageSquare, FileText, Calendar, User, MessageCircle } from 'lucide-react'

const TeamWorkspace = () => {
  const { teamId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const queryClient = useQueryClient()

  const { data: team, isLoading } = useQuery({
    queryKey: ['team', teamId],
    queryFn: async () => {
      const res = await api.get(`/teams/${teamId}`)
      return res.data.team
    }
  })

  if (isLoading) {
    return (
      <Layout>
        <div className="text-center py-12">Loading team workspace...</div>
      </Layout>
    )
  }

  if (!team) {
    return (
      <Layout>
        <div className="text-center py-12 text-red-600">Team not found</div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{team.name}</h1>
              <p className="mt-2 text-gray-600">
                {team.project_title || team.hackathon_title}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                {team.status}
              </span>
            </div>
          </div>
        </div>

        {/* Team Members */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2 text-primary-600" />
            Team Members ({team.members?.length || 0})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {team.members?.map((member) => (
              <div
                key={member.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center min-w-0">
                    <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center shrink-0">
                      <User className="w-6 h-6 text-primary-600" />
                    </div>
                    <div className="ml-4 min-w-0">
                      <p className="font-semibold text-gray-900">{member.user_name}</p>
                      <p className="text-sm text-gray-600 truncate">{member.user_email}</p>
                      <span className="inline-block mt-1 px-2 py-1 bg-gray-100 rounded text-xs">
                        {member.role}
                      </span>
                    </div>
                  </div>
                  {member.user_id !== user?.id && (
                    <button
                      onClick={() => navigate(`/messages?with=${member.user_id}`)}
                      className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg shrink-0"
                      title="Message"
                    >
                      <MessageCircle className="w-5 h-5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Workspace Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Project Info */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <FileText className="w-5 h-5 mr-2 text-primary-600" />
              Project Details
            </h2>
            <div className="space-y-3 text-sm">
              <div>
                <p className="font-medium text-gray-700">Description</p>
                <p className="text-gray-600 mt-1">
                  {team.description || 'No description available'}
                </p>
              </div>
            </div>
          </div>

          {/* Team Activity */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <Calendar className="w-5 h-5 mr-2 text-primary-600" />
              Team Activity
            </h2>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Team Created</span>
                <span className="font-medium text-gray-900">
                  {new Date(team.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Status</span>
                <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-xs">
                  {team.status}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Collaboration Space */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <MessageSquare className="w-5 h-5 mr-2 text-primary-600" />
            Collaboration Space
          </h2>
          <div className="border border-gray-200 rounded-lg p-4 min-h-[200px]">
            <p className="text-gray-500 text-center py-8">
              Collaboration features coming soon. Use this space for team discussions and file sharing.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default TeamWorkspace
