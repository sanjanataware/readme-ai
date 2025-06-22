# README.ai (read me pls)

**To the abstract and beyond**

## Inspiration
*Scientists spend 23% of their total work time reading research papers*

While this is an important part of scientific training, we believe that oftentimes there is a comprehension barrier in academic research papers that are not generally written to explain something to a novice. 
We are a group of student researchers who understand the feeling of being unable to make it past the abstract when trying to understand a complex paper. 
We wanted to change that, making research more accessible and providing different avenues of understanding. This is where the idea for README.ai came from. 


## What it does
*Watch, understand, implement - research made accessible*

README.ai takes in a research paper and…

1. Create a clean tailored explainer video with a voice-over (akin to 3Blue1Brown or Khan Academy Videos) with targeted and accurate animations grounded in the research paper (minimizing video hallucinations)

2. Highlights key concepts of the paper with text citations on a web interface

3. Generate a quiz for users to test their understanding of the concepts from the paper

4. Hosts a library of your analyzed papers and educational videos to reference past materials

## How we built it
1. We started by testing the video with Manim and Google Veo with PDF and seeing how it makes a video using Claude API
2. Then we built a GitHub readme extractor using the Claude and GitHub API, then integrated Claude API to make the readme easier to understand
3. We worked on the Front end where it can take in pdf and generate the quiz to check for understanding along with returning key concepts
4. Then we weaved in the LMNT API for voice with a script that we generated from the paper to go along with video animation
5. We then integrated the Audio with the video and then connected the backend with the frontend, and created a folder to store the videos.

## Challenges we ran into
We had to figure out how to sync the video and audio generation and linking (one or the other was working but not both) We solved this by testing out different libraries to find the most optimal pipeline configuration. Also, we ran into difficulties integrating parallel API calls, so we ended up testing out different integrations to minimize latency. 

## Accomplishments that we're proud of
1. Creating a robust platform that can handle multiple research papers
2. Designing our video generation pipeline that is tailored to scientific papers, prioritizing meaningful animations and narration to break down complex topics by prioritizing specific video creation tools (not relying solely on video creation models) 
3. Creating a fully functional web platform that is easy to use and user-centric

## What we learned
1. How to use the Claude API to generate summaries, code, and quiz questions.
2. How to use Claude Code for quick scaffolding and code development.
3. How to use Veo for dynamic video generation.
4. How to use Manim code to generate animations.
5. How to deploy our application with Vercel.

## What's next for README.AI
1. Integrate automatically generated interactive demos within the web application to enable users to understand the paper alongside the video explanation better.
2. Create a chatbot that the user can query during the video and at the various sections of the web application to ask clarifying questions regarding the research paper.

