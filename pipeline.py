import yt_dlp
import os
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from logging import getLogger
import ollama

logger = getLogger(__name__)

def download(video_id):
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'paths': {'home': 'audio/'},
        'outtmpl': {'default': '%(id)s.%(ext)s'},
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download([video_url])
        if error_code != 0:
            raise Exception('Failed to download video')

    return f'audio/{video_id}.m4a'


def transcribe(video_id, model_id="openai/whisper-large-v3", language="en"):
    if os.path.exists(f"transcripts/{video_id}.txt"):
        with open(f"transcripts/{video_id}.txt", "r") as f:
            logger.info("Loading existing transcript...")
            transcript = f.read()
    else:
        filepath = f'audio/{video_id}.m4a'
        device = "mps"
        torch_dtype = torch.float32

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=torch_dtype, use_safetensors=True
        )
        model.to(device)

        processor = AutoProcessor.from_pretrained(model_id, language=language)

        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=16,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device,
        )
        logger.info("Transcribing audio...")
        transcript = pipe(filepath)["text"]
        with open(f"transcripts/{video_id}.txt", "w") as f:
            f.write(transcript)
    return transcript


# Generator function to split the transcript into chunks with overlapping content
def chunker(transcript: str, chunk_size: int = 6000, overlap: int = 500):
    # Create a rolling window of ~3000 characters, find the last period, and truncate the transcript there. Repeat until the entire transcript is processed.
    while transcript:
        yield transcript[:chunk_size]
        transcript = transcript[chunk_size - overlap:]

def summarize(transcript, video_id, model="llama3:70b-instruct", chunk_size=6000, overlap=500, abstract=True):
    modelfile=f'''
FROM {model}
SYSTEM """
# ROLE: News Analyst
You are a news analyst. You will read a transcript of a youtube video, and extract stories, news, opinions, events from it like a journalist. You will convert the transcript into a detailed journalistic expression that captures the main points and key ideas of the video, with each news item or topic covered in a separate section.
**BE SURE TO INCLUDE ALL THE TOPICS/NEWS/INFORMATION FROM THE VIDEO IN YOUR SUMMARY.**
**START FROM THE VERY BEGINNING OF THE VIDEO, DO NOT SKIP CONTENT**
**DO NOT INCLUDE YOUR OPINION, ONLY THE FACTS AND INFORMATION FROM THE VIDEO**
**INCLUDE ALL NEWS ITEMS, EVENTS, AND TOPICS DISCUSSED IN THE VIDEO, EVEN IF THEY SOUND GOSSIPY**
**DO NOT INCLUDE ANY INFORMATION THAT IS NOT IN THE VIDEO**
**DO NOT INCLUDE ANY INFORMATION THAT IS NOT IN THE VIDEO**
**DO NOT INCLUDE ANY INFORMATION THAT IS NOT IN THE VIDEO**
# STYLE: Journalistic
Use markdown to express the news items, events, topics, shared opinions, etc.. in a journalistic style.
**USE HEADINGS FOR EACH NEWS ITEM OR TOPIC**
**USE BULLET POINTS FOR DETAILS**
**USE PARAGRAPHS FOR DESCRIPTIONS**
**USE QUOTES FOR DIRECT QUOTES**
**USE ITALICS FOR EMPHASIS**
**USE BOLD FOR IMPORTANT POINTS**
**USE LINKS FOR REFERENCES**
**USE BLOCKQUOTES FOR LONG QUOTES**
"""
'''
    summary = ""
    abstract_txt = ""
    ctx = []
    try:
        ollama.delete(model="llama-summarizer")
    except:
        pass
    ollama.create(model="llama-summarizer", modelfile=modelfile)
    for chunk in chunker(transcript, chunk_size, overlap):
        chat = ollama.generate(
            stream=False, model="llama-summarizer", prompt=chunk, context=ctx
        )
        summary += chat['response']
        ctx = chat['context']
    with open(f"summaries/{video_id}.md", "w") as f:
        f.write(summary)
    if abstract:
        modelfile=f'''
FROM {model}
SYSTEM """
# ROLE: Abstractor
You are an abstractor. You will read a summary of a youtube video, and summarize it. Pay attention to the main points and the key ideas.
**DO NOT INCLUDE YOUR OPINION, ONLY THE FACTS AND INFORMATION FROM THE VIDEO**
**DO NOT OUTPUT ANYTHING ELSE**
# FORMAT: Markdown
"""
'''
        try:
            ollama.delete(model="llama-abstractor")
        except:
            pass
        ollama.create(model="llama-abstractor", modelfile=modelfile)
        chat = ollama.generate(
            stream=False, model="llama-abstractor", prompt=summary
        )
        abstract_txt = chat['response']
        with open(f"abstracts/{video_id}.md", "w") as f:
            f.write(abstract_txt)
    return summary, abstract_txt
