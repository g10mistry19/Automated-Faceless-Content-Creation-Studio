# Automated-Faceless-Content-Creation-Studio
An automated content creation studio powered by a multi-agent system that transforms fascinating, evergreen ideas into ready-to-publish, subtitled short videos using AI.

This project is a fully automated content creation pipeline that uses a multi-agent system to produce engaging, short-form "faceless" videos. The system is designed as a "Curiosity Engine," moving beyond fleeting trends to discover and create content on fascinating, evergreen topics that spark wonder and curiosity.

From finding a unique idea to rendering the final, subtitled video, the entire workflow is handled by a team of specialized AI agents.

## Key Features ✨
Curiosity Engine: Instead of tracking trends, the primary agent performs "deep dives" into niche online communities to find high-quality, evergreen content ideas from a knowledge base of over 50 categories.

Semantic Memory: The system uses a ChromaDB vector database to remember and understand the topics it has already covered. It actively rejects new ideas that are semantically similar to previous videos, ensuring all content is unique.

End-to-End Automation: A digital assembly line of AI agents handles everything:

## Topic Discovery

1.Scriptwriting & Visual Prompting

2.Voiceover Generation (TTS)

3.Image Sourcing

4.Video Assembly, Merging & Subtitling

5.AI-Powered Scripting: Uses Google's Gemini models to write captivating, curiosity-driven scripts in a consistent style, optimized for short-form video.

## How It Works ⚙️
The studio operates on a multi-agent architecture orchestrated by a framework like LangGraph. Each agent performs a specific task and passes its work to the next agent in the production line:

1.The Curiosity Engine Agent finds a unique, evergreen topic.

2.The Scriptwriter Agent creates a compelling narrative and visual prompts.

3.The Voice Director Agent generates the audio narration.

4.The Media Sourcer Agent downloads the required visuals.

5.The Audio-Visual Editor Agent assembles all assets into a final, subtitled .mp4 video.

## Technology Stack 🛠️
Orchestration: LangChain / LangGraph

AI & Content: Google Gemini, PRAW (Reddit API)

Semantic Memory: ChromaDB

Media Production: MoviePy, Google Text-to-Speech (gTTS), Google Custom Search API
