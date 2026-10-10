"""Scratch pack builder: SQLite schema, export from a reviewed safety sheet, parity recording and validation."""
import argparse
import csv
import json
import pathlib
import sqlite3

import numpy

EMBED_DIM: int = 768
SCHEMA: str = """
CREATE TABLE species (
  id                  INTEGER PRIMARY KEY,
  common_name         TEXT NOT NULL,
  scientific_name     TEXT NOT NULL,
  taxon_group         TEXT NOT NULL CHECK (taxon_group IN ('bird','reptile','amphibian','mammal','invertebrate')),
  origin_status       TEXT NOT NULL CHECK (origin_status IN ('native','nonnative','unknown')),
  conservation_status TEXT NOT NULL CHECK (conservation_status IN ('none','threatened','endangered','unknown')),
  risk                TEXT NOT NULL CHECK (risk IN ('low','caution','danger')),
  default_guidance    TEXT NOT NULL CHECK (default_guidance IN ('observe','keep_distance')),
  source_url          TEXT NOT NULL CHECK (source_url <> ''),
  verified_at         TEXT NOT NULL CHECK (verified_at <> ''),
  blurb               TEXT NOT NULL CHECK (length(blurb) <= 200),
  photo_credit        TEXT NOT NULL CHECK (photo_credit <> ''),
  CHECK (risk = 'low' OR default_guidance = 'keep_distance')
);
CREATE TABLE incident_option (
  species_id INTEGER NOT NULL REFERENCES species(id) ON DELETE CASCADE,
  incident   TEXT NOT NULL CHECK (incident IN ('injured_or_dead','safety_concern','reportable_sighting','violation')),
  action     TEXT NOT NULL CHECK (action IN ('call_gator_hotline','report_wildlife_alert','report_nonnative')),
  PRIMARY KEY (species_id, incident)
);
CREATE TABLE prototype (
  species_id INTEGER NOT NULL REFERENCES species(id) ON DELETE CASCADE,
  kind       TEXT NOT NULL CHECK (kind IN ('text','image')),
  vec        BLOB NOT NULL CHECK (length(vec) = 3072)
);
CREATE TABLE pack_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""
SPECIES_COLUMNS: tuple[str, ...] = (
    "id", "common_name", "scientific_name", "taxon_group", "origin_status", "conservation_status",
    "risk", "default_guidance", "source_url", "verified_at", "blurb", "photo_credit",
)


def read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV into a list of row dicts."""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def vector_blob(vec: numpy.ndarray) -> bytes:
    """Encode one vector as float32 little-endian bytes after shape, finite and unit-norm checks."""
    array: numpy.ndarray = numpy.asarray(vec, dtype="<f4")
    if array.shape != (EMBED_DIM,) or not bool(numpy.all(numpy.isfinite(array))):
        raise ValueError("Vector has the wrong shape or non-finite values")
    if abs(float(numpy.linalg.norm(array)) - 1.0) > 1e-3:
        raise ValueError("Vector is not unit-normalized")
    return array.tobytes()


def create_db(db_path: pathlib.Path, safety_sheet: pathlib.Path, incidents: pathlib.Path) -> None:
    """Create a fresh database and load the human-reviewed species and incident rows; CHECKs reject blanks."""
    if db_path.exists():
        db_path.unlink()
    connection: sqlite3.Connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
        for row in read_csv(safety_sheet):
            connection.execute(
                f"INSERT INTO species ({', '.join(SPECIES_COLUMNS)}) VALUES ({', '.join('?' * len(SPECIES_COLUMNS))})",
                tuple(row[c].strip() for c in SPECIES_COLUMNS),
            )
        for row in read_csv(incidents):
            if not row.get("fwc_source_url", "").strip() or not row.get("reviewed_at", "").strip():
                raise ValueError(f"Incident option not reviewed: {row['species_id']} {row['incident']}")
            connection.execute(
                "INSERT INTO incident_option (species_id, incident, action) VALUES (?, ?, ?)",
                (int(row["species_id"]), row["incident"].strip(), row["action"].strip()),
            )
        connection.commit()
    finally:
        connection.close()


def embed_prompts(model_path: pathlib.Path, prompts: list[str]) -> numpy.ndarray:
    """Embed text prototypes with litert-lm from the same .litertlm file (needs a machine that can run the model)."""
    import litert_lm  # deferred so validate/parity commands run without the runtime

    engine: litert_lm.EmbeddingEngine = litert_lm.EmbeddingEngine(str(model_path), backend=litert_lm.Backend.CPU())
    options: litert_lm.EmbeddingOptions = litert_lm.EmbeddingOptions(normalize=True)
    rows: list[numpy.ndarray] = []
    for prompt in prompts:
        vec: numpy.ndarray = numpy.asarray(engine.compute_embedding(prompt.strip(), options).embedding, dtype="<f4")
        rows.append(vec / numpy.linalg.norm(vec))
    return numpy.stack(rows)


def export_pack(db_path: pathlib.Path, species: list[dict[str, str]], text: numpy.ndarray, image_cache: dict[str, numpy.ndarray], photo_dir: pathlib.Path, manifest: dict[str, object], pack_version: int) -> None:
    """Write prototypes in deterministic order (species id, text, references by file name) plus the manifest."""
    connection: sqlite3.Connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("DELETE FROM prototype")
        for index, s in enumerate(species):
            species_id: int = int(s["id"])
            connection.execute("INSERT INTO prototype (species_id, kind, vec) VALUES (?, 'text', ?)", (species_id, vector_blob(text[index])))
            for ref in sorted(photo_dir.glob(f"{species_id}__p__*.jpg")):
                connection.execute("INSERT INTO prototype (species_id, kind, vec) VALUES (?, 'image', ?)", (species_id, vector_blob(image_cache[ref.name])))
        connection.execute("INSERT OR REPLACE INTO pack_meta (key, value) VALUES ('manifest', ?)", (json.dumps(manifest, sort_keys=True),))
        connection.execute(f"PRAGMA user_version = {int(pack_version)}")
        connection.commit()
    finally:
        connection.close()


def record_parity(db_path: pathlib.Path, device: str, android_runtime: str, backend: str, min_cosine: float, top3_identical: int, photos: int, checked_at: str, checked_by: str) -> None:
    """Write G1 parity evidence into the pack manifest, bound to the pack's model SHA-256 and pack version."""
    connection: sqlite3.Connection = sqlite3.connect(db_path)
    try:
        manifest: dict[str, object] = json.loads(connection.execute("SELECT value FROM pack_meta WHERE key = 'manifest'").fetchone()[0])
        pack_version: int = connection.execute("PRAGMA user_version").fetchone()[0]
        manifest["android_runtime"] = android_runtime
        manifest["backend"] = backend
        manifest["parity"] = {
            "litertlm_sha256": manifest["litertlm_sha256"], "pack_version": pack_version, "device": device,
            "android_runtime": android_runtime, "backend": backend, "photos": photos, "min_cosine": min_cosine,
            "top3_identical": top3_identical, "checked_at": checked_at, "checked_by": checked_by,
        }
        connection.execute("UPDATE pack_meta SET value = ? WHERE key = 'manifest'", (json.dumps(manifest, sort_keys=True),))
        connection.commit()
    finally:
        connection.close()


def check_manifest(manifest: dict[str, object], pack_version: int, require_parity: bool) -> list[str]:
    """Check vector provenance and, in release mode, that G1 parity evidence matches this model and pack."""
    problems: list[str] = []
    if manifest.get("vectors_generated_by") == "litert-lm" and manifest.get("vector_model_ref") != manifest.get("litertlm_sha256"):
        problems.append("litert-lm vectors were not generated from the shipped .litertlm file")
    if not require_parity:
        return problems
    parity: object = manifest.get("parity")
    if not isinstance(parity, dict):
        return problems + ["parity block missing (run G1 and record-parity)"]
    if parity.get("litertlm_sha256") != manifest.get("litertlm_sha256"):
        problems.append("parity was measured against a different model file")
    if parity.get("pack_version") != pack_version:
        problems.append("parity was measured against a different pack version")
    if float(parity.get("min_cosine", 0.0)) < 0.95:
        problems.append("parity minimum cosine below 0.95")
    if int(parity.get("top3_identical", 0)) != int(parity.get("photos", -1)):
        problems.append("parity top-3 rankings differ")
    return problems


def validate_pack(db_path: pathlib.Path, expected_species: int, require_parity: bool) -> list[str]:
    """Return every problem found in the pack; empty means pass. Release mode sets require_parity=True."""
    problems: list[str] = []
    connection: sqlite3.Connection = sqlite3.connect(db_path)
    try:
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            problems.append("foreign key violations")
        pack_version: int = connection.execute("PRAGMA user_version").fetchone()[0]
        if pack_version < 1:
            problems.append("user_version is still 0 (fixture)")
        count: int = connection.execute("SELECT COUNT(*) FROM species").fetchone()[0]
        if count != expected_species:
            problems.append(f"expected {expected_species} species, found {count}")
        missing: list[tuple[int]] = connection.execute(
            "SELECT id FROM species s WHERE "
            "NOT EXISTS (SELECT 1 FROM prototype p WHERE p.species_id = s.id AND p.kind = 'text') OR "
            "NOT EXISTS (SELECT 1 FROM prototype p WHERE p.species_id = s.id AND p.kind = 'image')"
        ).fetchall()
        if missing:
            problems.append(f"species missing text or image prototypes: {[r[0] for r in missing]}")
        for (blob,) in connection.execute("SELECT vec FROM prototype"):
            vec: numpy.ndarray = numpy.frombuffer(blob, dtype="<f4")
            if not bool(numpy.all(numpy.isfinite(vec))) or abs(float(numpy.linalg.norm(vec)) - 1.0) > 1e-3:
                problems.append("prototype vector not finite or not unit-norm")
                break
        unprotected: list[tuple[int]] = connection.execute(
            "SELECT id FROM species s WHERE conservation_status IN ('threatened', 'endangered') AND "
            "NOT EXISTS (SELECT 1 FROM incident_option o WHERE o.species_id = s.id AND o.incident = 'injured_or_dead')"
        ).fetchall()
        if unprotected:
            problems.append(f"listed species without an injured_or_dead option: {[r[0] for r in unprotected]}")
        row: tuple[str] | None = connection.execute("SELECT value FROM pack_meta WHERE key = 'manifest'").fetchone()
        if row is None:
            problems.append("manifest missing")
        else:
            problems.extend(check_manifest(json.loads(row[0]), pack_version, require_parity))
    finally:
        connection.close()
    return problems


def build(args: argparse.Namespace) -> None:
    """Create the DB from the safety sheet, embed text prototypes, export, then validate in build mode."""
    manifest: dict[str, object] = json.loads((args.out / "manifest.json").read_text(encoding="utf-8"))
    species: list[dict[str, str]] = sorted(read_csv(args.data / "species.csv"), key=lambda r: int(r["id"]))
    prompts: list[str] = [str(manifest["prompt_template"]).format(**s) for s in species]
    image_cache: dict[str, numpy.ndarray] = dict(numpy.load(args.out / "image_vectors.npz"))
    create_db(args.db, args.data / "safety_sheet.csv", args.data / "incident_options.csv")
    export_pack(args.db, species, embed_prompts(args.model, prompts), image_cache, args.data / "photos", manifest, args.pack_version)
    report(validate_pack(args.db, len(species), require_parity=False))


def report(problems: list[str]) -> None:
    """Print the validator verdict and exit non-zero on any problem."""
    if problems:
        raise SystemExit("Pack failed validation: " + "; ".join(problems))
    print("Pack passed validation")


def main() -> None:
    """CLI: build | validate [--release] | record-parity."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description=__doc__)
    sub: argparse._SubParsersAction = parser.add_subparsers(dest="command", required=True)
    b: argparse.ArgumentParser = sub.add_parser("build")
    b.add_argument("--data", type=pathlib.Path, default=pathlib.Path("data"))
    b.add_argument("--out", type=pathlib.Path, default=pathlib.Path("out"))
    b.add_argument("--model", type=pathlib.Path, default=pathlib.Path("model/embeddinggemma-2-text-vision-440m.litertlm"))
    b.add_argument("--db", type=pathlib.Path, default=pathlib.Path("out/wildlife.db"))
    b.add_argument("--pack-version", type=int, required=True)
    v: argparse.ArgumentParser = sub.add_parser("validate")
    v.add_argument("--db", type=pathlib.Path, default=pathlib.Path("out/wildlife.db"))
    v.add_argument("--species", type=int, default=30)
    v.add_argument("--release", action="store_true")
    r: argparse.ArgumentParser = sub.add_parser("record-parity")
    r.add_argument("--db", type=pathlib.Path, default=pathlib.Path("out/wildlife.db"))
    for name in ("device", "android-runtime", "backend", "checked-at", "checked-by"):
        r.add_argument(f"--{name}", required=True)
    r.add_argument("--min-cosine", type=float, required=True)
    r.add_argument("--top3-identical", type=int, required=True)
    r.add_argument("--photos", type=int, default=10)
    args: argparse.Namespace = parser.parse_args()
    if args.command == "build":
        build(args)
    elif args.command == "validate":
        report(validate_pack(args.db, args.species, require_parity=args.release))
    else:
        record_parity(args.db, args.device, args.android_runtime, args.backend, args.min_cosine, args.top3_identical, args.photos, args.checked_at, args.checked_by)


if __name__ == "__main__":
    main()
