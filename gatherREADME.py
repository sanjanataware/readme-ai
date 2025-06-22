import PyPDF2
import requests
import json
import re
import base64
from typing import List, Optional, Dict

class PDFGitHubExtractor:
    def __init__(self, claude_api_key: str, github_token: str = None):
        """
        Initialize the extractor with your Claude API key and GitHub token
        
        Args:
            claude_api_key: Your Anthropic API key
            github_token: Your GitHub personal access token (optional, but recommended)
        """
        self.claude_api_key = claude_api_key
        self.github_token = github_token
        self.claude_headers = {
            "Content-Type": "application/json",
            "x-api-key": self.claude_api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # GitHub API headers
        self.github_headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "PDF-GitHub-Extractor"
        }
        if self.github_token:
            self.github_headers["Authorization"] = f"token {self.github_token}"
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as string
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    def find_github_links_with_claude(self, text: str) -> List[str]:
        """
        Use Claude API to find GitHub links in the text
        
        Args:
            text: Text content to analyze
            
        Returns:
            List of GitHub links found
        """
        prompt = f"""
        Please analyze the following text and extract any GitHub repository URLs or links. 
        Return only the GitHub URLs, one per line, with no additional text or formatting.
        If no GitHub links are found, return "No GitHub links found".
        
        Text to analyze:
        {text[:4000]}  # Limit text to avoid token limits
        """
        
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = requests.post("https://api.anthropic.com/v1/messages", headers=self.claude_headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result['content'][0]['text'].strip()
            
            if "No GitHub links found" in content:
                return []
            
            # Extract GitHub URLs from the response
            github_pattern = r'https?://github\.com/[^\s<>"\']*'
            github_links = re.findall(github_pattern, content, re.IGNORECASE)
            
            # Clean up and deduplicate
            clean_links = []
            for link in github_links:
                # Remove trailing punctuation
                link = re.sub(r'[.,;)]*$', '', link)
                if link not in clean_links:
                    clean_links.append(link)
            
            return clean_links
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format: {str(e)}")
    
    def parse_github_url(self, github_url: str) -> Dict[str, str]:
        """
        Parse a GitHub URL to extract owner and repository name
        
        Args:
            github_url: GitHub repository URL
            
        Returns:
            Dictionary with 'owner' and 'repo' keys
        """
        # Remove trailing slashes and .git extension
        url = github_url.rstrip('/').replace('.git', '')
        
        # Extract owner and repo from URL
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, url, re.IGNORECASE)
        
        if not match:
            raise ValueError(f"Invalid GitHub URL format: {github_url}")
        
        return {
            'owner': match.group(1),
            'repo': match.group(2)
        }
    
    def fetch_readme(self, github_url: str) -> Optional[str]:
        """
        Fetch README content from a GitHub repository
        
        Args:
            github_url: GitHub repository URL
            
        Returns:
            README content as text, or None if not found
        """
        try:
            repo_info = self.parse_github_url(github_url)
            owner = repo_info['owner']
            repo = repo_info['repo']
            
            # Try common README file names
            readme_names = ['README.md', 'README.rst', 'README.txt', 'README', 'readme.md']
            
            for readme_name in readme_names:
                api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{readme_name}"
                
                try:
                    response = requests.get(api_url, headers=self.github_headers)
                    
                    if response.status_code == 200:
                        content_data = response.json()
                        
                        # Decode base64 content
                        if content_data.get('encoding') == 'base64':
                            content = base64.b64decode(content_data['content']).decode('utf-8')
                            return content
                        else:
                            # If not base64, try direct content
                            return content_data.get('content', '')
                            
                except requests.exceptions.RequestException:
                    continue  # Try next README name
            
            print(f"No README found for {github_url}")
            return None
            
        except Exception as e:
            print(f"Error fetching README from {github_url}: {str(e)}")
            return None
    
    def fetch_all_readmes(self, github_links: List[str]) -> Dict[str, str]:
        """
        Fetch README files from multiple GitHub repositories
        
        Args:
            github_links: List of GitHub repository URLs
            
        Returns:
            Dictionary mapping GitHub URLs to their README content
        """
        readmes = {}
        
        for link in github_links:
            print(f"Fetching README from {link}...")
            readme_content = self.fetch_readme(link)
            
            if readme_content:
                readmes[link] = readme_content
                print(f"✓ README fetched successfully")
            else:
                print(f"✗ No README found or error occurred")
        
        return readmes
    
    def simplify_readme_with_claude(self, readme_content: str, github_url: str) -> str:
        """
        Use Claude API to simplify and make README content more digestible
        
        Args:
            readme_content: Raw README text content
            github_url: The GitHub repository URL for context
            
        Returns:
            Simplified and more digestible README content
        """
        prompt = f"""
        Please analyze and simplify the following README file from the GitHub repository: {github_url}

        Make it more digestible by:
        1. Creating a clear, concise summary of what this project does
        2. Highlighting the key features and benefits
        3. Simplifying technical jargon while keeping important details
        4. Organizing information in a logical, easy-to-read format
        5. Extracting the most important installation/usage instructions
        6. Noting any prerequisites or dependencies clearly

        Please structure your response with clear headings and make it accessible to both technical and non-technical readers.

        Original README content:
        {readme_content[:6000]}  # Limit to avoid token limits
        """
        
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = requests.post("https://api.anthropic.com/v1/messages", headers=self.claude_headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            simplified_content = result['content'][0]['text'].strip()
            
            return simplified_content
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed while simplifying README: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format during simplification: {str(e)}")
    
    def simplify_all_readmes(self, readmes: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """
        Simplify multiple README files using Claude API
        
        Args:
            readmes: Dictionary mapping GitHub URLs to their README content
            
        Returns:
            Dictionary mapping GitHub URLs to both original and simplified README content
        """
        simplified_readmes = {}
        
        for github_url, readme_content in readmes.items():
            print(f"Simplifying README from {github_url}...")
            
            try:
                simplified_content = self.simplify_readme_with_claude(readme_content, github_url)
                simplified_readmes[github_url] = {
                    'original': readme_content,
                    'simplified': simplified_content
                }
                print(f"✓ README simplified successfully")
                
            except Exception as e:
                print(f"✗ Error simplifying README: {str(e)}")
                # Keep original if simplification fails
                simplified_readmes[github_url] = {
                    'original': readme_content,
                    'simplified': f"Error simplifying README: {str(e)}"
                }
        
        return simplified_readmes
    
    def process_pdf(self, pdf_path: str, fetch_readmes: bool = True, simplify_readmes: bool = True) -> Dict[str, any]:
        """
        Main method to process PDF and extract GitHub links with optional README fetching and simplification
        
        Args:
            pdf_path: Path to the PDF file
            fetch_readmes: Whether to fetch README files from found repositories
            simplify_readmes: Whether to simplify README content using Claude API
            
        Returns:
            Dictionary containing github_links, readmes, and simplified_readmes (if requested)
        """
        print(f"Extracting text from {pdf_path}...")
        text = self.extract_text_from_pdf(pdf_path)
        
        print("Analyzing text with Claude API...")
        github_links = self.find_github_links_with_claude(text)
        
        result = {
            'github_links': github_links,
            'readmes': {},
            'simplified_readmes': {}
        }
        
        if fetch_readmes and github_links:
            print(f"\nFetching README files from {len(github_links)} repository(ies)...")
            result['readmes'] = self.fetch_all_readmes(github_links)
            
            if simplify_readmes and result['readmes']:
                print(f"\nSimplifying README files using Claude API...")
                result['simplified_readmes'] = self.simplify_all_readmes(result['readmes'])
        
        return result


def main():
    """
    Example usage of the PDF GitHub extractor with README fetching
    """
    # PUT YOUR API KEYS HERE
    CLAUDE_API_KEY = "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"
    GITHUB_TOKEN = "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"  # Optional but recommended for higher rate limits
    
    # Initialize extractor
    extractor = PDFGitHubExtractor(CLAUDE_API_KEY, GITHUB_TOKEN)
    
    # Get PDF path from user
    pdf_path = input("Enter the path to your PDF file: ").strip()
    
    try:
        # Process the PDF, fetch READMEs, and simplify them
        result = extractor.process_pdf(pdf_path, fetch_readmes=True, simplify_readmes=True)
        
        github_links = result['github_links']
        readmes = result['readmes']
        simplified_readmes = result['simplified_readmes']
        
        # Display results
        if github_links:
            print(f"\n{'='*50}")
            print(f"Found {len(github_links)} GitHub link(s):")
            for i, link in enumerate(github_links, 1):
                print(f"{i}. {link}")
            
            if simplified_readmes:
                print(f"\n{'='*50}")
                print("SIMPLIFIED README CONTENT:")
                print(f"{'='*50}")
                
                for link, content_dict in simplified_readmes.items():
                    print(f"\n📁 Simplified README from {link}:")
                    print("-" * 60)
                    print(content_dict['simplified'])
                    print("-" * 60)
                    
                    # Ask if user wants to see original content
                    show_original = input("Show original README? (y/n): ").lower().strip()
                    if show_original == 'y':
                        print("\nOriginal README content:")
                        print(content_dict['original'][:1000] + "..." if len(content_dict['original']) > 1000 else content_dict['original'])
                        print("-" * 60)
            
            elif readmes:
                print(f"\n{'='*50}")
                print("README CONTENT (No simplification performed):")
                print(f"{'='*50}")
                
                for link, content in readmes.items():
                    print(f"\n📁 README from {link}:")
                    print("-" * 60)
                    preview = content[:500] + "..." if len(content) > 500 else content
                    print(preview)
                    print("-" * 60)
            else:
                print("\nNo README files could be fetched.")
        else:
            print("\nNo GitHub links found in the PDF.")
            
    except Exception as e:
        print(f"Error: {str(e)}")


def save_readmes_to_files(simplified_readmes: Dict[str, Dict[str, str]], output_dir: str = "readmes"):
    """
    Helper function to save both original and simplified README contents to separate files
    
    Args:
        simplified_readmes: Dictionary of GitHub URLs to original and simplified README content
        output_dir: Directory to save README files
    """
    import os
    
    if not simplified_readmes:
        print("No README content to save.")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    for i, (url, content_dict) in enumerate(simplified_readmes.items(), 1):
        # Create safe filename from URL
        base_filename = re.sub(r'[^\w\-_.]', '_', url.split('/')[-2:][0] + '_' + url.split('/')[-1])
        
        # Save original README
        original_filepath = os.path.join(output_dir, f"{base_filename}_original.md")
        with open(original_filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Original README from {url}\n\n")
            f.write(content_dict['original'])
        print(f"Saved original README to: {original_filepath}")
        
        # Save simplified README
        simplified_filepath = os.path.join(output_dir, f"{base_filename}_simplified.md")
        with open(simplified_filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Simplified README from {url}\n\n")
            f.write(content_dict['simplified'])
        print(f"Saved simplified README to: {simplified_filepath}")


def save_summary_report(result: Dict[str, any], output_file: str = "pdf_analysis_report.md"):
    """
    Create a comprehensive summary report of the entire analysis
    
    Args:
        result: The complete result dictionary from process_pdf
        output_file: Output filename for the report
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# PDF GitHub Analysis Report\n\n")
        f.write(f"Generated on: {json.dumps(str(requests.get('http://worldtimeapi.org/api/timezone/Etc/UTC').json().get('datetime', 'Unknown')))}\n\n")
        
        # GitHub Links Found
        f.write("## GitHub Repositories Found\n\n")
        if result['github_links']:
            for i, link in enumerate(result['github_links'], 1):
                f.write(f"{i}. [{link}]({link})\n")
        else:
            f.write("No GitHub links found in the PDF.\n")
        
        # Simplified READMEs
        if result['simplified_readmes']:
            f.write("\n## Simplified README Summaries\n\n")
            for link, content_dict in result['simplified_readmes'].items():
                f.write(f"### {link}\n\n")
                f.write(content_dict['simplified'])
                f.write("\n\n---\n\n")
    
    print(f"Summary report saved to: {output_file}")



if __name__ == "__main__":
    main()