"""Scratch: pull CC0/CC BY research-grade photos from iNaturalist, one photo per observation, named per Phase 0."""
import csv
import pathlib
import sys
import time

import requests
import requests.adapters
import urllib3.util.retry

API: str = "https://api.inaturalist.org/v1/observations"
FLORIDA_PLACE_ID: int = 21
SPLIT_PLAN: tuple[str, ...] = ("p",) * 6 + ("d",) * 2 + ("t",) * 2 + ("r",)
NEGATIVE_ANIMALS: tuple[str, ...] = (
    "Lynx rufus", "Dasypus novemcinctus", "Haliaeetus leucocephalus", "Antigone canadensis", "Pandion haliaetus",
    "Cyanocitta cristata", "Cardinalis cardinalis", "Terrapene carolina", "Micrurus fulvius", "Odocoileus virginianus",
    "Sylvilagus palustris", "Ardea herodias", "Platalea ajaja", "Nannopterum auritum", "Quiscalus major",
    "Columba livia", "Hemidactylus mabouia", "Trachemys scripta", "Pseudemys nelsoni", "Nerodia fasciata",
    "Pantherophis guttatus", "Lithobates catesbeianus", "Danaus plexippus", "Dryas iulia", "Argiope aurantia",
    "Gasteracantha cancriformis", "Felis catus", "Canis familiaris", "Ctenosaura similis", "Basiliscus vittatus",
)
NEGATIVE_NON_ANIMALS: tuple[str, ...] = (
    "Cocos nucifera", "Sabal palmetto", "Bougainvillea", "Hibiscus", "Ficus aurea",
    "Rhizophora mangle", "Quercus virginiana", "Delonix regia", "Tillandsia usneoides", "Nymphaea odorata",
    "Ipomoea pes-caprae", "Serenoa repens", "Lantana camara", "Bursera simaruba", "Pinus elliottii",
    "Ganoderma", "Trametes sanguinea", "Cladonia", "Sargassum", "Pontederia crassipes",
)
SESSION: requests.Session = requests.Session()
SESSION.headers["User-Agent"] = "wild-miami-hackathon-scratch/0.1"
SESSION.mount("https://", requests.adapters.HTTPAdapter(max_retries=urllib3.util.retry.Retry(total=6, backoff_factor=2, status_forcelist=(429, 500, 502, 503, 504))))


def query(taxon_name: str, place: bool, per_page: int) -> list[dict[str, object]]:
    """Return research-grade observations with CC0/CC BY photos for a taxon, optionally limited to Florida."""
    params: dict[str, object] = {
        "taxon_name": taxon_name,
        "quality_grade": "research",
        "photos": "true",
        "photo_license": "cc0,cc-by",
        "per_page": per_page,
        "order_by": "votes",
    }
    if place:
        params["place_id"] = FLORIDA_PLACE_ID
    time.sleep(1.1)
    response: requests.Response = SESSION.get(API, params=params, timeout=60)
    response.raise_for_status()
    return response.json()["results"]


def pick(taxon_name: str, count: int) -> list[dict[str, object]]:
    """Pick up to `count` observations from distinct observers, widening the search when Florida results are thin."""
    attempts: list[tuple[str, bool]] = [(taxon_name, True), (taxon_name, False)]
    if len(taxon_name.split()) > 2:
        short: str = " ".join(taxon_name.split()[:2])
        attempts += [(short, True), (short, False)]
    picked: list[dict[str, object]] = []
    seen_obs: set[int] = set()
    seen_users: set[int] = set()
    for name, place in attempts:
        for obs in query(name, place, per_page=60):
            taxon: str = str(obs["taxon"]["name"])
            if " × " in taxon or not (taxon == name or taxon.startswith(name + " ")):
                continue
            user: int = obs["user"]["id"]
            if obs["id"] in seen_obs or user in seen_users:
                continue
            photo: dict[str, object] | None = next(
                (p for p in obs["photos"] if p.get("license_code") in ("cc0", "cc-by")), None
            )
            if photo is None:
                continue
            seen_obs.add(obs["id"])
            seen_users.add(user)
            picked.append({"obs": obs, "photo": photo})
            if len(picked) >= count:
                return picked
    return picked


def download(photo: dict[str, object], target: pathlib.Path) -> None:
    """Download the 'large' rendition of a photo unless it already exists."""
    if target.exists():
        return
    url: str = str(photo["url"]).replace("/square.", "/large.")
    response: requests.Response = SESSION.get(url, timeout=60)
    response.raise_for_status()
    target.write_bytes(response.content)


def credit_row(file_name: str, label: str, split: str, item: dict[str, object]) -> dict[str, str]:
    """Build one attribution record: photographer, license and source URL."""
    obs: dict[str, object] = item["obs"]
    photo: dict[str, object] = item["photo"]
    return {
        "file": file_name,
        "label": label,
        "split": split,
        "observation_id": str(obs["id"]),
        "taxon": str(obs["taxon"]["name"]),
        "photographer": str(obs["user"].get("name") or obs["user"]["login"]),
        "license": str(photo["license_code"]),
        "attribution": str(photo.get("attribution", "")),
        "source_url": f"https://www.inaturalist.org/observations/{obs['id']}",
    }


def main(root: pathlib.Path) -> None:
    """Fetch 11 photos per catalog species and 1 per negative taxon; write credits.csv."""
    photo_dir: pathlib.Path = root / "photos"
    negatives_dir: pathlib.Path = root / "negatives"
    photo_dir.mkdir(parents=True, exist_ok=True)
    negatives_dir.mkdir(parents=True, exist_ok=True)
    credits: list[dict[str, str]] = []
    with (root / "species.csv").open(newline="", encoding="utf-8") as handle:
        species: list[dict[str, str]] = list(csv.DictReader(handle))
    for s in species:
        items: list[dict[str, object]] = pick(s["scientific_name"], len(SPLIT_PLAN))
        print(f"{s['id']:>2} {s['common_name']}: {len(items)} photos", flush=True)
        for split, item in zip(SPLIT_PLAN, items):
            name: str = f"{s['id']}__{split}__{item['obs']['id']}.jpg"
            download(item["photo"], photo_dir / name)
            credits.append(credit_row(name, s["id"], split, item))
    negatives: list[str] = list(NEGATIVE_ANIMALS) + list(NEGATIVE_NON_ANIMALS)
    for index, taxon in enumerate(negatives):
        items = pick(taxon, 1)
        if not items:
            print(f"negative {taxon}: none", flush=True)
            continue
        split = "d" if index % 2 == 0 else "t"
        name = f"neg__{split}__{items[0]['obs']['id']}.jpg"
        download(items[0]["photo"], negatives_dir / name)
        credits.append(credit_row(name, "neg", split, items[0]))
    print(f"negatives: {sum(1 for c in credits if c['label'] == 'neg')}", flush=True)
    with (root / "credits.csv").open("w", newline="", encoding="utf-8") as handle:
        writer: csv.DictWriter = csv.DictWriter(handle, fieldnames=list(credits[0]))
        writer.writeheader()
        writer.writerows(credits)


if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]))
