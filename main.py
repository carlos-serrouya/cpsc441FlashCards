import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import random

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML is required. Install it with: pip install pyyaml")


class FlashcardApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Flashcards")
        self.root.geometry("900x600")
        self.root.minsize(700, 450)

        self.cards = []
        self.index = 0
        self.answer_visible = False
        self.shuffle_enabled = tk.BooleanVar(value=False)
        self.card_file = None

        self._build_ui()
        self._render_empty_state()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)

        top_bar = ttk.Frame(outer)
        top_bar.pack(fill="x", pady=(0, 12))

        ttk.Button(top_bar, text="Open YAML", command=self.open_yaml).pack(side="left")
        ttk.Button(top_bar, text="Reveal / Hide", command=self.toggle_answer).pack(side="left", padx=8)
        ttk.Button(top_bar, text="Shuffle", command=self.shuffle_cards).pack(side="left")

        ttk.Checkbutton(
            top_bar,
            text="Shuffle on load",
            variable=self.shuffle_enabled,
        ).pack(side="left", padx=(12, 0))

        self.status_var = tk.StringVar(value="No deck loaded")
        ttk.Label(top_bar, textvariable=self.status_var).pack(side="right")

        self.card_frame = ttk.Frame(outer, padding=18, relief="solid", borderwidth=1)
        self.card_frame.pack(fill="both", expand=True)

        self.counter_var = tk.StringVar(value="0 / 0")
        ttk.Label(self.card_frame, textvariable=self.counter_var, font=("Arial", 11, "bold")).pack(anchor="ne")

        self.question_label = tk.Label(
            self.card_frame,
            text="",
            font=("Arial", 18, "bold"),
            justify="left",
            wraplength=800,
            anchor="w",
        )
        self.question_label.pack(fill="x", pady=(10, 20))

        self.answer_label = tk.Label(
            self.card_frame,
            text="",
            font=("Arial", 15),
            justify="left",
            wraplength=800,
            anchor="w",
        )
        self.answer_label.pack(fill="x")

        bottom_bar = ttk.Frame(outer)
        bottom_bar.pack(fill="x", pady=(12, 0))

        ttk.Button(bottom_bar, text="Previous", command=self.prev_card).pack(side="left")
        ttk.Button(bottom_bar, text="Next", command=self.next_card).pack(side="left", padx=8)
        ttk.Button(bottom_bar, text="Random", command=self.random_card).pack(side="left")

        ttk.Label(
            bottom_bar,
            text="Keyboard: ←/→ move, Space reveal, O open, S shuffle",
        ).pack(side="right")

        self.root.bind("<Left>", lambda _event: self.prev_card())
        self.root.bind("<Right>", lambda _event: self.next_card())
        self.root.bind("<space>", lambda _event: self.toggle_answer())
        self.root.bind("<o>", lambda _event: self.open_yaml())
        self.root.bind("<O>", lambda _event: self.open_yaml())
        self.root.bind("<s>", lambda _event: self.shuffle_cards())
        self.root.bind("<S>", lambda _event: self.shuffle_cards())

    def open_yaml(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Open flashcard YAML",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            loaded_cards = self._load_cards_from_yaml(Path(file_path))
        except Exception as exc:
            messagebox.showerror("Could not load deck", str(exc))
            return

        self.cards = loaded_cards
        self.card_file = Path(file_path)
        self.index = 0
        self.answer_visible = False

        if self.shuffle_enabled.get():
            random.shuffle(self.cards)

        self.status_var.set(f"Loaded {len(self.cards)} cards from {self.card_file.name}")
        self._render_card()

    def _load_cards_from_yaml(self, path: Path):
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            raise ValueError("The YAML file is empty.")

        cards = []

        if isinstance(data, list):
            for i, item in enumerate(data, start=1):
                if not isinstance(item, dict):
                    raise ValueError(f"Card {i} must be a mapping like {{q: ..., a: ...}}.")
                q = item.get("q") or item.get("question")
                a = item.get("a") or item.get("answer")
                if q is None or a is None:
                    raise ValueError(f"Card {i} is missing 'q'/'a' or 'question'/'answer'.")
                cards.append((str(q).strip(), str(a).strip()))

        elif isinstance(data, dict):
            normalized = {str(k).strip().lower(): v for k, v in data.items()}

            indices = sorted(
                {
                    key[1:]
                    for key in normalized
                    if key.startswith("q") and key[1:].isdigit()
                },
                key=lambda x: int(x),
            )

            if indices:
                for idx in indices:
                    q_key = f"q{idx}"
                    a_key = f"a{idx}"
                    if q_key not in normalized or a_key not in normalized:
                        raise ValueError(f"Missing matching pair for {q_key}/{a_key}.")
                    cards.append((str(normalized[q_key]).strip(), str(normalized[a_key]).strip()))
            else:
                raise ValueError(
                    "Unsupported YAML structure. Use either a list of {q, a} cards or flat q1/a1 pairs."
                )
        else:
            raise ValueError("Top-level YAML must be a list or a mapping.")

        cards = [(q, a) for q, a in cards if q and a]
        if not cards:
            raise ValueError("No valid flashcards were found.")

        return cards

    def _render_empty_state(self) -> None:
        self.counter_var.set("0 / 0")
        self.question_label.config(text="Open a YAML file to start studying.")
        self.answer_label.config(text="")

    def _render_card(self) -> None:
        if not self.cards:
            self._render_empty_state()
            return

        question, answer = self.cards[self.index]
        self.counter_var.set(f"{self.index + 1} / {len(self.cards)}")
        self.question_label.config(text=f"Q: {question}")

        if self.answer_visible:
            self.answer_label.config(text=f"A: {answer}")
        else:
            self.answer_label.config(text="Click Reveal / Hide or press Space to show the answer.")

    def toggle_answer(self) -> None:
        if not self.cards:
            return
        self.answer_visible = not self.answer_visible
        self._render_card()

    def next_card(self) -> None:
        if not self.cards:
            return
        self.index = (self.index + 1) % len(self.cards)
        self.answer_visible = False
        self._render_card()

    def prev_card(self) -> None:
        if not self.cards:
            return
        self.index = (self.index - 1) % len(self.cards)
        self.answer_visible = False
        self._render_card()

    def random_card(self) -> None:
        if not self.cards:
            return
        if len(self.cards) == 1:
            self.index = 0
        else:
            current = self.index
            while self.index == current:
                self.index = random.randrange(len(self.cards))
        self.answer_visible = False
        self._render_card()

    def shuffle_cards(self) -> None:
        if not self.cards:
            return
        random.shuffle(self.cards)
        self.index = 0
        self.answer_visible = False
        self._render_card()
        self.status_var.set(f"Shuffled {len(self.cards)} cards")


def main() -> None:
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    FlashcardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()