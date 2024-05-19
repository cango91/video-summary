import threading
import queue
import logging


logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.current_task = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.processing = False
        self.runner_thread = threading.Thread(target=self._task_runner)
        self.runner_thread.start()
        self.on_status_change = self._on_status_change
    
    def _on_status_change(self):
        if self.current_task:
            if self.current_task.status == "Complete":
                if self.task_queue.empty():
                    logger.info("All tasks complete. Stopping processing.")
                    self.stop_processing()

    def _task_runner(self):
        while True:
            self.stop_event.wait()  # Wait until processing is allowed
            with self.lock:
                if self.task_queue.empty():
                    self.processing = False
                    continue
                self.current_task = self.task_queue.get()
            if self.current_task is None:  # Sentinel to stop the thread
                break
            self.stop_event.clear()
            try:
                logger.info(f"Starting task {self.current_task.video_id}")
                self.current_task.run(self.stop_event)
            except Exception as e:
                logger.error(f"Error while processing task {self.current_task.video_id}: {str(e)}")
                self.current_task.set_status(f"Error: {str(e)}")
            with self.lock:
                self.current_task = None
            if self.on_status_change:
                self.on_status_change()

    def remove_task(self, video_id):
        with self.lock:
            queue_list = list(self.task_queue.queue)
            self.task_queue = queue.Queue()
            for task in queue_list:
                if task.video_id != video_id:
                    self.task_queue.put(task)
        if self.on_status_change:
            self.on_status_change()

    def add_task(self, task):
        self.task_queue.put(task)
        if self.processing:
            self.stop_event.set()
        if self.on_status_change:
            self.on_status_change()

    def start_processing(self):
        self.processing = True
        self.stop_event.set()

    def stop_processing(self):
        self.processing = False
        self.stop_event.clear()

    def stop_current_task(self):
        with self.lock:
            if self.current_task is not None:
                self.stop_event.set()
                self.current_task = None
                if self.on_status_change:
                    self.on_status_change()

    def stop(self):
        self.task_queue.put(None)
        self.runner_thread.join()

    def get_table(self):
        with self.lock:
            queue_list = list(self.task_queue.queue)
        return [{"Video ID": task.video_id, "Status": task.status, "Title": task.title , "Language": task.language} for task in queue_list]
