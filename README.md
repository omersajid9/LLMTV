# LLMTV - AI Music Video Generator

Automatically generate music videos from a text prompt using AI.

## Features

- **Lyrics Generation**: Uses LiteLLM to generate structured lyrics from your prompt
- **Music Creation**: Generates music using Replicate's Minimax Music-1.5 model
- **Transcription**: Timestamps lyrics using Whisper for precise video sync
- **Video Generation**: Creates 8-second video clips using Google VEO3 for each segment
- **Video Stitching**: Combines all clips with the full audio track into a final music video

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- **OPENAI_API_KEY**, **ANTHROPIC_API_KEY**, or **GEMINI_API_KEY**: For lyrics generation (LiteLLM)
- **REPLICATE_API_TOKEN**: For music generation and transcription
- **GOOGLE_API_KEY**: For VEO3 video generation

### 3. Create Output Directories

The app will automatically create these directories if they don't exist:
- `downloads/` - Final output videos and songs
- `videos/` - Temporary video segments
- `temp/` - Temporary files

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

Then:
1. Enter your video concept/prompt (e.g., "A song about cats taking over the world")
2. (Optional) Add music style/genre description
3. Click "Generate Music Video"
4. Wait for the AI to work its magic (this can take several minutes)
5. Download your completed music video!

## Architecture

The app follows a multi-stage pipeline:

1. **Lyrics Generation** (`utils/llm_handler.py`) - LLM creates structured lyrics
2. **Music Generation** (`utils/music_generator.py`) - Replicate creates the song
3. **Transcription** (`utils/transcriber.py`) - Whisper timestamps the lyrics
4. **Video Generation** (`utils/video_generator.py`) - VEO3 creates 8-second clips
5. **Video Stitching** (`utils/video_stitcher.py`) - MoviePy combines everything

## Notes

- Video generation can take 5-10 minutes per segment
- For a 30-second song, expect ~4 video segments (about 20-40 minutes total)
- Make sure you have sufficient API credits for all services
- Videos are exactly 8 seconds each from VEO3, trimmed as needed to match song length

## Troubleshooting

- **API Key Errors**: Double-check your `.env` file has the correct keys
- **Out of Memory**: Video stitching requires sufficient RAM, especially for longer videos
- **Timeout Errors**: VEO3 generation can be slow, be patient during the process

## License

MIT

