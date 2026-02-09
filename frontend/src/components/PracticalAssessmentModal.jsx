import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import { X, CheckCircle, XCircle, Clock, Code } from 'lucide-react'

const ASSESSMENT_DURATION_MINUTES = 15

const PracticalAssessmentModal = ({ skill, onClose, onComplete }) => {
  const [step, setStep] = useState('check') // check | questions | result
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [assessment, setAssessment] = useState(null)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(ASSESSMENT_DURATION_MINUTES * 60)
  const [timerActive, setTimerActive] = useState(false)

  const startTimer = useCallback(() => {
    setTimerActive(true)
    setSecondsLeft(ASSESSMENT_DURATION_MINUTES * 60)
  }, [])

  useEffect(() => {
    if (!timerActive) return
    const t = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          clearInterval(t)
          setTimerActive(false)
          return 0
        }
        return s - 1
      })
    }, 1000)
    return () => clearInterval(t)
  }, [timerActive])

  const formatTime = (s) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  const handleStart = async () => {
    if (!skill?.id) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.post(`/skills/practical/start/${skill.id}`)
      setAssessment(res.data)
      setAnswers({})
      setStep('questions')
      startTimer()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start assessment')
    } finally {
      setLoading(false)
    }
  }

  const handleCheck = async () => {
    if (!skill?.id) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.get(`/skills/practical/check/${skill.id}`)
      if (res.data.available) {
        setStep('ready')
      } else {
        setError(res.data.message || 'Assessment not available')
        setStep('check')
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to check')
      setStep('check')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (skill?.id && step === 'check') {
      handleCheck()
    }
  }, [skill?.id])

  const handleAnswerChange = (questionId, value) => {
    setAnswers((prev) => ({ ...prev, [String(questionId)]: value }))
  }

  const handleSubmit = async () => {
    if (!assessment?.set_id || !skill?.id) return
    const qIds = assessment.questions?.map((q) => q.id) || []
    const missing = qIds.filter((id) => !(answers[String(id)] || '').trim())
    if (missing.length > 0) {
      setError('Please complete all questions')
      return
    }
    setSubmitting(true)
    setError(null)
    setTimerActive(false)
    try {
      const answersPayload = {}
      assessment.questions?.forEach((q) => {
        const v = answers[String(q.id)] ?? answers[q.id] ?? ''
        if (v != null && String(v).trim()) {
          answersPayload[String(q.id)] = String(v).trim()
        }
      })
      const res = await api.post('/skills/practical/submit', {
        student_skill_id: skill.id,
        set_id: assessment.set_id,
        answers: answersPayload,
      })
      let data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
      if (!data || data.score === undefined) {
        data = { score: 0, passed: true, easy_score: 0, hard_score: 0, skill: null }
      }
      setResult(data)
      setStep('result')
    } catch (err) {
      setError(err.response?.data?.error || 'Submission failed')
    } finally {
      setSubmitting(false)
    }
  }

  if (!skill) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto flex flex-col">
        <div className="p-6 border-b flex items-center justify-between flex-shrink-0">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Code className="w-5 h-5 text-primary-600" />
            Skill Verification: {skill.skill_name}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 flex-1 overflow-y-auto">
          {step === 'check' && (
            <div className="text-center py-8">
              {loading ? (
                <p className="text-gray-500">Checking assessment availability...</p>
              ) : error ? (
                <div>
                  <p className="text-amber-600 mb-4">{error}</p>
                  <p className="text-sm text-gray-500 mb-4">
                    This skill may use MCQ assessment instead, or assessment is not yet available.
                  </p>
                  <button
                    onClick={onClose}
                    className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
                  >
                    Close
                  </button>
                </div>
              ) : (
                <p className="text-gray-600">Loading...</p>
              )}
            </div>
          )}

          {step === 'ready' && (
            <div className="text-center py-8">
              <p className="text-gray-700 mb-4">
                You will receive <strong>1 Easy</strong> and <strong>1 Hard</strong> practical task.
                Complete both within {ASSESSMENT_DURATION_MINUTES} minutes.
              </p>
              <button
                onClick={handleStart}
                disabled={loading}
                className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {loading ? 'Starting...' : 'Start Assessment'}
              </button>
            </div>
          )}

          {step === 'questions' && assessment && (
            <div className="space-y-6">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-1 text-gray-600">
                  <Clock className="w-4 h-4" />
                  Time remaining: {formatTime(secondsLeft)}
                </span>
                {secondsLeft <= 60 && (
                  <span className="text-amber-600 font-medium">Hurry! Less than 1 minute left.</span>
                )}
                {secondsLeft === 0 && (
                  <span className="text-red-600 font-medium">Time&apos;s up. Submit now.</span>
                )}
              </div>

              {error && (
                <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
              )}

              {assessment.questions?.map((q) => (
                <div key={q.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        q.difficulty === 'easy' ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {q.difficulty}
                    </span>
                    <span className="text-xs text-gray-500">({q.evaluation_type})</span>
                  </div>
                  <p className="font-medium text-gray-900 mb-2">{q.question_text}</p>
                  <textarea
                    value={answers[String(q.id)] ?? q.starter_code ?? ''}
                    onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                    placeholder="Write your code or answer here..."
                    className="w-full h-32 p-3 font-mono text-sm border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                    spellCheck={false}
                  />
                </div>
              ))}

              <div className="flex justify-end gap-2 pt-4">
                <button
                  onClick={onClose}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting || secondsLeft < 0}
                  className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Assessment'}
                </button>
              </div>
            </div>
          )}

          {step === 'result' && result && (
            <div className="text-center py-8">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <p className="text-xl font-semibold text-green-700">Assessment complete</p>
              <p className="text-gray-600 mt-2">
                Score: {result.score ?? 0}%
                {result.easy_score != null && result.hard_score != null && (
                  <span className="text-sm text-gray-500"> (Easy: {result.easy_score}%, Hard: {result.hard_score}%)</span>
                )}
              </p>
              <p className="text-sm text-gray-500 mt-1">{skill.skill_name} is now verified with this score.</p>
              <button
                onClick={() => {
                  onComplete?.(result.skill)
                  onClose()
                }}
                className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default PracticalAssessmentModal
