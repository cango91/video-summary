# YouTube Summarizer Project (Apple Silicon)

This is a hobby project that aims to streamline the ingestion of YouTube content.

This app is meant to be run locally on an Apple Silicon device (tested with M3 Max with 128GB memory) and uses only local resources.

The app works as follows:

1. Download the YouTube video as best quality audio.
2. Transcribe the audio using OAI's open-source Whisper models.
3. Use a local LLM to summarize the transcript.

## Getting Started

### Installing System Dependencies

Install `ffmpeg` and `ollama`. Installing virtualenv is recommended.

```sh
brew install ffmpeg ollama virtualenv
```

### Getting Ollama Ready
Once installed, start ollama by running 

```sh
ollama serve
```

Then, download an LLM of your choosing. This LLM will be used during summarization

```sh
ollama pull llama3:70b-instruct
```

Wait for the download to finish.

### Installing

1. Clone this repository

```sh
git clone https://github.com/cango91/video-summary.git
```

2. Create and activate new virtualenvironment

```sh
cd video-summary
virtualenv .venv -p 3.11
source .venv/bin/activate
```

3. Install requirements

`pip install -r requirements.txt`

4. Launch Web UI

`python app.py`

Navigate to `127.0.0.1:7860` in your browser.

## Usage
![Screenshot of new tasks tab](https://i.imgur.com/gQ8ukIl.png)
<subtitle>New Tasks tab.</subtitle>

When you load the app, you will reach the new tasks tab. Here, you can create a queue of videos to be summarized. Simply paste in their links, choose your models, language and chunking size, and click Add Task.

Tasks will not automatically start. You should press `Start` manually to start processing the queue.

**Note:** If UI appears broken, navigate to Browse tab and back, or reload the page.

### Customizing your task
+ **Video ID or URL:** Paste in the video url from youtube. Make sure to not include any query params after `v={video_id}` (such as timestamps)
+ **Generate Abstract:** By my preference, the initial summary will be more of a detailed description of the video. Checking this option will allow creating a second, shorter summary.
+ **Whisper Model ID:** This is the whisper model that will be used from the `transformers` library to transcribe the video's audio.
  + This list is populated from `whisper.json`
  + You can add additional models (such as distill-whisper, etc) by extending the array of `models` in `whisper.json`
  + Restart the app (from terminal) for changes to be reflected.
+ **Language:** The language of the video.
  + This list is populated form `whisper.json`
  + You can add additional languages by extending the `languages` array in `whisper.json`
  + Restart the app (from terminal) for changes to be reflected.
+ **Ollama Model:** This is the local LLM to use for summarizing.
  + This list is populated by the outputs of `ollama list`. If you don't see a model you like, make sure you pulled it first using `ollama pull <model>` and restart the app from the terminal.
+ **Chunk Size & Overlap:** My experiments have showed feeding the whole transcript as an input to LLMs, makes the summary miss the content of the earlier parts of the transcript on long videos. Therefore, the transcript is chunked with this character size with the given overlap, and sequentially used as context when generating the summary.

![Screenshot of Browse Summaries tab](https://i.imgur.com/gd4pDRo.png)
<subtitle>Browse completed summaries</subtitle>

Use the `Browse` tab to easily browse finished summaries.

## Contributing
Contributions are welcome. However, this is a hobby project and may not be actively monitored. Feel free to open issues or submit pull requests.

## License
This project is licensed under the MIT License. Please check the licensing of any AI models you choose to use.

