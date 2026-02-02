import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import Layout from '../components/Layout'
import toast from 'react-hot-toast'
import { Mail, Send, UserPlus, Search } from 'lucide-react'

const Messages = () => {
  const queryClient = useQueryClient()
  const [selectedUserId, setSelectedUserId] = useState(null)
  const [showNewChat, setShowNewChat] = useState(false)
  const [emailSearch, setEmailSearch] = useState('')
  const [replyText, setReplyText] = useState('')
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })

  const { data: conversationsData, isLoading: convLoading } = useQuery({
    queryKey: ['messages-conversations'],
    queryFn: async () => {
      const res = await api.get('/messages/conversations')
      return res.data.conversations || []
    }
  })

  const { data: threadData, isLoading: threadLoading } = useQuery({
    queryKey: ['messages-thread', selectedUserId],
    queryFn: async () => {
      const res = await api.get(`/messages/conversations/${selectedUserId}`)
      return res.data
    },
    enabled: !!selectedUserId && !showNewChat
  })

  useEffect(() => {
    if (threadData && selectedUserId) {
      queryClient.invalidateQueries(['messages-unread'])
      queryClient.invalidateQueries(['messages-conversations'])
    }
  }, [threadData, selectedUserId, queryClient])

  const [debouncedEmail, setDebouncedEmail] = useState('')
  useEffect(() => {
    const t = setTimeout(() => setDebouncedEmail(emailSearch), 300)
    return () => clearTimeout(t)
  }, [emailSearch])

  const { data: recipientsData } = useQuery({
    queryKey: ['messages-recipients', debouncedEmail],
    queryFn: async () => {
      const res = await api.get(`/messages/recipients?q=${encodeURIComponent(debouncedEmail)}`)
      return res.data.users || []
    },
    enabled: showNewChat && debouncedEmail.length >= 2
  })

  const sendMutation = useMutation({
    mutationFn: async (data) => api.post('/messages', data),
    onSuccess: () => {
      queryClient.invalidateQueries(['messages-conversations'])
      queryClient.invalidateQueries(['messages-thread', selectedUserId])
      queryClient.invalidateQueries(['messages-unread'])
      setReplyText('')
      toast.success('Sent!')
    },
    onError: (e) => toast.error(e.response?.data?.error || 'Failed to send')
  })

  useEffect(() => {
    if (threadData?.messages?.length) scrollToBottom()
  }, [threadData?.messages])

  const conversations = conversationsData || []
  const otherUser = threadData?.other_user
  const messages = threadData?.messages || []

  const handleSendReply = (e) => {
    e.preventDefault()
    const content = replyText.trim()
    if (!content) return
    const receiverId = selectedUserId
    if (!receiverId) return
    sendMutation.mutate({ receiver_id: receiverId, content })
  }

  const handleStartNewChat = (user) => {
    setSelectedUserId(user.id)
    setShowNewChat(false)
    setEmailSearch('')
  }

  const handleNewMessage = () => {
    setSelectedUserId(null)
    setShowNewChat(true)
  }

  const filteredRecipients = recipientsData || []

  return (
    <Layout>
      <div className="bg-white rounded-lg shadow-sm overflow-hidden" style={{ height: 'calc(100vh - 12rem)', minHeight: 400 }}>
        <div className="flex h-full">
          {/* Left: Conversations */}
          <div className="w-80 border-r border-gray-200 flex flex-col shrink-0">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900">Messages</h2>
              <button
                onClick={handleNewMessage}
                className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg"
                title="New message"
              >
                <UserPlus className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              {convLoading ? (
                <div className="p-4 text-center text-gray-500 text-sm">Loading...</div>
              ) : conversations.length === 0 && !showNewChat ? (
                <div className="p-4 text-center text-gray-500 text-sm">
                  No conversations yet.
                  <button
                    onClick={handleNewMessage}
                    className="block mt-2 text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Start a chat
                  </button>
                </div>
              ) : showNewChat ? (
                <div className="p-4">
                  <div className="mb-3">
                    <label className="block text-xs font-medium text-gray-500 mb-1">Search by email</label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={emailSearch}
                        onChange={(e) => setEmailSearch(e.target.value)}
                        placeholder="Type email to search..."
                        className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-primary-500 focus:border-primary-500"
                        autoFocus
                      />
                    </div>
                  </div>
                  {emailSearch.length < 2 ? (
                    <p className="text-xs text-gray-400">Type at least 2 characters</p>
                  ) : (
                    <div className="space-y-1">
                      {filteredRecipients.length === 0 ? (
                        <p className="text-sm text-gray-500">No users found</p>
                      ) : (
                        filteredRecipients.map((u) => (
                          <button
                            key={u.id}
                            onClick={() => handleStartNewChat(u)}
                            className="w-full text-left p-3 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-100"
                          >
                            <p className="font-medium text-gray-900 text-sm">{u.full_name}</p>
                            <p className="text-xs text-gray-500">{u.email}</p>
                          </button>
                        ))
                      )}
                    </div>
                  )}
                  <button
                    onClick={() => { setShowNewChat(false); setEmailSearch('') }}
                    className="mt-3 text-sm text-gray-500 hover:text-gray-700"
                  >
                    ← Back to conversations
                  </button>
                </div>
              ) : (
                conversations.map((conv) => {
                  const other = conv.other_user
                  const last = conv.last_message
                  const preview = last?.content?.length > 40 ? last.content.slice(0, 40) + '...' : last?.content || ''
                  const isSelected = selectedUserId === other.id
                  return (
                    <button
                      key={other.id}
                      onClick={() => { setSelectedUserId(other.id); setShowNewChat(false) }}
                      className={`w-full text-left p-4 border-b border-gray-100 hover:bg-gray-50 ${
                        isSelected ? 'bg-primary-50 border-l-4 border-l-primary-600' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-gray-900 truncate">{other.full_name}</span>
                        {conv.unread_count > 0 && (
                          <span className="flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-red-500 px-1.5 text-xs font-bold text-white">
                            {conv.unread_count}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 truncate mt-0.5">{preview}</p>
                    </button>
                  )
                })
              )}
            </div>
          </div>

          {/* Right: Chat thread */}
          <div className="flex-1 flex flex-col min-w-0">
            {!selectedUserId ? (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <Mail className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                  <p className="font-medium">Select a conversation</p>
                  <p className="text-sm mt-1">or start a new chat</p>
                </div>
              </div>
            ) : (
              <>
                <div className="p-4 border-b border-gray-200 flex items-center">
                  <div>
                    <h3 className="font-semibold text-gray-900">{otherUser?.full_name}</h3>
                    <p className="text-xs text-gray-500 capitalize">{otherUser?.role}</p>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {threadLoading ? (
                    <div className="text-center py-8 text-gray-500">Loading...</div>
                  ) : (
                    messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.is_mine ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[75%] rounded-2xl px-4 py-2 ${
                            msg.is_mine
                              ? 'bg-primary-600 text-white rounded-br-md'
                              : 'bg-gray-200 text-gray-900 rounded-bl-md'
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                          <p className={`text-xs mt-1 ${msg.is_mine ? 'text-primary-100' : 'text-gray-500'}`}>
                            {msg.created_at ? new Date(msg.created_at).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) : ''}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={messagesEndRef} />
                </div>
                <form onSubmit={handleSendReply} className="p-4 border-t border-gray-200">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      placeholder="Type a message..."
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    <button
                      type="submit"
                      disabled={!replyText.trim() || sendMutation.isLoading}
                      className="p-3 bg-primary-600 text-white rounded-full hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Send className="w-5 h-5" />
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default Messages
