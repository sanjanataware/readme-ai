import { config, GitHubExtractionResult, GitHubRepo } from "./config"

export async function extractGitHubRepos(
  file: File,
  options: {
    fetchReadmes?: boolean
    simplifyReadmes?: boolean
  } = {}
): Promise<GitHubRepo[]> {
  const {
    fetchReadmes = true,
    simplifyReadmes = true
  } = options

  const formData = new FormData()
  formData.append("file", file)
  formData.append("fetch_readmes", fetchReadmes.toString())
  formData.append("simplify_readmes", simplifyReadmes.toString())

  try {
    const response = await fetch(`${config.VIDEO_API_URL}/extract-github-upload`, {
      method: "POST",
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    const result: GitHubExtractionResult = await response.json()
    
    // Transform the result into the format expected by the component
    const repos: GitHubRepo[] = result.github_links.map(url => ({
      url,
      original: result.readmes[url],
      simplified: result.simplified_readmes[url]?.simplified
    }))

    return repos

  } catch (error) {
    console.error("GitHub extraction failed:", error)
    throw error instanceof Error ? error : new Error("Unknown error occurred")
  }
}

export async function extractGitHubReposFromPath(
  pdfPath: string,
  options: {
    fetchReadmes?: boolean
    simplifyReadmes?: boolean
  } = {}
): Promise<GitHubRepo[]> {
  const {
    fetchReadmes = true,
    simplifyReadmes = true
  } = options

  try {
    const response = await fetch(`${config.VIDEO_API_URL}/extract-github`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        pdf_path: pdfPath,
        fetch_readmes: fetchReadmes,
        simplify_readmes: simplifyReadmes
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    const result: GitHubExtractionResult = await response.json()
    
    // Transform the result into the format expected by the component
    const repos: GitHubRepo[] = result.github_links.map(url => ({
      url,
      original: result.readmes[url],
      simplified: result.simplified_readmes[url]?.simplified
    }))

    return repos

  } catch (error) {
    console.error("GitHub extraction failed:", error)
    throw error instanceof Error ? error : new Error("Unknown error occurred")
  }
}