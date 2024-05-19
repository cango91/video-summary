import json
import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
import gradio as gr
import ollama
from utils import get_video_id, get_video_info
from manager import TaskManager
from task import SummarizationTask
from utils import load_config

NO_VIDEOS_ID = "__<NO_VIDEOS>__"

whisper_cfg = load_config("whisper.json")

def get_local_models():
    models = ollama.list()
    return [model["name"] for model in models["models"]]

task_manager = TaskManager()

def refresh_table():
    table_data = task_manager.get_table()
    table_list = [[task["Video ID"], task["Status"], task["Title"], task["Language"]] for task in table_data] + ([[task_manager.current_task.video_id, task_manager.current_task.status, task_manager.current_task.title, task_manager.current_task.language]] if task_manager.current_task else [])
    return table_list

#task_manager.on_status_change = refresh_table

def start_stop_processing():
    if task_manager.processing:
        if task_manager.current_task:
            task_manager.stop_current_task()
        task_manager.stop_processing()
        return "Start"
    else:
        task_manager.start_processing()
        return "Stop"

def add_task(video_id, abstract, model_id, language, sum_model_id, chunk_size, overlap):
    video_id = get_video_id(video_id)
    video_title = get_video_info(video_id)
    task_manager.add_task(SummarizationTask(video_id, video_title, language, model_id, sum_model_id, chunk_size, overlap, abstract, task_manager.on_status_change))
    choices = [task["Video ID"] for task in task_manager.get_table()]
    return "", refresh_table(), gr.Dropdown(label="Remove from queue", choices=choices, interactive=True, value=choices[0] if choices else "")

def get_total_tasks():
    return f"**Total Tasks:** {len(task_manager.get_table()) + (1 if task_manager.current_task else 0)}"

def get_status():
    if not task_manager.current_task:
        return "**Status:** Idle"
    return f"**Status:** Processing {task_manager.current_task.video_id}"

def remove_task(video_id):
    task_manager.remove_task(video_id)
    choices = [task["Video ID"] for task in task_manager.get_table()]
    return gr.Dropdown(label="Remove from queue", choices=choices, interactive=True, value=choices[0] if choices else ""), refresh_table()

def get_button_text():
    return "Stop" if task_manager.processing else "Start"

def get_items():
    if os.path.exists("map.json"):
        with open("map.json", "r") as f:
            video_map = json.load(f)

            items = [{"title": item["title"], "video_id": video_id, "has_abstract": item["abstract"]} for video_id, item in video_map.items()]
            items.reverse()
            return items

    else:
        return [{"title": "No videos found", "video_id": NO_VIDEOS_ID, "has_abstract": False}]


def get_summaries(item):
    if item == NO_VIDEOS_ID:
        return "", ""
    video_id = item
    summary, abstract = "", ""
    try:
        with open(f"summaries/{video_id}.md", "r") as f:
            summary = f.read()
    except:
        pass
    try:
        with open(f"abstracts/{video_id}.md", "r") as f:
            abstract = f.read()
    except:
        pass
    return summary, abstract

selected_item = NO_VIDEOS_ID

def update_tabs(item):
    global selected_item
    selected_item = item
    summary, abstract = get_summaries(item)
    return gr.Markdown(value=abstract), gr.Markdown(value=summary), gr.update(visible=True)

def get_markdown_abs():
    global selected_item
    _, abstract = get_summaries(selected_item)
    return abstract

def get_markdown_sum():
    global selected_item
    summary, _ = get_summaries(selected_item)
    return summary

def get_html():
    return """
    <div style="height: 100%; overflow-y: scroll;">
        <ul>
            {0}
        </ul>
    </div>  
    """.format("".join([f"<li data-vid='{item['video_id']}' class='summary-list-item' onclick='document.selectItem(\"{item['video_id']}\")'>{item['title']}</li>" for item in get_items()]))

js = """
document.selectItem = (video_id) => {
    const itemInput = document.getElementById("item_input").querySelector("textarea");
    itemInput.value = video_id;
    itemInput.dispatchEvent(new Event("input", { bubbles: true }));
    const tabs = document.getElementById("tabs");
    tabs.style.display = "block";
    const listItems = document.querySelectorAll(".summary-list-item");
    listItems.forEach(item => {
        if (item.dataset.vid === video_id) {
            item.classList.add("selected");
        } else {
            item.classList.remove("selected");
        }
    });
    
}
"""    

with gr.Blocks(js=js) as app:
    with gr.Tabs():
        with gr.TabItem("New Tasks"):
            with gr.Row():
                gr.Markdown("# New Video Summary Task")
            with gr.Row():
                with gr.Column() as new_task:
                    video_id_input = gr.Textbox(label="YouTube Video ID or URL", placeholder="e.g. dQw4w9WgXcQ", min_width=500, interactive=True)
                    abstract = gr.Checkbox(label="Generate Abstract", interactive=True, value=True)
                    model_id = gr.Dropdown(label="Whisper Model ID", choices=whisper_cfg.get("models", ["openai/whisper-large-v3"]), interactive=True, value=whisper_cfg["models"][0], min_width=500)
                    language = gr.Dropdown(label="Language", choices=whisper_cfg.get("languages", ["en"]), interactive=True, value="en")
                    sum_model_id = gr.Dropdown(label="Ollama Model ID", choices=get_local_models(), interactive=True, value=get_local_models()[0], min_width=500)
                    chunk_size = gr.Slider(label="Chunk Size", minimum=3000, maximum=10000, step=100, interactive=True, value=6000)
                    overlap = gr.Slider(label="Overlap", minimum=0, maximum=1000, step=100, interactive=True, value=500)
                with gr.Column():
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown(value=get_total_tasks, every=2)
                        with gr.Column():
                            gr.Markdown(value=get_status, every=2)
                    with gr.Row():
                        add_task_button = gr.Button("Add Task", interactive=True)
                        start_tasks_button = gr.Button(value=get_button_text, interactive=True, every=1)
                        start_tasks_button.click(
                            fn=start_stop_processing,
                            outputs=[start_tasks_button]
                        )
                        clear_queue_button = gr.Button("Clear Queue", interactive=True)
                        with gr.Row():
                            with gr.Column():
                                task_to_remove = gr.Dropdown(label="Remove from queue", choices=[task["Video ID"] for task in task_manager.get_table()], interactive=True)
                            with gr.Column():
                                remove_task_button = gr.Button("Remove Task", interactive=True)
                                
            with gr.Row():
                gr.Markdown("# Task Queue")
            with gr.Row():
                with gr.Column():
                    table = gr.DataFrame(headers=["Video ID", "Status", "Title", "Language"], interactive=False, value=refresh_table, every=1)
            add_task_button.click(
                fn=add_task,
                inputs=[video_id_input, abstract, model_id, language, sum_model_id, chunk_size, overlap],
                outputs=[video_id_input, table, task_to_remove]
            )
            remove_task_button.click(
                fn=remove_task,
                inputs=[task_to_remove],
                outputs=[task_to_remove, table]
            )
        with gr.TabItem("Browse"):
            with gr.Row():
                gr.Markdown("# Browse Summaries")
            with gr.Row():
                with gr.Column(scale=1):
                    gr.HTML(value=get_html, every=1)
                with gr.Column(scale=3):
                    with gr.Tabs(visible=False, elem_id="tabs") as tabs:
                        with gr.TabItem("Short Summary"):
                            short_summary_md = gr.Markdown(elem_id="short_summary_md", value=get_markdown_abs, every=0.5)
                        with gr.TabItem("Detailed Summary"):
                            detailed_summary_md = gr.Markdown(elem_id="detailed_summary_md", value=get_markdown_sum, every=0.5)
            item_input = gr.Textbox(visible=False, elem_id="item_input")
            item_input.change(update_tabs, inputs=item_input, outputs=[short_summary_md, detailed_summary_md, tabs])
    
    app.css = """
    .summary-list-item {
        cursor: pointer;
        padding: 10px;
        border-bottom: 1px solid #eee;
    }
    .summary-list-item:hover {
        background-color: #2f2f2f;
        color: white;
    }
    .selected {
        background-color: #2f2f2f;
        color: white;
    }
    li.summary-list-item {
        list-style-type: none;
    }
"""

app.title = "Video Summarization"

app.launch()

