"use client"

import { useState } from "react"
import ReactMarkdown from "react-markdown"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { ExternalLink, Github, ChevronDown, ChevronRight, BookOpen, FileText } from "lucide-react"

interface GitHubRepo {
  url: string
  original?: string
  simplified?: string
}

interface GitHubReposPanelProps {
  repos: GitHubRepo[]
  className?: string
}

export function GitHubReposPanel({ repos, className }: GitHubReposPanelProps) {
  const [expandedRepos, setExpandedRepos] = useState<Set<string>>(new Set())

  const toggleRepo = (url: string) => {
    const newExpanded = new Set(expandedRepos)
    if (newExpanded.has(url)) {
      newExpanded.delete(url)
    } else {
      newExpanded.add(url)
    }
    setExpandedRepos(newExpanded)
  }

  const getRepoName = (url: string) => {
    const match = url.match(/github\.com\/([^\/]+\/[^\/]+)/)
    return match ? match[1] : url
  }

  if (repos.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Github className="h-5 w-5" />
            GitHub Repositories
          </CardTitle>
          <CardDescription>
            No GitHub repositories found in this document
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Github className="h-5 w-5" />
          GitHub Repositories
        </CardTitle>
        <CardDescription>
          {repos.length} repository{repos.length !== 1 ? 'ies' : 'y'} referenced in this document
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {repos.map((repo, index) => (
          <div key={repo.url} className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Github className="h-4 w-4" />
                <span className="font-medium text-sm">{getRepoName(repo.url)}</span>
                <Badge variant="outline" className="text-xs">
                  #{index + 1}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  asChild
                >
                  <a
                    href={repo.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1"
                  >
                    <ExternalLink className="h-3 w-3" />
                    View
                  </a>
                </Button>
                {(repo.simplified || repo.original) && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleRepo(repo.url)}
                    className="flex items-center gap-1"
                  >
                    {expandedRepos.has(repo.url) ? (
                      <ChevronDown className="h-3 w-3" />
                    ) : (
                      <ChevronRight className="h-3 w-3" />
                    )}
                    README
                  </Button>
                )}
              </div>
            </div>
            
            {(repo.simplified || repo.original) && (
              <Collapsible open={expandedRepos.has(repo.url)}>
                <CollapsibleContent className="mt-3">
                  {repo.simplified && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                        <BookOpen className="h-3 w-3" />
                        Simplified README
                      </div>
                      <div className="prose prose-sm max-w-none p-4 bg-muted/50 rounded border prose-headings:text-foreground prose-p:text-muted-foreground prose-strong:text-foreground prose-code:bg-background prose-code:text-foreground prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-background prose-pre:border prose-ul:text-muted-foreground prose-ol:text-muted-foreground prose-li:text-muted-foreground prose-blockquote:text-muted-foreground prose-a:text-primary hover:prose-a:text-primary/80">
                        <ReactMarkdown>{repo.simplified}</ReactMarkdown>
                      </div>
                      
                      {repo.original && (
                        <Collapsible>
                          <CollapsibleTrigger asChild>
                            <Button variant="ghost" size="sm" className="text-xs">
                              <FileText className="h-3 w-3 mr-1" />
                              Show Original README
                            </Button>
                          </CollapsibleTrigger>
                          <CollapsibleContent className="mt-2">
                            <div className="prose prose-sm max-w-none p-3 bg-background rounded border text-xs">
                              <div className="whitespace-pre-wrap font-mono">
                                {repo.original.slice(0, 1000)}
                                {repo.original.length > 1000 && "..."}
                              </div>
                            </div>
                          </CollapsibleContent>
                        </Collapsible>
                      )}
                    </div>
                  )}
                  
                  {!repo.simplified && repo.original && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                        <FileText className="h-3 w-3" />
                        Original README
                      </div>
                      <div className="prose prose-sm max-w-none p-3 bg-background rounded border text-xs">
                        <div className="whitespace-pre-wrap font-mono">
                          {repo.original.slice(0, 1000)}
                          {repo.original.length > 1000 && "..."}
                        </div>
                      </div>
                    </div>
                  )}
                </CollapsibleContent>
              </Collapsible>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  )
}