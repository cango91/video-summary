from pipeline import download, summarize, transcribe
import logging
import json
from time import time as ttime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels of logs
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class SummarizationTask:
    def __init__(self, video_id, title, language="en", model_id="openai/whisper-large-v3", sum_model_id="llama3", chunk_size=6000, overlap=500, abstract=True, on_status_change=None):
        self.video_id = video_id
        self.title = title
        self.language = language
        self.model_id = model_id
        self.sum_model_id = sum_model_id
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.status = "Pending"
        self.transcript = None
        self.summary = None
        self.abstract = None
        self.get_abstract = abstract
        self.on_status_change = on_status_change

    def _download(self, stop_event):
        if stop_event.is_set(): return
        self.set_status("Downloading")
        logger.info(f"Downloading video {self.video_id}")
        start = ttime()
        download(self.video_id)
        logger.info(f"Downloaded video {self.video_id} in {ttime() - start:.2f} seconds")

    def _transcribe(self, stop_event):
        if stop_event.is_set(): return
        self.set_status("Transcribing")
        logger.info(f"Transcribing video {self.video_id}")
        start = ttime()
        self.transcript = transcribe(self.video_id, self.model_id, self.language)
        logger.info(f"Transcribed video {self.video_id} in {ttime() - start:.2f} seconds")

    def _summarize(self, stop_event):
        if stop_event.is_set(): return
        self.set_status("Summarizing")
        logger.info(f"Summarizing video {self.video_id}")
        start = ttime()
        self.summary, self.abstract = summarize(self.transcript, self.video_id, self.sum_model_id, self.chunk_size, self.overlap, self.get_abstract)
        logger.info(f"Summarized video {self.video_id} in {ttime() - start:.2f} seconds")


    def _add_mapping(self, stop_event):
        self.set_status("Adding Mapping")
        video_map = {}
        try:
            with open("map.json", "r") as f:
                video_map = json.load(f)
        except:
            pass
        video_map[self.video_id] = {
            "title": self.title,
            "abstract": len(self.abstract) > 0
        }
        with open("map.json", "w+") as f:
            json.dump(video_map, f)
        self.set_status("Complete")
        logger.info(f"Added mapping for video {self.video_id}")

    def set_status(self, status):
        self.status = status
        logger.info(f"Task {self.video_id} status: {self.status}")
        if self.on_status_change:
            self.on_status_change()

    def run(self, stop_event):
        try:
            self._download(stop_event)
            if stop_event.is_set(): return
            self._transcribe(stop_event)
            if stop_event.is_set(): return
            self._summarize(stop_event)
            self._add_mapping(stop_event)
        except Exception as e:
            logger.error(f"Error while running task {self.video_id}: {str(e)}")
            self.set_status(f"Error: {str(e)}")
