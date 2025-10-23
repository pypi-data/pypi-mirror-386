from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from omni_x.core import Archive, Task


def plot_success_timeline(archive: Archive, output_path: Path) -> None:
    """Plot success rate over time (by archive index)."""
    archived = list(archive.get_archived())
    if not archived:
        return

    indices = []
    successes = []

    for task in archived:
        if task.success is not None:
            indices.append(task.archive_idx)
            successes.append(1 if task.success else 0)

    if not indices:
        return

    window_size = min(10, len(indices))
    moving_avg = np.convolve(successes, np.ones(window_size)/window_size, mode='valid')
    moving_indices = indices[window_size-1:]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(indices, successes, alpha=0.3, s=30, c=['green' if s else 'red' for s in successes])
    if len(moving_avg) > 0:
        ax.plot(moving_indices, moving_avg, 'b-', linewidth=2, label=f'{window_size}-task moving average')
    ax.set_xlabel('Task Archive Index')
    ax.set_ylabel('Success Rate')
    ax.set_title('Task Success Over Time')
    ax.set_ylim(-0.1, 1.1)
    ax.grid(alpha=0.3)
    ax.legend()

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_status_pie(archive: Archive, output_path: Path) -> None:
    """Plot pie chart of task status distribution."""
    archived_count = len(list(archive.get_archived()))
    discarded_count = len(list(archive.get_discarded()))
    wip_count = len(list(archive.get_wip()))

    if archived_count + discarded_count + wip_count == 0:
        return

    fig, ax = plt.subplots(figsize=(8, 8))

    labels = []
    sizes = []
    colors = []

    if archived_count > 0:
        labels.append(f'Archived ({archived_count})')
        sizes.append(archived_count)
        colors.append('#3b82f6')

    if discarded_count > 0:
        labels.append(f'Discarded ({discarded_count})')
        sizes.append(discarded_count)
        colors.append('#6b7280')

    if wip_count > 0:
        labels.append(f'WIP ({wip_count})')
        sizes.append(wip_count)
        colors.append('#f59e0b')

    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.set_title('Task Status Distribution')

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_embedding_space(archive: Archive, embedding_model: str | None, output_path: Path) -> None:
    """Plot 2D embedding space with t-SNE by re-embedding tasks."""
    if embedding_model is None:
        return

    from sklearn.manifold import TSNE
    from sklearn.decomposition import PCA
    from omni_x.components.index.faiss_st import Embedder

    archived = list(archive.get_archived())
    if len(archived) < 3:
        return

    embedder = Embedder(embedding_model)

    embeddings = []
    colors = []
    labels = []

    for task in archived:
        if task.description and task.code:
            emb = embedder([task.embedding_text])[0]
            embeddings.append(emb)
            colors.append('green' if task.success else 'red' if task.success is False else 'gray')
            labels.append(f"#{task.archive_idx}")

    if len(embeddings) < 3:
        return

    embeddings = np.array(embeddings)

    if embeddings.shape[1] > 50:
        n_components = min(50, len(embeddings) - 1, embeddings.shape[1])
        pca = PCA(n_components=n_components)
        embeddings = pca.fit_transform(embeddings)

    if len(embeddings) > 2:
        perplexity = min(30, len(embeddings) - 1)
        tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity)
        coords = tsne.fit_transform(embeddings)
    else:
        coords = embeddings[:, :2]

    fig, ax = plt.subplots(figsize=(12, 10))

    for i, (x, y) in enumerate(coords):
        ax.scatter(x, y, c=colors[i], s=100, alpha=0.6, edgecolors='black', linewidth=0.5)
        ax.text(x, y, labels[i], fontsize=8, ha='center', va='center')

    ax.set_xlabel('t-SNE Component 1')
    ax.set_ylabel('t-SNE Component 2')
    ax.set_title('Task Embedding Space (2D t-SNE)')
    ax.grid(alpha=0.3)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', edgecolor='black', label='Success'),
        Patch(facecolor='red', edgecolor='black', label='Failed'),
        Patch(facecolor='gray', edgecolor='black', label='Not Evaluated'),
    ]
    ax.legend(handles=legend_elements)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
