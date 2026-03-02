import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { CheckCircle, AlertCircle, ClipboardList } from 'lucide-react'
import PracticalAssessmentModal from './PracticalAssessmentModal'
import { useState } from 'react'

const SkillsSection = () => {
  const queryClient = useQueryClient()
  const [assessingSkill, setAssessingSkill] = useState(null)
  const [isPracticalSupported, setIsPracticalSupported] = useState(null) // null=loading, true/false

  const { data: skillsData } = useQuery({
    queryKey: ['my-skills'],
    queryFn: async () => {
      const res = await api.get('/skills/my-skills')
      return res.data.skills || []
    }
  })

  const skills = skillsData || []
  const passedCount = skills.filter(s => s.status === 'passed' || s.status === 'verified').length
  const failedCount = skills.filter(s => s.status === 'failed').length
  const unverifiedCount = skills.filter(s => s.status === 'unverified').length

  const handleAssessmentComplete = (updatedSkill) => {
    queryClient.invalidateQueries({ queryKey: ['my-skills'] })
    queryClient.invalidateQueries({ queryKey: ['profile'] })
    queryClient.invalidateQueries({ queryKey: ['recommendations'] })
    setAssessingSkill(null)
    setIsPracticalSupported(null)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900 flex items-center">
            <ClipboardList className="w-5 h-5 mr-2 text-primary-600" />
            Skill Verification
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Pass practical assessments to unlock project recommendations.
          </p>
        </div>
      </div>

      {skills.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-xl border border-dashed">
          <p className="text-gray-500 text-sm">Add skills in your profile to start verification.</p>
        </div>
      ) : (
        <>
          <div className="flex gap-4 mb-6 text-xs font-bold uppercase tracking-wider">
            <span className="flex items-center gap-1.5 text-green-600 bg-green-50 px-2.5 py-1 rounded-full border border-green-100">
              <CheckCircle className="w-3.5 h-3.5" />
              {passedCount} Verified
            </span>
            {failedCount > 0 && (
              <span className="flex items-center gap-1.5 text-red-600 bg-red-50 px-2.5 py-1 rounded-full border border-red-100">
                <AlertCircle className="w-3.5 h-3.5" />
                {failedCount} Failed
              </span>
            )}
            <span className="flex items-center gap-1.5 text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-100">
              <AlertCircle className="w-3.5 h-3.5" />
              {unverifiedCount} Unverified
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {skills.map((skill) => {
              const isPassed = skill.status === 'passed' || skill.status === 'verified';
              const isFailed = skill.status === 'failed';

              return (
                <div
                  key={skill.id}
                  className={`flex items-center justify-between p-4 rounded-xl border transition-all ${isPassed ? 'bg-white border-green-100 shadow-sm shadow-green-50' :
                    isFailed ? 'bg-white border-red-100 shadow-sm shadow-red-50' :
                      'bg-white border-gray-100 shadow-sm'
                    }`}
                >
                  <div className="flex flex-col">
                    <span className="text-sm font-bold text-gray-800">{skill.skill_name}</span>
                    <span className="text-[10px] font-medium text-gray-400 mt-0.5">
                      {isPassed ? `Score: ${skill.assessment_score}%` :
                        isFailed ? 'Verification Failed' : 'Action Required'}
                    </span>
                  </div>

                  {isPassed ? (
                    <div className="flex items-center gap-1 text-green-500 bg-green-50 p-1.5 rounded-lg border border-green-100">
                      <CheckCircle className="w-4 h-4" />
                    </div>
                  ) : (
                    <button
                      onClick={async () => {
                        setAssessingSkill(skill)
                        setIsPracticalSupported(null)
                        try {
                          const res = await api.get(`/skills/practical/check/${skill.id}`)
                          setIsPracticalSupported(!!res.data?.is_supported)
                        } catch {
                          setIsPracticalSupported(false)
                        }
                      }}
                      className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${isFailed ? 'bg-gray-100 text-gray-600 hover:bg-gray-200' : 'bg-primary-600 text-white hover:bg-primary-700 shadow-md shadow-primary-100'
                        }`}
                    >
                      {isFailed ? 'Retake' : 'Verify'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}

      {assessingSkill && isPracticalSupported === true && (
        <PracticalAssessmentModal
          skill={assessingSkill}
          onClose={() => { setAssessingSkill(null); setIsPracticalSupported(null) }}
          onComplete={handleAssessmentComplete}
        />
      )}
      {assessingSkill && isPracticalSupported === false && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 text-center max-w-sm">
            <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
            <h3 className="text-lg font-bold text-gray-900 mb-2">Notice</h3>
            <p className="text-gray-600 text-sm mb-6">
              Practical assessment for {assessingSkill.skill_name} is currently unavailable. Please try again later.
            </p>
            <button
              onClick={() => { setAssessingSkill(null); setIsPracticalSupported(null) }}
              className="w-full py-2 bg-gray-100 text-gray-800 font-bold rounded-lg hover:bg-gray-200 transition-all"
            >
              Close
            </button>
          </div>
        </div>
      )}
      {assessingSkill && isPracticalSupported === null && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 text-center">
            <p className="text-gray-600">Loading assessment...</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default SkillsSection
