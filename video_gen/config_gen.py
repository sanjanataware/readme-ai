import anthropic
import os
import dotenv
import base64
import httpx
# Load environment variables from .env file
dotenv.load_dotenv()


API_KEY = os.getenv("ANTHROPIC_API_KEY", "your_api_key_here")

client = anthropic.Anthropic(
    api_key=API_KEY
)

prompt = """Imagine you are 3 Blue 1 Brown himself, an incredible teacher and instructor.
from this paper generate a json object for an educational video that is a list of clips, a clip is either of type: manim which has code to generate a clip with manim or of type: veo with a prompt to googles veo api which will generate a clip up to 8 seconds, this prompt is simply a description of what you would like to see in the clip, for all clips generate a voice over piece.
come up with good explanation, interesting analogies and really good but deep explanations, NEVER EVER dumb this down, keep it technical and treat your audience like grownups, think this through, you are an artist and teaching is your craft, treat it with the respect it deserves.
use veo quite sparingly, sometimes it generates kinda janky not clean videos. write code that is clean and well formatted, don't write broken code, be careful about not putting text or other objects ontop of other objects.
simply return the json object of schema, do not return any other text, don't even wrap it in a code block, just return the json object.
{
    "clips": [
        {
            "type: "manim" | "veo",
            "code": "string" | null,
            "prompt": "string" | null,
            "voice_over": "string"
        }
    ]
}
"""

def generate_video_config(pdf, use_base64=False):
    if use_base64:
        # Load PDF from URL and encode as base64
        if pdf.startswith('http'):
            pdf_data = base64.standard_b64encode(httpx.get(pdf).content).decode("utf-8")
        else:
            # Load from local file
            with open(pdf, "rb") as f:
                pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")
        
        document_content = {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": pdf_data
            }
        }
    else:
        # Use URL method
        document_content = {
            "type": "document",
            "source": {
                "type": "url",
                "url": pdf
            }
        }
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=10000,
        messages=[
            {
                "role": "user", 
                "content": [
                    document_content,
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            },
        ]
    )

    return message

if __name__ == "__main__":
    pdf = "./boltz2.pdf"
    response = generate_video_config(pdf, use_base64=True)
    print(response.content[0].text)

    # write to file
    with open("video_config.json", "w") as f:
        f.write(response.content[0].text)
