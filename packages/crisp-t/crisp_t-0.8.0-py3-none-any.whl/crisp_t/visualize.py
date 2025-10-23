import logging
import math
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence, Tuple, cast

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.text import Annotation
from matplotlib.ticker import FuncFormatter
from sklearn.manifold import TSNE
from wordcloud import STOPWORDS, WordCloud

try:
    import pyLDAvis
    import pyLDAvis.gensim_models as gensimvis
    PYLDAVIS_AVAILABLE = True
except ImportError:
    PYLDAVIS_AVAILABLE = False

from .model.corpus import Corpus

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class QRVisualize:

    def __init__(
        self, corpus: Corpus | None = None, folder_path: str | None = None
    ) -> None:
        # Matplotlib figure components assigned lazily by plotting methods
        self.corpus = corpus
        self.folder_path = folder_path
        self.fig: Figure | None = None
        self.ax: Axes | None = None
        self.sc: PathCollection | None = None
        self.annot: Annotation | None = None
        self.names: list[str] = []
        self.c: np.ndarray | None = None

    def _ensure_columns(self, df: pd.DataFrame, required: Iterable[str]) -> pd.DataFrame:
        """Ensure that the DataFrame has the required columns.

        Behavior:
        - If all required columns already exist, return df unchanged.
        - If the DataFrame has exactly the same number of columns as required,
          rename columns positionally to match the required names.
        - Otherwise, raise a ValueError listing the missing columns.
        """
        required = list(required)
        # Fast path: all required columns present
        missing = [col for col in required if col not in df.columns]
        if not missing:
            return df

        # If shape matches, attempt a positional rename
        if len(df.columns) == len(required):
            df = df.copy()
            df.columns = required
            return df

        # Otherwise, cannot satisfy required columns
        raise ValueError(f"Missing required columns: {missing}")

    def _finalize_plot(
        self,
        fig: Figure,
        folder_path: str | None,
        show: bool,
    ) -> Figure:
        if not folder_path:
            folder_path = self.folder_path
        if folder_path:
            output_path = Path(folder_path)
            if output_path.parent:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(folder_path)
        if show:
            plt.show(block=False)
        else:
            plt.close(fig)
        return fig

    def plot_frequency_distribution_of_words(
        self,
        df: pd.DataFrame | None = None,
        folder_path: str | None = None,
        text_column: str = "Text",
        bins: int = 100,
        show: bool = True,
    ) -> Tuple[Figure, Axes]:
        if df is None:
            try:
                df = pd.DataFrame(self.corpus.visualization["assign_topics"])
            except Exception as e:
                raise ValueError(f"Failed to create DataFrame from corpus: {e}")
        df = self._ensure_columns(df, [text_column])
        doc_lens = df[text_column].dropna().map(len).tolist()
        if not doc_lens:
            raise ValueError("No documents available to plot frequency distribution.")

        fig, ax = plt.subplots(figsize=(16, 7), dpi=160)
        counts, _, _ = ax.hist(doc_lens, bins=bins, color="navy")
        counts = np.asarray(counts)
        if counts.size:
            ax.set_ylim(top=float(counts.max()) * 1.1)

        stats = {
            "Mean": round(np.mean(doc_lens), 2),
            "Median": round(np.median(doc_lens), 2),
            "Stdev": round(np.std(doc_lens), 2),
            "1%ile": round(np.quantile(doc_lens, q=0.01), 2),
            "99%ile": round(np.quantile(doc_lens, q=0.99), 2),
        }
        for idx, (label, value) in enumerate(stats.items()):
            ax.text(
                0.98,
                0.98 - idx * 0.05,
                f"{label}: {value}",
                transform=ax.transAxes,
                ha="right",
                va="top",
                fontsize=11,
            )

        ax.set(
            ylabel="Number of Documents",
            xlabel="Document Word Count",
            title="Distribution of Document Word Counts",
        )
        ax.tick_params(axis="both", labelsize=12)
        if doc_lens:
            ax.set_xlim(left=0, right=max(doc_lens) * 1.05)

        fig = self._finalize_plot(fig, folder_path, show)
        return fig, ax

    def plot_distribution_by_topic(
        self,
        df: pd.DataFrame | None = None,
        folder_path: str | None = None,
        topic_column: str = "Dominant_Topic",
        text_column: str = "Text",
        bins: int = 100,
        show: bool = True,
    ) -> Tuple[Figure, np.ndarray]:
        if df is None:
            try:
                df = pd.DataFrame(self.corpus.visualization["assign_topics"])
            except Exception as e:
                raise ValueError(f"Failed to create DataFrame from corpus: {e}")
        df = self._ensure_columns(df, [topic_column, text_column])
        unique_topics = sorted(df[topic_column].dropna().unique())
        if not unique_topics:
            raise ValueError("No topics found to plot distribution.")

        n_topics = len(unique_topics)
        n_cols = min(3, n_topics)
        n_rows = math.ceil(n_topics / n_cols)
        cols = list(mcolors.TABLEAU_COLORS.values())

        fig, axes = plt.subplots(
            n_rows,
            n_cols,
            figsize=(6 * n_cols, 5 * n_rows),
            dpi=160,
            sharex=True,
            sharey=True,
        )
        if isinstance(axes, np.ndarray):
            axes_flat = axes.flatten().tolist()
        else:
            axes_flat = [axes]

        for idx, topic in enumerate(unique_topics):
            ax = axes_flat[idx]
            topic_series = cast(
                pd.Series,
                df.loc[df[topic_column] == topic, text_column],
            )
            topic_docs = topic_series.dropna()
            doc_lens = topic_docs.map(len).tolist()
            color = cols[idx % len(cols)]
            if doc_lens:
                ax.hist(doc_lens, bins=bins, color=color, alpha=0.7)
                sns.kdeplot(
                    doc_lens,
                    color="black",
                    fill=False,
                    ax=ax.twinx(),
                    warn_singular=False,
                )
            ax.set(xlabel="Document Word Count")
            ax.set_ylabel("Number of Documents", color=color)
            ax.set_title(f"Topic: {topic}", fontdict=dict(size=14, color=color))
            ax.tick_params(axis="y", labelcolor=color, color=color)

        for extra_ax in axes_flat[len(unique_topics) :]:
            extra_ax.set_visible(False)

        fig.tight_layout()
        fig.suptitle(
            "Distribution of Document Word Counts by Dominant Topic",
            fontsize=20,
            y=1.02,
        )

        fig = self._finalize_plot(fig, folder_path, show)
        axes_array = np.array(axes_flat, dtype=object).reshape(n_rows, n_cols)
        return fig, axes_array

    def plot_wordcloud(
        self,
        topics=None,
        folder_path: str | None = None,
        max_words: int = 50,
        show: bool = True,
    ) -> Tuple[Figure, np.ndarray]:
        if not topics:
            try:
                topics = self.corpus.visualization["word_cloud"]
            except Exception as e:
                raise ValueError(f"Failed to retrieve topics from corpus: {e}")
        n_topics = len(topics)
        n_cols = min(3, n_topics)
        n_rows = math.ceil(n_topics / n_cols)
        cols = list(mcolors.TABLEAU_COLORS.values())

        fig, axes = plt.subplots(
            n_rows,
            n_cols,
            figsize=(6 * n_cols, 4 * n_rows),
            sharex=True,
            sharey=True,
        )
        axes_flat = axes.flatten().tolist() if isinstance(axes, np.ndarray) else [axes]

        for idx, (topic_id, words) in enumerate(topics):
            ax = axes_flat[idx]
            topic_words = dict(words)
            color = cols[idx % len(cols)]
            cloud = WordCloud(
                stopwords=STOPWORDS,
                background_color="white",
                width=800,
                height=400,
                max_words=max_words,
                colormap="tab10",
                color_func=lambda *args, color=color, **kwargs: color,
                prefer_horizontal=0.9,
            )
            cloud.generate_from_frequencies(topic_words)
            ax.imshow(cloud)
            ax.set_title(f"Topic {topic_id}", fontdict=dict(size=14))
            ax.axis("off")

        for extra_ax in axes_flat[len(topics) :]:
            extra_ax.set_visible(False)

        fig.tight_layout()

        fig = self._finalize_plot(fig, folder_path, show)
        return fig, np.array(axes_flat).reshape(n_rows, n_cols)

    def plot_top_terms(
        self,
        df: pd.DataFrame | None = None,
        term_column: str = "term",
        frequency_column: str = "frequency",
        top_n: int = 20,
        folder_path: str | None = None,
        ascending: bool = False,
        show: bool = True,
    ) -> Tuple[Figure, Axes]:
        if df is None:
            try:
                df = pd.DataFrame(self.corpus.visualization["assign_topics"])
            except Exception as e:
                raise ValueError(f"Failed to create DataFrame from corpus: {e}")
        if top_n <= 0:
            raise ValueError("top_n must be greater than zero.")

        df = self._ensure_columns(df, [term_column, frequency_column])
        subset = df[[term_column, frequency_column]].dropna()
        if subset.empty:
            raise ValueError("No data available to plot top terms.")

        subset = subset.sort_values(frequency_column, ascending=ascending).head(top_n)
        subset = subset.iloc[::-1]

        fig, ax = plt.subplots(figsize=(10, max(4, top_n * 0.4)))
        ax.barh(subset[term_column], subset[frequency_column], color="steelblue")
        ax.set_xlabel("Frequency")
        ax.set_ylabel("Term")
        ax.set_title("Top Terms by Frequency")
        for idx, value in enumerate(subset[frequency_column]):
            ax.text(value, idx, f" {value}", va="center")
        fig.tight_layout()

        fig = self._finalize_plot(fig, folder_path, show)
        return fig, ax

    def plot_correlation_heatmap(
        self,
        df: pd.DataFrame | None = None,
        columns: Sequence[str] | None = None,
        folder_path: str | None = None,
        cmap: str = "coolwarm",
        show: bool = True,
    ) -> Tuple[Figure, Axes]:
        if df is None:
            try:
                df = pd.DataFrame(self.corpus.visualization["assign_topics"])
            except Exception as e:
                raise ValueError(f"Failed to create DataFrame from corpus: {e}")
        if columns:
            df = self._ensure_columns(df, columns)
            data = df[list(columns)]
        else:
            data = df
        if data.empty:
            raise ValueError("No data available to compute correlation heatmap.")

        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.shape[1] < 2:
            raise ValueError(
                "At least two numeric columns are required for correlation heatmap."
            )

        corr = numeric_data.corr()
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr, ax=ax, cmap=cmap, annot=True, fmt=".2f", square=True)
        ax.set_title("Correlation Heatmap")
        fig.tight_layout()

        fig = self._finalize_plot(fig, folder_path, show)
        return fig, ax

    def plot_importance(
        self,
        topics: Sequence[Tuple[int, Sequence[Tuple[str, float]]]],
        processed_docs: Sequence[Sequence[str]],
        folder_path: str | None = None,
        show: bool = True,
    ) -> Tuple[Figure, np.ndarray]:
        if not topics:
            raise ValueError("No topics provided to plot importance.")
        if not processed_docs:
            raise ValueError("No processed documents provided to plot importance.")

        counter = Counter(word for doc in processed_docs for word in doc)
        rows = []
        for topic_id, words in topics:
            for word, weight in words:
                rows.append(
                    {
                        "word": word,
                        "topic_id": topic_id,
                        "importance": weight,
                        "word_count": counter.get(word, 0),
                    }
                )

        df = pd.DataFrame(rows)
        if df.empty:
            raise ValueError("Unable to build importance DataFrame from inputs.")

        topic_ids = sorted(df["topic_id"].unique())
        n_topics = len(topic_ids)
        n_cols = min(3, n_topics)
        n_rows = math.ceil(n_topics / n_cols)
        cols = list(mcolors.TABLEAU_COLORS.values())

        fig, axes = plt.subplots(
            n_rows,
            n_cols,
            figsize=(7 * n_cols, 5 * n_rows),
            sharey=False,
            dpi=160,
        )
        axes_flat = axes.flatten().tolist() if isinstance(axes, np.ndarray) else [axes]

        for idx, topic_id in enumerate(topic_ids):
            ax = axes_flat[idx]
            subset = df[df["topic_id"] == topic_id]
            color = cols[idx % len(cols)]
            ax.bar(
                subset["word"],
                subset["word_count"],
                color=color,
                width=0.5,
                alpha=0.4,
                label="Word Count",
            )
            ax_twin = ax.twinx()
            ax_twin.plot(
                subset["word"],
                subset["importance"],
                color=color,
                marker="o",
                label="Importance",
            )
            ax.set_title(f"Topic {topic_id}", color=color, fontsize=14)
            ax.set_xlabel("Word")
            ax.set_ylabel("Word Count", color=color)
            ax.tick_params(axis="y", labelcolor=color)
            ax_twin.set_ylabel("Importance", color=color)
            ax_twin.tick_params(axis="y", labelcolor=color)
            ax.set_xticklabels(subset["word"], rotation=30, ha="right")
            ax.legend(loc="upper left")
            ax_twin.legend(loc="upper right")

        for extra_ax in axes_flat[len(topic_ids) :]:
            extra_ax.set_visible(False)

        fig.tight_layout()
        fig.suptitle(
            "Word Count and Importance of Topic Keywords",
            fontsize=20,
            y=1.02,
        )

        fig = self._finalize_plot(fig, folder_path, show)
        return fig, np.array(axes_flat).reshape(n_rows, n_cols)

    def sentence_chart(self, lda_model, text, start=0, end=13, folder_path=None):
        if lda_model is None:
            raise ValueError("LDA model is not provided.")
        corp = text[start:end]
        mycolors = [color for name, color in mcolors.TABLEAU_COLORS.items()]

        fig, axes = plt.subplots(
            end - start, 1, figsize=(20, (end - start) * 0.95), dpi=160
        )
        axes[0].axis("off")
        for i, ax in enumerate(axes):
            try:
                if i > 0:
                    corp_cur = corp[i - 1]
                    topic_percs, wordid_topics, _ = lda_model[corp_cur]
                    word_dominanttopic = [
                        (lda_model.id2word[wd], topic[0]) for wd, topic in wordid_topics
                    ]
                    ax.text(
                        0.01,
                        0.5,
                        "Doc " + str(i - 1) + ": ",
                        verticalalignment="center",
                        fontsize=16,
                        color="black",
                        transform=ax.transAxes,
                        fontweight=700,
                    )

                    # Draw Rectange
                    topic_percs_sorted = sorted(
                        topic_percs, key=lambda x: (x[1]), reverse=True
                    )
                    ax.add_patch(
                        Rectangle(
                            (0.0, 0.05),
                            0.99,
                            0.90,
                            fill=None,
                            alpha=1,
                            color=mycolors[topic_percs_sorted[0][0]],
                            linewidth=2,
                        )
                    )

                    word_pos = 0.06
                    for j, (word, topics) in enumerate(word_dominanttopic):
                        if j < 14:
                            ax.text(
                                word_pos,
                                0.5,
                                word,
                                horizontalalignment="left",
                                verticalalignment="center",
                                fontsize=16,
                                color=mycolors[topics],
                                transform=ax.transAxes,
                                fontweight=700,
                            )
                            word_pos += 0.009 * len(
                                word
                            )  # to move the word for the next iter
                            ax.axis("off")
                    ax.text(
                        word_pos,
                        0.5,
                        ". . .",
                        horizontalalignment="left",
                        verticalalignment="center",
                        fontsize=16,
                        color="black",
                        transform=ax.transAxes,
                    )
            except Exception as e:
                logger.error(f"Error occurred while processing document {i - 1}: {e}")
                continue

        plt.subplots_adjust(wspace=0, hspace=0)
        plt.suptitle(
            "Sentence Topic Coloring for Documents: "
            + str(start)
            + " to "
            + str(end - 2),
            fontsize=22,
            y=0.95,
            fontweight=700,
        )
        plt.tight_layout()
        plt.show(block=False)
        # save
        if folder_path:
            plt.savefig(folder_path)
            plt.close()

    def _cluster_chart(self, lda_model, text, n_topics=3, folder_path=None):
        # Get topic weights
        topic_weights = []
        for i, row_list in enumerate(lda_model[text]):
            topic_weights.append([w for i, w in row_list[0]])

        # Array of topic weights
        arr = pd.DataFrame(topic_weights).fillna(0).values

        # Keep the well separated points (optional)
        arr = arr[np.amax(arr, axis=1) > 0.35]

        # Dominant topic number in each doc
        topic_num = np.argmax(arr, axis=1)

        # tSNE Dimension Reduction
        tsne_model = TSNE(
            n_components=2, verbose=1, random_state=0, angle=0.99, init="pca"
        )
        tsne_lda = tsne_model.fit_transform(arr)

        # Plot
        plt.figure(figsize=(16, 10), dpi=160)
        for i in range(n_topics):
            plt.scatter(
                tsne_lda[topic_num == i, 0],
                tsne_lda[topic_num == i, 1],
                label=str(i),
                alpha=0.5,
            )
        plt.title("t-SNE Clustering of Topics", fontsize=22)
        plt.xlabel("t-SNE Dimension 1", fontsize=16)
        plt.ylabel("t-SNE Dimension 2", fontsize=16)
        plt.legend(title="Topic Number", loc="upper right")
        plt.show(block=False)
        # save
        if folder_path:
            plt.savefig(folder_path)
            plt.close()

    def most_discussed_topics(
        self, lda_model, dominant_topics, topic_percentages, folder_path=None
    ):

        # Distribution of Dominant Topics in Each Document
        df = pd.DataFrame(dominant_topics, columns=["Document_Id", "Dominant_Topic"])
        dominant_topic_in_each_doc = df.groupby("Dominant_Topic").size()
        df_dominant_topic_in_each_doc = dominant_topic_in_each_doc.to_frame(
            name="count"
        ).reset_index()

        # Total Topic Distribution by actual weight
        topic_weightage_by_doc = pd.DataFrame([dict(t) for t in topic_percentages])
        df_topic_weightage_by_doc = (
            topic_weightage_by_doc.sum().to_frame(name="count").reset_index()
        )

        # Top 3 Keywords for each Topic
        topic_top3words = [
            (i, topic)
            for i, topics in lda_model.show_topics(formatted=False)
            for j, (topic, wt) in enumerate(topics)
            if j < 3
        ]

        df_top3words_stacked = pd.DataFrame(
            topic_top3words, columns=["topic_id", "words"]
        )
        df_top3words = df_top3words_stacked.groupby("topic_id").agg(", \n".join)
        df_top3words.reset_index(level=0, inplace=True)

        # Plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), dpi=120, sharey=True)

        # Topic Distribution by Dominant Topics
        ax1.bar(
            x="Dominant_Topic",
            height="count",
            data=df_dominant_topic_in_each_doc,
            width=0.5,
            color="firebrick",
        )
        ax1.set_xticks(
            range(df_dominant_topic_in_each_doc.Dominant_Topic.unique().__len__())
        )
        tick_formatter = FuncFormatter(
            lambda x, pos: "Topic "
            + str(x)
            + "\n"
            + df_top3words.loc[df_top3words.topic_id == x, "words"].values[0]  # type: ignore
        )
        ax1.xaxis.set_major_formatter(tick_formatter)
        ax1.set_title("Number of Documents by Dominant Topic", fontdict=dict(size=10))
        ax1.set_ylabel("Number of Documents")
        ax1.set_ylim(0, 1000)

        # Topic Distribution by Topic Weights
        ax2.bar(
            x="index",
            height="count",
            data=df_topic_weightage_by_doc,
            width=0.5,
            color="steelblue",
        )
        ax2.set_xticks(range(df_topic_weightage_by_doc.index.unique().__len__()))
        ax2.xaxis.set_major_formatter(tick_formatter)
        ax2.set_title("Number of Documents by Topic Weightage", fontdict=dict(size=10))

        plt.show(block=False)

        # save
        if folder_path:
            plt.savefig(folder_path)
            plt.close()

    def update_annot(self, ind):
        if self.annot is None or self.sc is None or self.c is None:
            raise RuntimeError("cluster_chart must be called before update_annot.")
        indices_array = np.atleast_1d(ind.get("ind", []))
        if indices_array.size == 0:
            return
        indices = indices_array.astype(int)
        idx = int(indices[0])
        offsets = np.asarray(self.sc.get_offsets())
        pos = offsets[idx]
        annot = self.annot
        annot.xy = (float(pos[0]), float(pos[1]))
        text = "{}, {}".format(
            " ".join(list(map(str, indices))),
            " ".join([self.names[n] for n in indices]),
        )
        annot.set_text(text)
        cmap = plt.get_cmap("RdYlGn")
        norm = mcolors.Normalize(1, 4)
        bbox = annot.get_bbox_patch()
        if bbox is not None:
            try:
                color_value = float(self.c[idx])
            except (TypeError, ValueError):
                color_value = 1.0
            bbox.set_facecolor(cmap(norm(color_value)))
            bbox.set_alpha(0.4)

    def hover(self, event):
        if self.annot is None or self.sc is None or self.fig is None or self.ax is None:
            return
        vis = self.annot.get_visible()
        if event.inaxes == self.ax:
            cont, ind = self.sc.contains(event)
            if cont:
                self.update_annot(ind)
                self.annot.set_visible(True)
                self.fig.canvas.draw_idle()
            elif vis:
                self.annot.set_visible(False)
                self.fig.canvas.draw_idle()

    # https://stackoverflow.com/questions/7908636/how-to-add-hovering-annotations-to-a-plot
    def cluster_chart(self, data, folder_path=None):
        # Scatter plot for Text Cluster Prediction
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.names = list(map(str, data["title"]))
        self.sc = plt.scatter(
            data["x"],
            data["y"],
            c=data["colour"],
            s=36,
            edgecolors="black",
            linewidths=0.75,
        )
        self.c = np.asarray(data["colour"])
        self.annot = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(20, 20),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"),
            arrowprops=dict(arrowstyle="->"),
        )
        self.annot.set_visible(False)
        plt.title("Text Cluster Prediction")
        plt.axis("off")  # Optional: Remove axes for a cleaner look
        plt.colorbar(self.sc, label="Colour")  # Add colorbar if needed
        self.fig.canvas.mpl_connect("motion_notify_event", self.hover)
        plt.show(block=False)
        # save
        if folder_path:
            # annotate with data['title']
            for i, txt in enumerate(data["title"]):
                plt.annotate(
                    txt,
                    (data["x"][i], data["y"][i]),
                    fontsize=8,
                    ha="right",
                    va="bottom",
                )
            plt.savefig(folder_path)
            plt.close()

    def get_lda_viz(
        self,
        lda_model,
        corpus_bow,
        dictionary,
        folder_path: str | None = None,
        mds: str = "tsne",
        lambda_val: float = 0.6,
        show: bool = True,
    ) -> str | None:
        """
        Generate an interactive LDA visualization using pyLDAvis.

        Args:
            lda_model: The trained LDA model
            corpus_bow: Bag of words corpus
            dictionary: Gensim dictionary
            folder_path: Path to save the HTML visualization
            mds: Dimension reduction method ('tsne', 'mmds', or 'pcoa')
            lambda_val: Lambda parameter for relevance metric (default: 0.6).
                       Mettler et al. (2025) performed several experiments to identify
                       the optimal value of λ, which turned out to be 0.6.
            show: Whether to display the visualization

        Returns:
            HTML string of the visualization if successful, None otherwise

        Raises:
            ImportError: If pyLDAvis is not installed
            ValueError: If required inputs are missing
        """
        if not PYLDAVIS_AVAILABLE:
            raise ImportError(
                "pyLDAvis is not installed. Install it with: pip install pyLDAvis"
            )

        if lda_model is None:
            raise ValueError("LDA model is required")
        if corpus_bow is None:
            raise ValueError("Corpus bag of words is required")
        if dictionary is None:
            raise ValueError("Dictionary is required")

        try:
            # Prepare the visualization data
            vis_data = gensimvis.prepare(
                lda_model,
                corpus_bow,
                dictionary,
                mds=mds,
                R=30,
                lambda_step=0.01,
                plot_opts={'xlab': 'PC1', 'ylab': 'PC2'}
            )

            # Save to HTML file if path provided
            if folder_path:
                output_path = Path(folder_path)
                if output_path.parent:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                pyLDAvis.save_html(vis_data, str(output_path))
                logger.info(f"LDA visualization saved to {output_path}")

            # Return HTML string for embedding or further use
            html_string = pyLDAvis.prepared_data_to_html(vis_data)
            return html_string

        except Exception as e:
            logger.error(f"Error generating LDA visualization: {e}")
            raise
