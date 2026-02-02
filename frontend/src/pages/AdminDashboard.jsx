import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import Layout from '../components/Layout'
import toast from 'react-hot-toast'
import { Settings, Users, Briefcase, Activity, BarChart3, RotateCcw, Trash2 } from 'lucide-react'

const AdminDashboard = () => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const [showFullResetConfirm, setShowFullResetConfirm] = useState(false)
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const res = await api.get('/admin/stats')
      return res.data.stats
    }
  })

  const { data: logs } = useQuery({
    queryKey: ['admin-logs'],
    queryFn: async () => {
      const res = await api.get('/admin/logs')
      return res.data.logs || []
    }
  })

  const { data: usersData } = useQuery({
    queryKey: ['admin-users'],
    queryFn: async () => {
      const res = await api.get('/admin/users')
      return res.data.users || []
    }
  })

  const resetProjectsMutation = useMutation({
    mutationFn: () => api.post('/admin/reset-projects'),
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-stats'])
      queryClient.invalidateQueries(['admin-logs'])
      setShowResetConfirm(false)
      toast.success('Project data reset. Users and profiles preserved.')
    },
    onError: (e) => toast.error(e.response?.data?.error || 'Reset failed')
  })

  const resetFullMutation = useMutation({
    mutationFn: () => api.post('/admin/reset-full'),
    onSuccess: () => {
      setShowFullResetConfirm(false)
      toast.success('Full reset complete. You will need to register again.')
      localStorage.removeItem('token')
      navigate('/login')
      window.location.reload()
    },
    onError: (e) => toast.error(e.response?.data?.error || 'Reset failed')
  })

  if (isLoading) {
    return (
      <Layout>
        <div className="text-center py-12">Loading admin dashboard...</div>
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
              <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
              <p className="mt-2 text-gray-600">System overview and management</p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowResetConfirm(true)}
                className="flex items-center px-4 py-2 border border-amber-300 text-amber-700 rounded-lg hover:bg-amber-50"
                title="Reset projects, teams. Keeps users and profiles."
              >
                <RotateCcw className="w-5 h-5 mr-2" />
                Reset Projects
              </button>
              <button
                onClick={() => setShowFullResetConfirm(true)}
                className="flex items-center px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50"
                title="Remove all data. Fresh start."
              >
                <Trash2 className="w-5 h-5 mr-2" />
                Full Reset
              </button>
              <Settings className="w-6 h-6 text-gray-400" />
            </div>
          </div>
        </div>

        {/* Full reset confirmation */}
        {showFullResetConfirm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl">
              <h3 className="text-lg font-semibold text-red-700 mb-2">Full System Reset?</h3>
              <p className="text-sm text-gray-600 mb-4">
                This will delete ALL data: users, profiles, projects, teams, messages. The database will be empty. You will need to register again. Application structure is unchanged.
              </p>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowFullResetConfirm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => resetFullMutation.mutate()}
                  disabled={resetFullMutation.isLoading}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  {resetFullMutation.isLoading ? 'Resetting...' : 'Full Reset'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Reset projects confirmation */}
        {showResetConfirm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Reset Project Data?</h3>
              <p className="text-sm text-gray-600 mb-4">
                This will remove all projects, teams, hackathons, and matching data. Users and profiles will be kept. Mentors can create new projects; students will see no joined teams.
              </p>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowResetConfirm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => resetProjectsMutation.mutate()}
                  disabled={resetProjectsMutation.isLoading}
                  className="px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 disabled:opacity-50"
                >
                  {resetProjectsMutation.isLoading ? 'Resetting...' : 'Reset Projects'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Users"
            value={stats?.users?.total || 0}
            subtitle={`${stats?.users?.active || 0} active`}
            icon={Users}
            color="primary"
          />
          <StatCard
            title="Students"
            value={stats?.users?.students || 0}
            subtitle="Registered"
            icon={Users}
            color="accent"
          />
          <StatCard
            title="Projects"
            value={stats?.projects?.total || 0}
            subtitle={`${stats?.projects?.open || 0} open`}
            icon={Briefcase}
            color="purple"
          />
          <StatCard
            title="Teams"
            value={stats?.teams?.total || 0}
            subtitle={`${stats?.teams?.active || 0} active`}
            icon={Activity}
            color="blue"
          />
        </div>

        {/* Detailed Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* User Breakdown */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <Users className="w-5 h-5 mr-2 text-primary-600" />
              User Breakdown
            </h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Students</span>
                <span className="font-semibold text-gray-900">
                  {stats?.users?.students || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Mentors</span>
                <span className="font-semibold text-gray-900">
                  {stats?.users?.mentors || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Admins</span>
                <span className="font-semibold text-gray-900">
                  {stats?.users?.admins || 0}
                </span>
              </div>
              <div className="flex items-center justify-between pt-3 border-t">
                <span className="font-medium text-gray-900">Total Active</span>
                <span className="font-bold text-primary-600">
                  {stats?.users?.active || 0}
                </span>
              </div>
            </div>
          </div>

          {/* Project Status */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <Briefcase className="w-5 h-5 mr-2 text-primary-600" />
              Project Status
            </h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Open</span>
                <span className="font-semibold text-gray-900">
                  {stats?.projects?.open || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">In Progress</span>
                <span className="font-semibold text-gray-900">
                  {stats?.projects?.in_progress || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Completed</span>
                <span className="font-semibold text-gray-900">
                  {stats?.projects?.completed || 0}
                </span>
              </div>
              <div className="flex items-center justify-between pt-3 border-t">
                <span className="font-medium text-gray-900">Total</span>
                <span className="font-bold text-primary-600">
                  {stats?.projects?.total || 0}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Users List */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2 text-primary-600" />
            All Users ({usersData?.length || 0})
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {usersData && usersData.length > 0 ? (
                  usersData.map((user) => (
                    <tr key={user.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {user.full_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-primary-100 text-primary-800">
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          user.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                      No users found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Activity Logs */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-primary-600" />
            Recent Activity
          </h2>
          <div className="space-y-2">
            {logs && logs.length > 0 ? (
              logs.slice(0, 10).map((log) => (
                <div
                  key={log.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{log.action}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(log.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className="text-xs text-gray-500">
                    {log.entity_type} #{log.entity_id}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">No activity logs</div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}

const StatCard = ({ title, value, subtitle, icon: Icon, color = 'primary' }) => {
  const colorClasses = {
    primary: 'bg-primary-100 text-primary-600',
    accent: 'bg-accent-100 text-accent-600',
    purple: 'bg-purple-100 text-purple-600',
    blue: 'bg-blue-100 text-blue-600'
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard
