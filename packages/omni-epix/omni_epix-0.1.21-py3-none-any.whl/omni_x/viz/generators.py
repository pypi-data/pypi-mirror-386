import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from omni_x.core import Task, Archive, RunPaths


def render_task_page(
    task: Task,
    parent_tasks: dict[int, Task],
    all_tasks: list[Task],
    run_dir: Path,
    paths: RunPaths,
    viz_dir: Path,
    llm_logs: dict[str, dict] | None = None,
) -> None:
    """Render a single task detail page."""
    env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))
    template = env.get_template("task.html")

    videos = []
    for video_dir_template, source_label in [
        (paths.eval_videos_dir, "Eval"),
        (paths.training_videos_dir, "Training"),
    ]:
        task_video_dir = run_dir / video_dir_template.format(task_id=task.id)
        if task_video_dir.exists():
            for video_file in sorted(task_video_dir.glob("*.mp4")):
                videos.append({
                    "name": video_file.name,
                    "path": f"videos/{task.id}/{video_file.name}",
                    "source": source_label
                })

    lineage_svg_path = None
    lineage_file = viz_dir / "assets" / "plots" / f"lineage_{task.id}.svg"
    if lineage_file.exists():
        lineage_svg_path = f"assets/plots/lineage_{task.id}.svg"

    # Sort tasks for sidebar: archived by index, intermixed with discarded by created_at, then wip
    archived = [t for t in all_tasks if t.archive_idx is not None]
    discarded = [t for t in all_tasks if t.archive_idx is None and t.done and t.success is None]
    wip = [t for t in all_tasks if not t.done]

    archived.sort(key=lambda t: t.archive_idx)
    discarded.sort(key=lambda t: t.created_at)

    # Intermix archived and discarded tasks chronologically
    sidebar_tasks = []
    discarded_idx = 0

    for archived_task in archived:
        # Insert all discarded tasks created before this archived task
        while discarded_idx < len(discarded) and discarded[discarded_idx].created_at < archived_task.created_at:
            sidebar_tasks.append(discarded[discarded_idx])
            discarded_idx += 1
        sidebar_tasks.append(archived_task)

    # Append any remaining discarded tasks
    sidebar_tasks.extend(discarded[discarded_idx:])

    # Append WIP tasks at the end
    sidebar_tasks.extend(wip)

    html = template.render(
        task=task,
        parent_tasks=parent_tasks,
        all_tasks=sidebar_tasks,
        task_json=json.dumps(task.to_dict(), indent=2, default=str),
        lineage_svg_path=lineage_svg_path,
        videos=videos,
        llm_logs=llm_logs or {},
    )

    task_file = viz_dir / "tasks" / f"{task.id}.html"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    task_file.write_text(html, encoding="utf-8")


def render_dashboard(
    archive: Archive,
    run_name: str,
    run_dir: Path,
    viz_dir: Path,
    plots: dict[str, str] | None = None,
) -> None:
    """Render the main dashboard index page."""
    env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))
    template = env.get_template("index.html")

    all_tasks = list(archive.get_archived()) + list(archive.get_discarded()) + list(archive.get_wip())

    def get_status(task: Task) -> str:
        if task.archive_idx is not None:
            return "archived"
        elif task.done and task.success is None:
            return "discarded"
        else:
            return "wip"

    tasks_for_json = [
        {
            "id": t.id,
            "status": get_status(t),
            "success": t.success,
            "parents": t.parents or [],
            "description": t.description[:200] if t.description else None,
        }
        for t in all_tasks
    ]

    archived = list(archive.get_archived())
    discarded = list(archive.get_discarded())
    wip = list(archive.get_wip())

    evaluated = [t for t in archived if t.success is not None]
    successful = [t for t in evaluated if t.success]

    stats = {
        "total": len(all_tasks),
        "archived": len(archived),
        "discarded": len(discarded),
        "wip": len(wip),
        "evaluated": len(evaluated),
        "successful": len(successful),
        "success_rate": len(successful) / len(evaluated) if evaluated else None,
    }

    html = template.render(
        run_name=run_name,
        tasks_for_alpine=tasks_for_json,
        stats=stats,
        plots=plots or {},
    )

    index_file = viz_dir / "index.html"
    index_file.write_text(html, encoding="utf-8")


def load_llm_logs(run_dir: Path, paths: RunPaths, task: Task) -> dict[str, dict]:
    """Load LLM reasoning logs for a task."""
    logs = {}
    if not task.metadata.get("llm_calls"):
        return logs

    llm_logs_dir = run_dir / paths.llm_log_dir.format(task_id=task.id)
    if not llm_logs_dir.exists():
        return logs

    for call in task.metadata["llm_calls"]:
        log_file = llm_logs_dir / call["log_file"]
        if log_file.exists():
            try:
                data = json.loads(log_file.read_text())
                reasoning = ""
                if "completion" in data and "choices" in data["completion"]:
                    for choice in data["completion"]["choices"]:
                        if "message" in choice and "reasoning" in choice["message"]:
                            reasoning = choice["message"]["reasoning"]
                            break
                logs[call["log_file"]] = {"reasoning": reasoning}
            except Exception:
                pass

    return logs
