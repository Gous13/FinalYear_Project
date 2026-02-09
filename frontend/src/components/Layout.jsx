import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../services/api'
import { LogOut, User, LayoutDashboard, Users, Settings } from 'lucide-react'
import NotificationDropdown from './NotificationDropdown'

const Layout = ({ children }) => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const { data: unreadCount = 0 } = useQuery({
    queryKey: ['messages-unread'],
    queryFn: async () => {
      const res = await api.get('/messages/unread-count')
      return res.data.unread_count || 0
    },
    enabled: !!user
  })

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const getNavigationLinks = () => {
    if (user?.role === 'admin') {
      return [
        { path: '/admin', label: 'Admin Dashboard', icon: Settings },
        { path: '/mentor', label: 'Mentor View', icon: Users },
        { path: '/dashboard', label: 'Student View', icon: LayoutDashboard }
      ]
    } else if (user?.role === 'mentor') {
      return [
        { path: '/mentor', label: 'Mentor Dashboard', icon: Users },
        { path: '/dashboard', label: 'Student View', icon: LayoutDashboard }
      ]
    } else {
      return [
        { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }
      ]
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <Link to="/dashboard" className="flex items-center">
                <span className="text-2xl font-bold text-primary-600">SynapseLink</span>
              </Link>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {getNavigationLinks().map((link) => {
                  const Icon = link.icon
                  return (
                    <Link
                      key={link.path}
                      to={link.path}
                      className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-700 hover:text-primary-600 border-b-2 border-transparent hover:border-primary-600"
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {link.label}
                    </Link>
                  )
                })}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <NotificationDropdown unreadCount={unreadCount} />
              <div className="flex items-center space-x-2 text-sm text-gray-700">
                <User className="w-4 h-4" />
                <span>{user?.full_name || user?.email}</span>
                <span className="px-2 py-1 text-xs bg-primary-100 text-primary-700 rounded-full">
                  {user?.role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-red-600"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  )
}

export default Layout
