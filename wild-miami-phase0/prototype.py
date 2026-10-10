"""Scratch desktop prototype (litert-lm vectors): tune, evaluate once, write scoring/golden/manifest. Disposable."""
import argparse
import csv
import hashlib
import importlib.metadata
import itertools
import json
import pathlib
import time

import litert_lm
import numpy

EMBED_DIM: int = 768
LABEL_TEMPLATE: str = "a photo of a {common_name} ({scientific_name})"
PROMPT_PREFIXES: dict[str, str] = {
    "none": "{label}",
    "classification": "task: classification | query: {label}",
    "document": "title: none | text: {label}",
}
SPLITS: tuple[str, ...] = ("p", "d", "t", "r")
W_GRID: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0)
DELTA_GRID: tuple[float, ...] = (0.0, 0.01, 0.02, 0.04, 0.06)
GRID_STEPS: int = 40
MAX_WRONG_LIKELY: float = 0.05
MAX_UNKNOWN_LIKELY: float = 0.05
MAX_KNOWN_ABSTENTION: float = 0.30


def load_species(csv_path: pathlib.Path) -> list[dict[str, str]]:
    """Read the curated species list (columns: id, common_name, scientific_name, lookalike)."""
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows: list[dict[str, str]] = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("Species list is empty")
    return sorted(rows, key=lambda row: int(row["id"]))


def parse_photo(path: pathlib.Path) -> tuple[str, str, str]:
    """Split '<species_id or neg>__<split>__<observation_id>.jpg' into its three parts."""
    parts: list[str] = path.stem.split("__")
    if len(parts) != 3 or parts[1] not in SPLITS:
        raise ValueError(f"Bad photo name: {path.name}")
    return parts[0], parts[1], parts[2]


def check_data(photo_dir: pathlib.Path, negatives_dir: pathlib.Path, species: list[dict[str, str]]) -> None:
    """Fail on bad names, observations shared across splits, species without references or empty eval splits."""
    seen: dict[str, str] = {}
    for path in sorted(photo_dir.glob("*.jpg")) + sorted(negatives_dir.glob("*.jpg")):
        _, split, observation = parse_photo(path)
        first: str = seen.setdefault(observation, split)
        if first != split:
            raise ValueError(f"Observation {observation} appears in splits {first} and {split}")
    for s in species:
        if not list(photo_dir.glob(f"{s['id']}__p__*.jpg")):
            raise ValueError(f"Species {s['id']} has no reference photos")
    for split in ("d", "t"):
        if not list(photo_dir.glob(f"*__{split}__*.jpg")) or not list(negatives_dir.glob(f"neg__{split}__*.jpg")):
            raise ValueError(f"Split '{split}' needs both known and negative photos")


class Embedder:
    """litert-lm embedder over the exact .litertlm file the phone runs, with an on-disk image-vector cache."""

    def __init__(self, model_path: pathlib.Path, cache_path: pathlib.Path) -> None:
        """Load the model on CPU and the vector cache, if any."""
        self.engine: litert_lm.EmbeddingEngine = litert_lm.EmbeddingEngine(
            str(model_path), backend=litert_lm.Backend.CPU(), vision_backend=litert_lm.Backend.CPU()
        )
        self.options: litert_lm.EmbeddingOptions = litert_lm.EmbeddingOptions(normalize=True)
        self.cache_path: pathlib.Path = cache_path
        self.cache: dict[str, numpy.ndarray] = dict(numpy.load(cache_path)) if cache_path.exists() else {}
        self.image_seconds: list[float] = []

    def _vector(self, content: object) -> numpy.ndarray:
        """Embed one input and return a float32 unit vector after shape and finite checks."""
        vec: numpy.ndarray = numpy.asarray(self.engine.compute_embedding(content, self.options).embedding, dtype="<f4")
        if vec.shape != (EMBED_DIM,) or not bool(numpy.all(numpy.isfinite(vec))):
            raise ValueError("Embedding has the wrong shape or non-finite values")
        return vec / numpy.linalg.norm(vec)

    def embed_texts(self, texts: list[str]) -> numpy.ndarray:
        """Embed strings (whitespace trimmed) as rows of unit vectors."""
        return numpy.stack([self._vector(t.strip()) for t in texts])

    def embed_images(self, paths: list[pathlib.Path]) -> numpy.ndarray:
        """Embed photos as rows of unit vectors; litert-lm handles resizing, cached by file name."""
        if not paths:
            raise ValueError("No images to embed")
        rows: list[numpy.ndarray] = []
        for path in paths:
            if path.name not in self.cache:
                start: float = time.perf_counter()
                self.cache[path.name] = self._vector(litert_lm.Content.ImageFile(str(path)))
                self.image_seconds.append(time.perf_counter() - start)
            rows.append(self.cache[path.name])
        return numpy.stack(rows)

    def save(self) -> None:
        """Persist the image-vector cache."""
        numpy.savez(self.cache_path, **self.cache)


def build_prompts(species: list[dict[str, str]], prefix: str) -> list[str]:
    """Return one text prompt per species using the given task prefix."""
    return [PROMPT_PREFIXES[prefix].format(label=LABEL_TEMPLATE.format(**s)) for s in species]


def reference_vectors(embedder: Embedder, species: list[dict[str, str]], photo_dir: pathlib.Path) -> tuple[list[numpy.ndarray], list[list[str]]]:
    """Return a stack of reference-image vectors per species plus the file names in deterministic order."""
    stacks: list[numpy.ndarray] = []
    names: list[list[str]] = []
    for s in species:
        refs: list[pathlib.Path] = sorted(photo_dir.glob(f"{s['id']}__p__*.jpg"))
        stacks.append(embedder.embed_images(refs))
        names.append([p.name for p in refs])
    return stacks, names


def load_split(embedder: Embedder, species: list[dict[str, str]], photo_dir: pathlib.Path, negatives_dir: pathlib.Path, split: str) -> tuple[numpy.ndarray, list[int], list[str]]:
    """Embed one evaluation split plus its negatives; label -1 marks out-of-catalog photos."""
    index: dict[str, int] = {s["id"]: i for i, s in enumerate(species)}
    known: list[pathlib.Path] = sorted(photo_dir.glob(f"*__{split}__*.jpg"))
    negatives: list[pathlib.Path] = sorted(negatives_dir.glob(f"neg__{split}__*.jpg"))
    labels: list[int] = [index[parse_photo(p)[0]] for p in known] + [-1] * len(negatives)
    return embedder.embed_images(known + negatives), labels, [p.name for p in known + negatives]


def blended_scores(photos: numpy.ndarray, text: numpy.ndarray, images: list[numpy.ndarray], w: float) -> numpy.ndarray:
    """Return raw ranking scores, one row per photo and one column per species (not probabilities)."""
    image_best: numpy.ndarray = numpy.stack([(photos @ stack.T).max(axis=1) for stack in images], axis=1)
    return w * image_best + (1.0 - w) * (photos @ text.T)


def verdict(row: numpy.ndarray, theta: float, delta: float, possible_floor: float) -> str:
    """Return 'likely', 'possible' or 'unsure' for one photo's scores."""
    ordered: numpy.ndarray = numpy.sort(row)[::-1]
    if ordered[0] >= theta and ordered[0] - ordered[1] >= delta:
        return "likely"
    if ordered[0] >= possible_floor:
        return "possible"
    return "unsure"


def top_k(row: numpy.ndarray, k: int) -> list[int]:
    """Return column indices of the k highest scores, best first (stable on ties)."""
    return [int(i) for i in numpy.argsort(-row, kind="stable")[:k]]


def evaluate(scores: numpy.ndarray, labels: list[int], theta: float, delta: float, possible_floor: float) -> dict[str, float]:
    """Return raw counts (n_*) and rates for retrieval, likely-coverage and open-set safety."""
    counts: dict[str, int] = dict.fromkeys(
        ("known", "unknown", "top1", "top3", "correct_likely", "wrong_likely", "known_unsure", "unknown_likely", "unknown_unsure"), 0
    )
    for row, label in zip(scores, labels):
        call: str = verdict(row, theta, delta, possible_floor)
        if label < 0:
            counts["unknown"] += 1
            counts["unknown_likely"] += int(call == "likely")
            counts["unknown_unsure"] += int(call == "unsure")
            continue
        top3: list[int] = top_k(row, 3)
        hit: bool = top3[0] == label
        counts["known"] += 1
        counts["top1"] += int(hit)
        counts["top3"] += int(label in top3)
        counts["correct_likely"] += int(call == "likely" and hit)
        counts["wrong_likely"] += int(call == "likely" and not hit)
        counts["known_unsure"] += int(call == "unsure")
    known: int = counts["known"]
    unknown: int = counts["unknown"]
    rates: dict[str, float] = {
        "top1_accuracy": counts["top1"] / known,
        "top3_accuracy": counts["top3"] / known,
        "correct_likely_coverage": counts["correct_likely"] / known,
        "wrong_likely_rate": counts["wrong_likely"] / known,
        "known_abstention": counts["known_unsure"] / known,
        "unknown_likely_rate": counts["unknown_likely"] / unknown,
        "unknown_rejection": counts["unknown_unsure"] / unknown,
    }
    return {**{f"n_{name}": float(value) for name, value in counts.items()}, **rates}


def select_prompt_and_w(embedder: Embedder, species: list[dict[str, str]], images: list[numpy.ndarray], vecs: numpy.ndarray, labels: list[int]) -> tuple[str, float, numpy.ndarray, list[dict[str, object]]]:
    """Pick task prefix and blend weight by tuning-split top-1 accuracy (top-3 breaks ties)."""
    best: tuple[tuple[float, float], str, float, numpy.ndarray] = ((-1.0, -1.0), "", 0.0, numpy.empty(0))
    trials: list[dict[str, object]] = []
    for prefix in PROMPT_PREFIXES:
        text: numpy.ndarray = embedder.embed_texts(build_prompts(species, prefix))
        for w in W_GRID:
            metrics: dict[str, float] = evaluate(blended_scores(vecs, text, images, w), labels, float("inf"), 0.0, float("inf"))
            key: tuple[float, float] = (metrics["top1_accuracy"], metrics["top3_accuracy"])
            trials.append({"prefix": prefix, "w": w, "top1": key[0], "top3": key[1]})
            if key > best[0]:
                best = (key, prefix, w, text)
    return best[1], best[2], best[3], trials


def tune_thresholds(scores: numpy.ndarray, labels: list[int]) -> dict[str, float]:
    """Maximize correct-likely coverage under the wrong-likely, unknown-likely and abstention limits."""
    top: numpy.ndarray = scores.max(axis=1)
    low: float = float(numpy.floor(top.min() * 100) / 100)
    high: float = float(numpy.ceil(top.max() * 100) / 100)
    grid: list[float] = [round(low + (high - low) * i / GRID_STEPS, 4) for i in range(GRID_STEPS + 1)]
    best: dict[str, float] = {}
    best_key: tuple[float, float, float] = (-1.0, -1.0, -1.0)
    for theta, delta, floor in itertools.product(grid, DELTA_GRID, grid):
        if floor > theta:
            continue
        metrics: dict[str, float] = evaluate(scores, labels, theta, delta, floor)
        if (
            metrics["wrong_likely_rate"] > MAX_WRONG_LIKELY
            or metrics["unknown_likely_rate"] > MAX_UNKNOWN_LIKELY
            or metrics["known_abstention"] > MAX_KNOWN_ABSTENTION
        ):
            continue
        key: tuple[float, float, float] = (metrics["correct_likely_coverage"], metrics["unknown_rejection"], -metrics["known_abstention"])
        if key > best_key:
            best_key = key
            best = {"theta": theta, "delta": delta, "possible_floor": floor}
    return best


def lookalike_report(scores: numpy.ndarray, labels: list[int], species: list[dict[str, str]]) -> list[dict[str, object]]:
    """For each held-out photo of a lookalike species, report whether the true species beats its lookalike and is in the top 3."""
    index: dict[str, int] = {s["id"]: i for i, s in enumerate(species)}
    rows: list[dict[str, object]] = []
    for row, label in zip(scores, labels):
        if label < 0 or not species[label]["lookalike"]:
            continue
        other: int = index[species[label]["lookalike"]]
        rows.append({
            "species": species[label]["common_name"],
            "lookalike": species[other]["common_name"],
            "true_above_lookalike": bool(row[label] > row[other]),
            "true_in_top3": label in top_k(row, 3),
        })
    return rows


def select_golden(labels: list[int], species: list[dict[str, str]], size: int, negatives: int) -> list[int]:
    """Pick row indices: lookalike species first, then round-robin across species, plus a few negatives."""
    by_species: dict[int, list[int]] = {}
    negative_rows: list[int] = []
    for row, label in enumerate(labels):
        if label < 0:
            negative_rows.append(row)
        else:
            by_species.setdefault(label, []).append(row)
    order: list[int] = sorted(by_species, key=lambda i: (species[i].get("lookalike", "") == "", i))
    picked: list[int] = []
    while len(picked) < size and any(by_species[i] for i in order):
        for i in order:
            if by_species[i] and len(picked) < size:
                picked.append(by_species[i].pop(0))
    return picked + negative_rows[:negatives]


def golden_cases(scores: numpy.ndarray, labels: list[int], names: list[str], species: list[dict[str, str]], params: dict[str, float]) -> dict[str, object]:
    """Return expected species IDs, verdicts and scores for the stratified golden set."""
    cases: list[dict[str, object]] = []
    for row in select_golden(labels, species, size=20, negatives=5):
        top3: list[int] = top_k(scores[row], 3)
        cases.append({
            "photo": names[row],
            "in_catalog": labels[row] >= 0,
            "top3": [species[i]["id"] for i in top3],
            "scores": [round(float(scores[row][i]), 6) for i in top3],
            "verdict": verdict(scores[row], params["theta"], params["delta"], params["possible_floor"]),
        })
    return {"score_tolerance": 0.01, "cases": cases}


def file_sha256(path: pathlib.Path) -> str:
    """Return the SHA-256 hex digest of a file, read in 1 MB chunks."""
    digest: "hashlib._Hash" = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_version(name: str) -> str:
    """Return an installed package's version, or 'not installed'."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def build_manifest(model_path: pathlib.Path, prefix: str, w: float, params: dict[str, float]) -> dict[str, object]:
    """Record everything that must match between the desktop pack and the phone; vectors come from litert-lm."""
    model_sha256: str = file_sha256(model_path)
    return {
        "model_id": "litert-community/embeddinggemma-2-text-vision-440m-litert-lm",
        "litertlm_file": model_path.name,
        "litertlm_sha256": model_sha256,
        "embedding_dim": EMBED_DIM,
        "normalization": "L2",
        "vector_encoding": "float32 little-endian",
        "prompt_template": PROMPT_PREFIXES[prefix].format(label=LABEL_TEMPLATE),
        "image_preprocessing": "JPEG file passed to litert-lm Content.ImageFile; litert-lm scales and patchifies; default vision tokens",
        "vectors_generated_by": "litert-lm",
        "vector_model_ref": model_sha256,
        "desktop_versions": {name: package_version(name) for name in ("litert-lm", "numpy")},
        "desktop_backend": "CPU",
        "android_runtime": "record at G1: MediaPipe tasks version",
        "backend": "record at G1: CPU or GPU",
        "scoring": {"w": w, **params},
        "parity": None,
    }


def main() -> None:
    """Check data, choose prefix and w, tune thresholds, evaluate once on held-out, then write reports."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=pathlib.Path, default=pathlib.Path("data"))
    parser.add_argument("--model", type=pathlib.Path, default=pathlib.Path("model/embeddinggemma-2-text-vision-440m.litertlm"))
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("out"))
    parser.add_argument("--eval-split", default="t", choices=("t", "r"))
    args: argparse.Namespace = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    photo_dir: pathlib.Path = args.data / "photos"
    negatives_dir: pathlib.Path = args.data / "negatives"
    species: list[dict[str, str]] = load_species(args.data / "species.csv")
    check_data(photo_dir, negatives_dir, species)
    embedder: Embedder = Embedder(args.model, args.out / "image_vectors.npz")
    try:
        images, _ = reference_vectors(embedder, species, photo_dir)
        dev_vecs, dev_labels, _ = load_split(embedder, species, photo_dir, negatives_dir, "d")
        test_vecs, test_labels, test_names = load_split(embedder, species, photo_dir, negatives_dir, args.eval_split)
    finally:
        embedder.save()
    prefix, w, text, trials = select_prompt_and_w(embedder, species, images, dev_vecs, dev_labels)
    dev_scores: numpy.ndarray = blended_scores(dev_vecs, text, images, w)
    params: dict[str, float] = tune_thresholds(dev_scores, dev_labels)
    if not params:
        raise SystemExit("No threshold setting met the safety limits; revisit species, photos or grids.")
    test_scores: numpy.ndarray = blended_scores(test_vecs, text, images, w)
    report: dict[str, float] = evaluate(test_scores, test_labels, params["theta"], params["delta"], params["possible_floor"])
    tuning: dict[str, float] = evaluate(dev_scores, dev_labels, params["theta"], params["delta"], params["possible_floor"])
    lookalikes: list[dict[str, object]] = lookalike_report(test_scores, test_labels, species)
    timing: dict[str, float] = {"images_embedded": len(embedder.image_seconds), "mean_image_seconds": float(numpy.mean(embedder.image_seconds)) if embedder.image_seconds else 0.0}
    failures: list[dict[str, object]] = [
        {"photo": n, "label": species[l]["common_name"] if l >= 0 else "unknown", "top3": [species[i]["common_name"] for i in top_k(r, 3)],
         "verdict": verdict(r, params["theta"], params["delta"], params["possible_floor"])}
        for r, l, n in zip(test_scores, test_labels, test_names)
        if (l >= 0 and top_k(r, 1)[0] != l) or (l < 0 and verdict(r, params["theta"], params["delta"], params["possible_floor"]) == "likely")
    ]
    result: dict[str, object] = {"prefix": prefix, "w": w, "params": params, "eval_split": args.eval_split, "held_out": report,
                                 "tuning": tuning, "lookalikes": lookalikes, "failures": failures, "selection_trials": trials, "timing": timing}
    (args.out / "scoring.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (args.out / "golden.json").write_text(json.dumps(golden_cases(test_scores, test_labels, test_names, species, params), indent=2), encoding="utf-8")
    (args.out / "manifest.json").write_text(json.dumps(build_manifest(args.model, prefix, w, params), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("prefix", "w", "params", "held_out")}, indent=2))


if __name__ == "__main__":
    main()
