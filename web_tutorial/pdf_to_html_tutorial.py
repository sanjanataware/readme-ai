#!/usr/bin/env python3
"""
Research Paper to Interactive HTML Generator
Converts PDF research papers into interactive HTML demos using Claude API
"""

import os
import sys
from pathlib import Path
import pdfplumber
from anthropic import Anthropic
import dotenv

dotenv.load_dotenv()
API_KEY = os.getenv("ANTHROPIC_API_KEY", "your_api_key_here")

MAX_PAPER_LEN = 15000
MAX_TOKENS = 10000

prompt_template = """
I need you to create an interactive HTML page that breaks down this research paper step by step. 

Paper content:
{}

Please create a comprehensive, interactive HTML page that includes:

1. **Clean, minimalistic design** with a white background and mostly black text with tasteful accent colors
2. **Step-by-step breakdown** of the paper's key concepts
3. **Interactive demonstrations** where possible (visualizations, simulations, etc.)
4. **Key insights highlighted** in special boxes
5. **Architecture diagrams** if the paper describes models/systems
6. **Results and metrics** presented clearly
7. **Technical innovations** explained with examples

Requirements:
- Use the same clean, minimal style as the U-Net page
- Make it educational and engaging
- Include interactive elements where they make sense
- Break down complex concepts into digestible sections
- Use modern web technologies (HTML5, CSS3, vanilla JavaScript)
- Make it responsive for mobile devices
- Include hover effects and smooth animations
- Focus on visual learning and interactivity

The page should help someone understand the paper's core contributions, methodology, and significance through interactive exploration rather than just reading dense text.

In addition, the page should have an element user's can interact with. And all graphics should be Scalable Vector Graphics.

Please create a complete, self-contained HTML file that I can save and open in a browser.
"""

def extract_pdf_text(pdf_path: str) -> str:
	text = ""
	with pdfplumber.open(pdf_path) as pdf:
		for page in pdf.pages:
			text += page.extract_text()
	return text

def query_claude(prompt: str) -> str:
	client = Anthropic(api_key=API_KEY)
	message = client.messages.create(
		model="claude-sonnet-4-20250514",
		max_tokens=MAX_TOKENS,
		temperature=0.1,
		messages=[{
			"role": "user",
			"content": prompt
		}]
	)
	return message.content[0].text

def extract_html_content(raw_response: str) -> str:
	html_start_markers = ['```html', '<!DOCTYPE html', '<html']
	html_end_markers = ['```', '</html>']

	html_content = raw_response

	# Try to extract HTML from code blocks
	for start_marker in html_start_markers:
		if start_marker in raw_response:
			start_idx = raw_response.find(start_marker)
			if start_marker == '```html':
				start_idx += len(start_marker)
			
			# Find the end
			remaining = raw_response[start_idx:]
			for end_marker in html_end_markers:
				if end_marker in remaining:
					end_idx = remaining.find(end_marker)
					if end_marker == '</html>':
						end_idx += len(end_marker)
					html_content = remaining[:end_idx]
					break
			break

	return html_content.strip()	

def generate_html_content(paper_content: str) -> str:
	response = query_claude(prompt_template.format(paper_content))
	return extract_html_content(response)

def save_html_file(html_content, output_path):
	with open(output_path, 'w', encoding='utf-8') as f:
		f.write(html_content)	

def pdf_to_html_tutorial(pdf_path, output_path):
	print("extracting pdf text...")
	pdf_text = extract_pdf_text(pdf_path)
	print("generating html content...")
	html_content = generate_html_content(pdf_text)
	print("saving html file")
	save_html_file(html_content, output_path)

if __name__ == "__main__":
	pdf_to_html_tutorial('./unet.pdf', 'unet.html')