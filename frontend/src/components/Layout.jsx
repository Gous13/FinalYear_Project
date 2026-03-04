import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../services/api'
import { LogOut, User, LayoutDashboard, Users, Settings, Trophy, ChevronDown, Star } from 'lucide-react'
import NotificationDropdown from './NotificationDropdown'
import { useState, useRef, useEffect } from 'react'

const Layout = ({ children }) => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [showScoreDropdown, setShowScoreDropdown] = useState(false)
  const scoreDropdownRef = useRef(null)

  const { data: unreadCount = 0 } = useQuery({
    queryKey: ['messages-unread'],
    queryFn: async () => {
      const res = await api.get('/messages/unread-count')
      return res.data.unread_count || 0
    },
    enabled: !!user
  })

  const { data: totalScore = 0 } = useQuery({
    queryKey: ['total-score'],
    queryFn: async () => {
      const res = await api.get('/profiles/total-score')
      return res.data.total_score || 0
    },
    enabled: user?.role === 'student'
  })

  const { data: verifiedSkills = [] } = useQuery({
    queryKey: ['verified-skills'],
    queryFn: async () => {
      const res = await api.get('/skills/verified-only')
      return res.data.skills || []
    },
    enabled: user?.role === 'student' && showScoreDropdown
  })

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (scoreDropdownRef.current && !scoreDropdownRef.current.contains(event.target)) {
        setShowScoreDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

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
              {user?.role === 'student' && (
                <div className="relative" ref={scoreDropdownRef}>
                  <button
                    onClick={() => setShowScoreDropdown(!showScoreDropdown)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-full hover:shadow-md transition-all group"
                  >
                    <div className="p-1 bg-amber-500 rounded-full text-white group-hover:scale-110 transition-transform shadow-sm">
                      <Trophy className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex flex-col items-start">
                      <span className="text-[10px] font-black text-amber-600 uppercase leading-none tracking-tight">Verified Score</span>
                      <span className="text-sm font-black text-amber-800 leading-none">{totalScore}</span>
                    </div>
                    <ChevronDown className={`w-3 h-3 text-amber-500 transition-transform ${showScoreDropdown ? 'rotate-180' : ''}`} />
                  </button>

                  {showScoreDropdown && (
                    <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-gray-100 py-4 z-50 animate-in fade-in zoom-in duration-200">
                      <div className="px-4 mb-3">
                        <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest">Verified Skills</h3>
                      </div>
                      <div className="max-h-60 overflow-y-auto px-2 space-y-1">
                        {verifiedSkills.length > 0 ? (
                          verifiedSkills.map((s, idx) => (
                            <div key={idx} className="flex items-center justify-between p-2 rounded-xl hover:bg-amber-50 group transition-colors">
                              <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-lg bg-amber-100 flex items-center justify-center">
                                  <Star className="w-3 h-3 text-amber-600" />
                                </div>
                                <span className="text-sm font-bold text-gray-700">{s.skill_name}</span>
                              </div>
                              <span className="text-sm font-black text-amber-600">{s.score}%</span>
                            </div>
                          ))
                        ) : (
                          <div className="p-4 text-center">
                            <p className="text-xs text-gray-500">No skills verified yet</p>
                          </div>
                        )}
                      </div>
                      <div className="mt-3 pt-3 border-t border-gray-50 px-4 flex items-center justify-between">
                        <span className="text-xs font-bold text-gray-500">Total Cumulative</span>
                        <span className="text-lg font-black text-amber-700">{totalScore}</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
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
