import PyPDF2
import requests
import json
import re
import base64
import os
from typing import List, Optional, Dict
from .config_gen import client

class GitHubExtractor:
    def __init__(self, github_token: str = None):
        """
        Initialize the extractor with optional GitHub token
        
        Args:
            github_token: Your GitHub personal access token (optional, but recommended)
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        
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
        """
        prompt = f"""
        Please analyze the following text and extract any GitHub repository URLs or links. 
        Return only the GitHub URLs, one per line, with no additional text or formatting.
        If no GitHub links are found, return "No GitHub links found".
        
        Text to analyze:
        {text[:4000]}  # Limit text to avoid token limits
        """
        
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = message.content[0].text.strip()
            
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
            
        except Exception as e:
            raise Exception(f"Claude API request failed: {str(e)}")
    
    def parse_github_url(self, github_url: str) -> Dict[str, str]:
        """
        Parse a GitHub URL to extract owner and repository name
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
            
            return None
            
        except Exception as e:
            print(f"Error fetching README from {github_url}: {str(e)}")
            return None
    
    def fetch_all_readmes(self, github_links: List[str]) -> Dict[str, str]:
        """
        Fetch README files from multiple GitHub repositories
        """
        readmes = {}
        
        for link in github_links:
            readme_content = self.fetch_readme(link)
            
            if readme_content:
                readmes[link] = readme_content
        
        return readmes
    
    def simplify_readme_with_claude(self, readme_content: str, github_url: str) -> str:
        """
        Use Claude API to simplify and make README content more digestible
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
        
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            simplified_content = message.content[0].text.strip()
            return simplified_content
            
        except Exception as e:
            raise Exception(f"Claude API request failed while simplifying README: {str(e)}")
    
    def simplify_all_readmes(self, readmes: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """
        Simplify multiple README files using Claude API
        """
        simplified_readmes = {}
        
        for github_url, readme_content in readmes.items():
            try:
                simplified_content = self.simplify_readme_with_claude(readme_content, github_url)
                simplified_readmes[github_url] = {
                    'original': readme_content,
                    'simplified': simplified_content
                }
                
            except Exception as e:
                # Keep original if simplification fails
                simplified_readmes[github_url] = {
                    'original': readme_content,
                    'simplified': f"Error simplifying README: {str(e)}"
                }
        
        return simplified_readmes
    
    def process_pdf(self, pdf_path: str, fetch_readmes: bool = True, simplify_readmes: bool = True) -> Dict[str, any]:
        """
        Main method to process PDF and extract GitHub links with optional README fetching and simplification
        """
        text = self.extract_text_from_pdf(pdf_path)
        github_links = self.find_github_links_with_claude(text)
        
        result = {
            'github_links': github_links,
            'readmes': {},
            'simplified_readmes': {}
        }
        
        if fetch_readmes and github_links:
            result['readmes'] = self.fetch_all_readmes(github_links)
            
            if simplify_readmes and result['readmes']:
                result['simplified_readmes'] = self.simplify_all_readmes(result['readmes'])
        
        return result