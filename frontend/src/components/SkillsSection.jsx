import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { CheckCircle, AlertCircle, ClipboardList } from 'lucide-react'
import SkillAssessmentModal from './SkillAssessmentModal'
import { useState } from 'react'

const SkillsSection = () => {
  const queryClient = useQueryClient()
  const [assessingSkill, setAssessingSkill] = useState(null)

  const { data: skillsData } = useQuery({
    queryKey: ['my-skills'],
    queryFn: async () => {
      const res = await api.get('/skills/my-skills')
      return res.data.skills || []
    }
  })

  const skills = skillsData || []
  const verifiedCount = skills.filter(s => s.status === 'verified').length
  const unverifiedCount = skills.filter(s => s.status === 'unverified').length

  const handleAssessmentComplete = () => {
    queryClient.invalidateQueries({ queryKey: ['my-skills'] })
    queryClient.invalidateQueries({ queryKey: ['profile'] })
    queryClient.invalidateQueries({ queryKey: ['recommendations'] })
    setAssessingSkill(null)
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-2 flex items-center">
        <ClipboardList className="w-5 h-5 mr-2 text-primary-600" />
        My Skills
      </h2>
      <p className="text-sm text-gray-600 mb-4">
        Verified skills count toward project recommendations. Complete assessments to verify.
      </p>
      {skills.length === 0 ? (
        <p className="text-gray-500 text-sm">Add skills in your profile to see them here and take assessments.</p>
      ) : (
        <>
          <div className="flex gap-4 mb-4 text-sm">
            <span className="flex items-center gap-1 text-green-600">
              <CheckCircle className="w-4 h-4" />
              {verifiedCount} verified
            </span>
            <span className="flex items-center gap-1 text-amber-600">
              <AlertCircle className="w-4 h-4" />
              {unverifiedCount} unverified
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {skills.map((skill) => (
              <span
                key={skill.id}
                className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
                  skill.status === 'verified'
                    ? 'bg-green-50 text-green-800 border border-green-200'
                    : 'bg-amber-50 text-amber-800 border border-amber-200'
                }`}
              >
                {skill.skill_name}
                {skill.status === 'verified' ? (
                  <span className="text-xs">✓ {skill.assessment_score}%</span>
                ) : (
                  <button
                    onClick={() => setAssessingSkill(skill)}
                    className="ml-1 px-2 py-0.5 text-xs bg-primary-600 text-white rounded hover:bg-primary-700"
                  >
                    Verify
                  </button>
                )}
              </span>
            ))}
          </div>
        </>
      )}

      {assessingSkill && (
        <SkillAssessmentModal
          skill={assessingSkill}
          onClose={() => setAssessingSkill(null)}
          onComplete={handleAssessmentComplete}
        />
      )}
    </div>
  )
}

export default SkillsSection
