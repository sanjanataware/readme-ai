"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Brain, ChevronDown, ChevronRight, Quote, Lightbulb } from "lucide-react"

interface Concept {
  title: string
  summary: string
  citations: string[]
  importance: string
}

interface ConceptsDisplayProps {
  concepts: Concept[]
}

export default function ConceptsDisplay({ concepts }: ConceptsDisplayProps) {
  const [expandedConcepts, setExpandedConcepts] = useState<Set<number>>(new Set())

  const toggleConcept = (index: number) => {
    const newExpanded = new Set(expandedConcepts)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedConcepts(newExpanded)
  }

  return (
    <Card className="mt-8 border-0 shadow-xl bg-white/80 backdrop-blur-sm">
      <CardContent className="p-8">
        <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
          <Brain className="w-6 h-6 text-blue-600" />
          Key Concepts Extracted
        </h2>
        <div className="space-y-4">
          {concepts.map((concept, index) => {
            const isExpanded = expandedConcepts.has(index)
            return (
              <div
                key={index}
                className="border border-blue-200 rounded-lg overflow-hidden transition-all duration-200 hover:shadow-md"
              >
                {/* Concept Header - Clickable */}
                <button
                  onClick={() => toggleConcept(index)}
                  className="w-full p-4 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 transition-all duration-200 flex items-center justify-between text-left"
                >
                  <span className="text-blue-800 font-semibold text-lg">{concept.title}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-blue-600 font-medium">{isExpanded ? "Collapse" : "Expand"}</span>
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-blue-600" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-blue-600" />
                    )}
                  </div>
                </button>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="p-6 bg-white border-t border-blue-100 space-y-6">
                    {/* Summary */}
                    <div>
                      <h4 className="text-lg font-semibold text-slate-800 mb-3 flex items-center gap-2">
                        <Brain className="w-5 h-5 text-blue-600" />
                        Summary
                      </h4>
                      <p className="text-slate-700 leading-relaxed">{concept.summary}</p>
                    </div>

                    {/* Citations */}
                    <div>
                      <h4 className="text-lg font-semibold text-slate-800 mb-3 flex items-center gap-2">
                        <Quote className="w-5 h-5 text-green-600" />
                        Citations from Paper
                      </h4>
                      <div className="space-y-3">
                        {concept.citations.map((citation, citationIndex) => (
                          <div key={citationIndex} className="p-4 bg-green-50 border-l-4 border-green-400 rounded-r-lg">
                            <p className="text-green-800 italic leading-relaxed">"{citation}"</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Importance */}
                    <div>
                      <h4 className="text-lg font-semibold text-slate-800 mb-3 flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-amber-600" />
                        Why This Matters
                      </h4>
                      <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-amber-800 leading-relaxed">{concept.importance}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
