import json
import logging
from pathlib import Path
from dataclasses import dataclass

import tyro

from omni_x.components.archive.fs import FsArchive
from omni_x.core import RunPaths
from omni_x.utils.run import load_run_metadata
from omni_x.viz.generators import render_task_page, render_dashboard, load_llm_logs
from omni_x.viz.plots import plot_success_timeline, plot_status_pie, plot_embedding_space
from omni_x.viz.trees import generate_lineage_tree, generate_task_lineage_subtree


logger = logging.getLogger(__name__)


@dataclass
class Args:
    run_dir: Path
    """Path to the run directory to visualize."""
    force: bool = False
    """Regenerate all visualizations even if they exist."""


def render_run(run_dir: Path, force: bool = False) -> None:
    """Generate static HTML visualization for a run."""
    run_dir = Path(run_dir).resolve()
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    viz_dir = run_dir / "viz"
    if viz_dir.exists() and not force:
        logger.info(f"Viz directory already exists: {viz_dir}. Use --force to regenerate.")

    viz_dir.mkdir(parents=True, exist_ok=True)
    (viz_dir / "videos").mkdir(exist_ok=True)

    logger.info(f"Loading archive from {run_dir}")
    archive = FsArchive(run_dir)

    all_tasks = list(archive.get_archived()) + list(archive.get_discarded()) + list(archive.get_wip())
    logger.info(f"Found {len(all_tasks)} tasks ({len(list(archive.get_archived()))} archived)")

    # Load run metadata (paths and config)
    meta = load_run_metadata(run_dir)
    paths = RunPaths(**meta.paths)
    embedding_model = meta.config.get("embedding_model")

    logger.info("Creating symlinks for videos...")
    for video_path_template in [paths.eval_videos_dir, paths.training_videos_dir]:
        # Extract base path (e.g., "videos/eval" from "videos/eval/{task_id}")
        base_path = Path(video_path_template.split("{")[0].rstrip("/"))
        src = run_dir / base_path
        dst = viz_dir / "videos"
        if src.exists():
            for task_video_dir in src.iterdir():
                if task_video_dir.is_dir():
                    task_id = task_video_dir.name
                    link = dst / task_id
                    if not link.exists():
                        try:
                            link.symlink_to(task_video_dir.resolve(), target_is_directory=True)
                        except Exception as e:
                            logger.warning(f"Failed to create symlink for {task_video_dir}: {e}")

    logger.info("Generating plots...")
    plots_dir = viz_dir / "assets" / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    plot_success_timeline(archive, plots_dir / "success_timeline.png")
    plot_status_pie(archive, plots_dir / "status_pie.png")
    plot_embedding_space(archive, embedding_model, plots_dir / "embedding_space.png")
    generate_lineage_tree(archive, plots_dir / "lineage_full.svg")

    plots = {}
    if (plots_dir / "success_timeline.png").exists():
        plots["success_timeline"] = "assets/plots/success_timeline.png"
    if (plots_dir / "status_pie.png").exists():
        plots["status_pie"] = "assets/plots/status_pie.png"
    if (plots_dir / "embedding_space.png").exists():
        plots["embedding_space"] = "assets/plots/embedding_space.png"
    if (plots_dir / "lineage_full.svg").exists():
        plots["lineage_tree"] = "assets/plots/lineage_full.svg"

    logger.info("Generating task subtree plots...")
    archived = list(archive.get_archived())
    for task in archived:
        if task.parents:
            generate_task_lineage_subtree(task, archive, plots_dir / f"lineage_{task.id}.svg")

    logger.info("Creating parent task lookup...")
    parent_tasks = {}
    for task in archived:
        if task.archive_idx is not None:
            parent_tasks[task.archive_idx] = task

    logger.info(f"Rendering {len(all_tasks)} task pages...")
    for task in all_tasks:
        llm_logs = load_llm_logs(run_dir, paths, task)
        render_task_page(task, parent_tasks, all_tasks, run_dir, paths, viz_dir, llm_logs)

    logger.info("Rendering dashboard...")
    run_name = run_dir.name
    render_dashboard(archive, run_name, run_dir, viz_dir, plots)

    logger.info(f"✓ Visualization complete: {viz_dir / 'index.html'}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = tyro.cli(Args)
    render_run(args.run_dir, args.force)


if __name__ == "__main__":
    main()
