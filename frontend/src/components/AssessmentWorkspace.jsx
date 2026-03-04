import { useState, useEffect } from 'react'
import { api } from '../services/api'
import toast from 'react-hot-toast'
import { Play, Send, ChevronLeft, Database, Code, Terminal, CheckCircle, XCircle } from 'lucide-react'

const AssessmentWorkspace = ({ skill, onClose, onComplete }) => {
    const [questions, setQuestions] = useState([])
    const [isCoding, setIsCoding] = useState(false)
    const [isSql, setIsSql] = useState(false)
    const [selectedLanguage, setSelectedLanguage] = useState('python')
    const [currentQIndex, setCurrentQIndex] = useState(0)
    const [answers, setAnswers] = useState({}) // Keyed by question ID
    const [outputs, setOutputs] = useState({}) // Keyed by question ID
    const [isLoading, setIsLoading] = useState(true)
    const [isRunning, setIsRunning] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)

    const currentQ = questions[currentQIndex]
    const code = answers[currentQ?.id] || ''
    const output = outputs[currentQ?.id] || null

    const languages = [
        { id: 'python', name: 'Python' },
        { id: 'java', name: 'Java' },
        { id: 'c', name: 'C' },
        { id: 'cpp', name: 'C++' },
        { id: 'javascript', name: 'JavaScript' }
    ]

    useEffect(() => {
        fetchQuestions()
    }, [skill])

    const fetchQuestions = async () => {
        try {
            setIsLoading(true)
            const res = await api.get(`/skills/assessment/${skill.skill_name}`)
            setQuestions(res.data.questions)
            setIsCoding(res.data.is_coding)
            setIsSql(res.data.is_sql)

            // Set initial language based on skill name if it matches
            const skillLower = skill.skill_name.toLowerCase()
            const matchedLang = languages.find(l => skillLower.includes(l.id))
            if (matchedLang) setSelectedLanguage(matchedLang.id)
            else if (res.data.is_coding) setSelectedLanguage('python')

            // Initialize empty answers for all questions
            const initialAnswers = {}
            res.data.questions.forEach(q => initialAnswers[q.id] = '')
            setAnswers(initialAnswers)

            setIsLoading(false)
        } catch (error) {
            toast.error(error.response?.data?.error || 'Failed to load assessment')
            onClose()
        }
    }

    const handleRun = async () => {
        if (!code.trim()) return toast.error('Please enter your code')
        setIsRunning(true)
        setOutputs(prev => ({ ...prev, [currentQ.id]: null }))
        try {
            const res = await api.post('/skills/run', {
                code,
                question_id: currentQ.id,
                language: selectedLanguage
            })
            setOutputs(prev => ({
                ...prev,
                [currentQ.id]: {
                    type: 'run',
                    passed_count: res.data.passed_count,
                    total_count: res.data.total_count,
                    results: res.data.results
                }
            }))
        } catch (error) {
            toast.error('Execution failed')
        } finally {
            setIsRunning(false)
        }
    }

    const handleSubmit = async () => {
        const unansweredCount = questions.length - Object.values(answers).filter(v => v?.trim()).length

        if (unansweredCount > 0) {
            if (!window.confirm(`You have ${unansweredCount} unanswered task(s). Submit anyway?`)) {
                return
            }
        }

        setIsSubmitting(true)
        try {
            const res = await api.post('/skills/submit', {
                answers,
                skill_assessment_id: skill.id,
                language: selectedLanguage
            })

            setOutputs(prev => ({
                ...prev,
                [currentQ.id]: {
                    type: 'submit',
                    score: res.data.score,
                    passed: res.data.passed,
                    results: []
                }
            }))

            if (res.data.passed) {
                toast.success(`Verification Passed! Total Score: ${res.data.score}%`)
                setTimeout(() => onComplete(res.data.skill), 2000)
            } else {
                toast.error(`Verification failed. Total Score: ${res.data.score}%`)
            }
        } catch (error) {
            toast.error('Submission failed')
        } finally {
            setIsSubmitting(false)
        }
    }

    if (isLoading) return (
        <div className="fixed inset-0 bg-gray-900 z-50 flex items-center justify-center">
            <div className="text-white flex flex-col items-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mb-4"></div>
                <p>Initializing Secure Assessment Environment...</p>
            </div>
        </div>
    )

    return (
        <div className="fixed inset-0 bg-gray-50 z-50 flex flex-col">
            {/* Header */}
            <div className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm">
                <div className="flex items-center space-x-4">
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg text-gray-500">
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                    <div className="h-6 w-px bg-gray-200" />
                    <div>
                        <span className="text-xs font-bold text-primary-600 uppercase tracking-widest">Skill Verification</span>
                        <h2 className="text-sm font-black text-gray-900">{skill.skill_name} Performance Task</h2>
                    </div>
                </div>

                <div className="flex items-center space-x-3">
                    {isCoding && (
                        <select
                            value={selectedLanguage}
                            onChange={(e) => setSelectedLanguage(e.target.value)}
                            className="bg-gray-100 border border-gray-200 text-xs font-bold rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                            {languages.map(lang => (
                                <option key={lang.id} value={lang.id}>{lang.name}</option>
                            ))}
                        </select>
                    )}
                    <div className="flex bg-gray-100 p-1 rounded-lg">
                        {questions.map((_, idx) => (
                            <button
                                key={idx}
                                onClick={() => setCurrentQIndex(idx)}
                                className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${currentQIndex === idx ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                Task {idx + 1}
                            </button>
                        ))}
                    </div>
                    <button
                        onClick={handleRun}
                        disabled={isRunning || isSubmitting}
                        className="flex items-center px-4 py-1.5 bg-gray-800 text-white rounded-lg hover:bg-gray-900 text-xs font-bold transition-all disabled:opacity-50"
                    >
                        <Play className="w-3.5 h-3.5 mr-2" />
                        RUN
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={isRunning || isSubmitting}
                        className="flex items-center px-4 py-1.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-xs font-bold transition-all shadow-md shadow-primary-100 disabled:opacity-50"
                    >
                        <Send className="w-3.5 h-3.5 mr-2" />
                        SUBMIT
                    </button>
                </div>
            </div>

            {/* Main Workspace */}
            <div className="flex-1 flex overflow-hidden">
                {/* Left Panel: Question */}
                <div className="w-1/2 border-r border-gray-200 overflow-y-auto bg-white p-8">
                    <div className="max-w-2xl mx-auto">
                        <div className="flex items-center gap-2 mb-2">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${currentQ.difficulty === 'easy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                                }`}>
                                {currentQ.difficulty}
                            </span>
                            <span className="text-xs text-gray-400 font-medium">
                                {isSql ? 'SQL Practical Assessment' : 'Coding Performance Task'}
                            </span>
                        </div>
                        <h1 className="text-2xl font-black text-gray-900 mb-6">{currentQ.title}</h1>

                        <div className="prose prose-sm text-gray-600 mb-8 whitespace-pre-line">
                            {currentQ.description}
                        </div>

                        <div className="space-y-6">
                            {isSql && (
                                <section>
                                    <h3 className="text-sm font-bold text-gray-900 flex items-center mb-3">
                                        <Database className="w-4 h-4 mr-2 text-primary-500" />
                                        Table Schema
                                    </h3>
                                    <div className="bg-gray-900 text-blue-300 p-4 rounded-xl font-mono text-xs overflow-x-auto border border-gray-800 shadow-inner">
                                        {currentQ.schema_details}
                                    </div>
                                </section>
                            )}

                            <div className="grid grid-cols-2 gap-4">
                                <section>
                                    <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Input Format</h4>
                                    <p className="text-xs text-gray-600 bg-gray-50 p-3 rounded-lg border border-gray-100">{currentQ.input_format}</p>
                                </section>
                                <section>
                                    <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Output Format</h4>
                                    <p className="text-xs text-gray-600 bg-gray-50 p-3 rounded-lg border border-gray-100">{currentQ.output_format}</p>
                                </section>
                            </div>

                            <section>
                                <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Constraints</h4>
                                <p className="text-xs text-gray-600 bg-gray-50 p-3 rounded-lg border border-gray-100">{currentQ.constraints}</p>
                            </section>

                            <div className="grid grid-cols-2 gap-4">
                                <section>
                                    <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Sample Input</h4>
                                    <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 font-mono text-xs text-gray-600 overflow-x-auto whitespace-pre">
                                        {currentQ.sample_input}
                                    </div>
                                </section>
                                <section>
                                    <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Sample Output</h4>
                                    <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 font-mono text-xs text-gray-600 overflow-x-auto whitespace-pre">
                                        {currentQ.sample_output}
                                    </div>
                                </section>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Panel: Editor & Console */}
                <div className="w-1/2 flex flex-col bg-gray-900">
                    <div className="flex-1 flex flex-col">
                        <div className="h-10 bg-gray-800 flex items-center px-4 justify-between border-b border-gray-700">
                            <div className="flex items-center space-x-2">
                                {isSql ? <Database className="w-3.5 h-3.5 text-gray-400" /> : <Terminal className="w-3.5 h-3.5 text-gray-400" />}
                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                                    {isSql ? 'SQL Editor' : `${selectedLanguage.toUpperCase()} Editor`}
                                </span>
                            </div>
                        </div>
                        <textarea
                            value={code}
                            onChange={(e) => setAnswers(prev => ({ ...prev, [currentQ.id]: e.target.value }))}
                            placeholder={isSql ? "-- Write your SQL query here..." : `// Write your ${selectedLanguage} code here...`}
                            className="flex-1 bg-gray-900 text-gray-100 p-6 font-mono text-sm focus:outline-none resize-none placeholder-gray-700 leading-relaxed"
                        />
                    </div>

                    {/* Console Output */}
                    <div className="h-1/3 bg-gray-950 border-t border-white/5 flex flex-col">
                        <div className="h-8 bg-gray-900 border-b border-white/5 flex items-center px-4">
                            <Terminal className="w-3 h-3 text-gray-500 mr-2" />
                            <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Console Output</span>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 font-mono text-xs scrollbar-hide">
                            {!output && !isRunning && !isSubmitting && (
                                <p className="text-gray-700 italic">No output to display. Click RUN to check against sample cases.</p>
                            )}

                            {(isRunning || isSubmitting) && (
                                <div className="flex items-center text-primary-400 animate-pulse">
                                    <div className="w-2 h-2 bg-primary-400 rounded-full mr-2"></div>
                                    <span>Executing verification suite...</span>
                                </div>
                            )}

                            {output && (
                                <div className="space-y-4">
                                    <div className={`p-4 rounded-xl border ${output.type === 'run' ? 'bg-gray-900 border-gray-800' :
                                        output.passed ? 'bg-green-950/30 border-green-900/50' : 'bg-red-950/30 border-red-900/50'
                                        }`}>
                                        <div className="flex items-center justify-between mb-3">
                                            <span className="font-bold text-gray-300">
                                                {output.type === 'run' ? 'Evaluation Result (Samples)' : 'Final Verification Result'}
                                            </span>
                                            {output.type === 'submit' && (
                                                <div className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${output.passed ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                                                    }`}>
                                                    {output.passed ? 'PASSED' : 'FAILED'}
                                                </div>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-4 text-sm">
                                            <div className="text-gray-400 font-bold">
                                                Score: <span className={output.score >= 60 ? 'text-green-400' : 'text-gray-200'}>{output.score || (output.passed_count / output.total_count * 100).toFixed(0)}%</span>
                                            </div>
                                            <div className="text-gray-400 font-bold">
                                                Passed: <span className="text-gray-200">{output.passed_count || output.results.filter(r => r.passed).length} / {output.total_count || output.results.length}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        {output.results.map((res, idx) => (
                                            <div key={idx} className="flex items-center text-[10px] py-1 border-b border-white/5">
                                                {res.passed ? (
                                                    <CheckCircle className="w-3 h-3 text-green-500 mr-2 shrink-0" />
                                                ) : (
                                                    <XCircle className="w-3 h-3 text-red-500 mr-2 shrink-0" />
                                                )}
                                                <span className={res.passed ? 'text-gray-400' : 'text-red-400'}>
                                                    Test Case {idx + 1}: {res.message}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default AssessmentWorkspace
