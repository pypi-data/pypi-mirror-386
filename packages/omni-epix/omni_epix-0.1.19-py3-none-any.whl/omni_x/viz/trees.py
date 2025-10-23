from pathlib import Path

from omni_x.core import Archive, Task


def generate_lineage_tree(archive: Archive, output_path: Path) -> None:
    """Generate full lineage tree SVG using graphviz."""
    try:
        import graphviz
    except ImportError:
        return

    archived = list(archive.get_archived())
    if not archived:
        return

    dot = graphviz.Digraph(comment='Task Lineage Tree')
    dot.attr(rankdir='TB', size='12,16!')
    dot.attr('node', shape='box', style='rounded,filled', fontname='monospace', fontsize='10')

    for task in archived:
        color = '#d1fae5' if task.success else '#fee2e2' if task.success is False else '#f3f4f6'
        label = f"#{task.archive_idx}\\n{task.id[:8]}"
        dot.node(str(task.archive_idx), label, fillcolor=color)

        if task.parents:
            for parent_idx in task.parents:
                dot.edge(str(parent_idx), str(task.archive_idx))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dot.render(output_path.with_suffix(''), format='svg', cleanup=True)


def generate_task_lineage_subtree(task: Task, archive: Archive, output_path: Path) -> None:
    """Generate lineage subtree for a specific task (ancestors only)."""
    try:
        import graphviz
    except ImportError:
        return

    if not task.parents:
        return

    dot = graphviz.Digraph(comment=f'Task {task.id} Lineage')
    dot.attr(rankdir='TB', size='8,10!')
    dot.attr('node', shape='box', style='rounded,filled', fontname='monospace', fontsize='10')

    visited = set()

    def add_task_and_parents(t: Task, depth: int = 0):
        if t.archive_idx in visited or depth > 10:
            return
        visited.add(t.archive_idx)

        color = '#dbeafe' if t.archive_idx == task.archive_idx else (
            '#d1fae5' if t.success else '#fee2e2' if t.success is False else '#f3f4f6'
        )
        label = f"#{t.archive_idx}\\n{t.id[:8]}"
        dot.node(str(t.archive_idx), label, fillcolor=color)

        if t.parents:
            for parent_idx in t.parents:
                try:
                    parent = archive.get(parent_idx)
                    add_task_and_parents(parent, depth + 1)
                    dot.edge(str(parent_idx), str(t.archive_idx))
                except KeyError:
                    pass

    add_task_and_parents(task)

    if len(visited) > 1:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dot.render(output_path.with_suffix(''), format='svg', cleanup=True)
