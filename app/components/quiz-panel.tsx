"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { CheckCircle, XCircle, HelpCircle, ChevronLeft, ChevronRight } from "lucide-react"

interface QuizQuestion {
  question: string
  options: string[]
  correctAnswer: number
  concept: string
}

interface QuizPanelProps {
  questions: QuizQuestion[]
  isVisible: boolean
}

export default function QuizPanel({ questions, isVisible }: QuizPanelProps) {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [showResult, setShowResult] = useState(false)
  const [score, setScore] = useState(0)
  const [answeredQuestions, setAnsweredQuestions] = useState<boolean[]>([])

  if (!isVisible || questions.length === 0) {
    return (
      <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm h-fit">
        <CardContent className="p-8 text-center">
          <HelpCircle className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-600 mb-2">Quiz Questions</h3>
          <p className="text-slate-500">Upload and analyze a research paper to generate interactive quiz questions</p>
        </CardContent>
      </Card>
    )
  }

  const handleAnswerSelect = (answerIndex: number) => {
    if (showResult) return

    setSelectedAnswer(answerIndex)
    setShowResult(true)

    const newAnsweredQuestions = [...answeredQuestions]
    if (!newAnsweredQuestions[currentQuestion]) {
      newAnsweredQuestions[currentQuestion] = true
      setAnsweredQuestions(newAnsweredQuestions)

      if (answerIndex === questions[currentQuestion].correctAnswer) {
        setScore(score + 1)
      }
    }
  }

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
      setSelectedAnswer(null)
      setShowResult(false)
    }
  }

  const prevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1)
      setSelectedAnswer(null)
      setShowResult(false)
    }
  }

  const resetQuiz = () => {
    setCurrentQuestion(0)
    setSelectedAnswer(null)
    setShowResult(false)
    setScore(0)
    setAnsweredQuestions([])
  }

  const question = questions[currentQuestion]

  return (
    <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm h-fit sticky top-8">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center justify-between">
          <span className="text-lg font-bold text-slate-800">Quiz Questions</span>
          <span className="text-sm text-slate-500">
            {currentQuestion + 1} / {questions.length}
          </span>
        </CardTitle>
        <div className="w-full bg-slate-200 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-600 to-indigo-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
          />
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Concept Tag */}
        <div className="inline-block px-3 py-1 bg-gradient-to-r from-blue-100 to-indigo-100 rounded-full">
          <span className="text-sm font-medium text-blue-800">{question.concept}</span>
        </div>

        {/* Question */}
        <div>
          <h3 className="text-lg font-semibold text-slate-800 mb-4 leading-relaxed">{question.question}</h3>
        </div>

        {/* Answer Options */}
        <div className="space-y-3">
          {question.options.map((option, index) => {
            const isCorrect = index === question.correctAnswer
            const isSelected = selectedAnswer === index
            const showCorrectAnswer = showResult && isCorrect
            const showWrongAnswer = showResult && isSelected && !isCorrect

            return (
              <button
                key={index}
                onClick={() => handleAnswerSelect(index)}
                disabled={showResult}
                className={`w-full p-4 text-left rounded-lg border-2 transition-all duration-200 ${
                  showCorrectAnswer
                    ? "border-green-500 bg-green-50 text-green-800"
                    : showWrongAnswer
                      ? "border-red-500 bg-red-50 text-red-800"
                      : isSelected
                        ? "border-blue-500 bg-blue-50 text-blue-800"
                        : "border-slate-200 hover:border-blue-300 hover:bg-blue-50 text-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{option}</span>
                  {showResult && (
                    <div>
                      {showCorrectAnswer && <CheckCircle className="w-5 h-5 text-green-600" />}
                      {showWrongAnswer && <XCircle className="w-5 h-5 text-red-600" />}
                    </div>
                  )}
                </div>
              </button>
            )
          })}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-4">
          <Button
            variant="outline"
            onClick={prevQuestion}
            disabled={currentQuestion === 0}
            className="flex items-center gap-2"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </Button>

          {currentQuestion === questions.length - 1 ? (
            <Button
              onClick={resetQuiz}
              className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
            >
              Reset Quiz
            </Button>
          ) : (
            <Button
              onClick={nextQuestion}
              disabled={!showResult}
              className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </Button>
          )}
        </div>

        {/* Score Display */}
        {answeredQuestions.some(Boolean) && (
          <div className="pt-4 border-t border-slate-200">
            <div className="text-center">
              <span className="text-lg font-semibold text-slate-800">
                Score: {score} / {answeredQuestions.filter(Boolean).length}
              </span>
              <div className="text-sm text-slate-600 mt-1">
                {Math.round((score / Math.max(answeredQuestions.filter(Boolean).length, 1)) * 100)}% correct
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
