"""Generate small, graph-compatible ToolNet demonstrations from JSON worlds."""

import argparse
import json
import pickle
import random
import shutil
from pathlib import Path

from src.datapoint import Datapoint, objects as object_catalog

ROOT = Path(__file__).parent
TOOLS = {
    "stool", "tray", "tray2", "lift", "big-tray", "book", "box", "chair",
    "stick", "glue", "tape", "mop", "sponge", "vacuum", "drill",
    "screwdriver", "hammer", "ladder", "trolley", "brick", "blow_dryer",
    "spraypaint", "welder", "toolbox", "wood_cutter", "3d_printer",
}
ALIASES = {"wall": "walls", "warehouse_wall": "wall_warehouse"}
CATALOG = {item["name"]: item for item in object_catalog}


def names_in_world(path):
    data = json.loads(path.read_text())
    return {
        name
        for entity in data.get("entities", [])
        if entity.get("ignore") != "true"
        for name in {entity.get("name"), entity.get("rename", entity.get("name"))}
        if name
    }


def required_objects(path):
    data = json.loads(path.read_text())
    if data.get("goal-objects") is not None:
        values = data["goal-objects"]
    else:
        values = [
            value
            for item in data.get("goals", [])
            for value in (item.get("object"), item.get("target"))
            if value
        ]
    return {ALIASES.get(value, value) for value in values}


def metrics_for_world(path):
    data = json.loads(path.read_text())
    metrics = {}
    for entity in data.get("entities", []):
        if entity.get("ignore") == "true":
            continue
        name = entity.get("name")
        if name in CATALOG:
            orientation = entity.get("orientation") or [0, 0, 0, 1]
            metrics[name] = [entity.get("position", [0, 0, 0]), orientation]
    return metrics


def make_datapoint(world_path, goal_path, demo_index):
    world_name = world_path.stem
    goal_name = goal_path.stem
    metrics = metrics_for_world(world_path)
    available = set(metrics)
    goal_objects = required_objects(goal_path)
    candidates = sorted(available & TOOLS)
    target = candidates[demo_index % len(candidates)] if candidates else sorted(available - {"floor", "walls"})[0]

    datapoint = Datapoint()
    datapoint.world = world_name
    datapoint.goal = goal_name
    datapoint.addSymbolicAction([{"name": "pick", "args": [target]}])
    datapoint.addPoint(
        [0, 0, 0, 0], [], [], False, "Start", {}, metrics, ["light"], [], False, [], [], [], [], []
    )
    datapoint.addPoint(
        [0, 0, 0, 0], [], [], False, ["pick", target], {}, metrics, ["light"], [], False, [], [], [], [], []
    )
    datapoint.time = float(demo_index)
    return datapoint


def compatible_pairs(domain):
    goals = sorted((ROOT / "jsons").glob(f"{domain}_goals/goal[1-8]-*.json"))
    worlds = sorted((ROOT / "jsons").glob(f"{domain}_worlds/world_{domain}*.json"))
    pairs = []
    for goal in goals:
        required = required_objects(goal)
        for world in worlds:
            if required <= {ALIASES.get(name, name) for name in names_in_world(world)}:
                pairs.append((world, goal))
    return pairs


def generate(domains, demos, overwrite):
    dataset_root = ROOT / "dataset"
    if overwrite and dataset_root.exists():
        shutil.rmtree(dataset_root)
    random.seed(7)
    written = []
    for domain in domains:
        pairs = compatible_pairs(domain)
        if not pairs:
            raise RuntimeError(f"No compatible {domain} goal/world pairs found")
        for split, split_pairs in (("train", pairs), ("test", pairs[: max(1, min(2, len(pairs)))])):
            for pair_index, (world, goal) in enumerate(split_pairs):
                folder = dataset_root / split / domain / world.stem
                folder.mkdir(parents=True, exist_ok=True)
                for demo_index in range(demos):
                    path = folder / f"demo_{demo_index}.datapoint"
                    with path.open("wb") as handle:
                        pickle.dump(make_datapoint(world, goal, demo_index), handle)
                    written.append(path)
    print(f"Generated {len(written)} demonstrations in {dataset_root}")
    return written


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worlds", type=int, default=3, help="Maximum worlds per domain")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--domain", choices=("home", "factory", "both"), default="both")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    domains = ["home", "factory"] if args.domain == "both" else [args.domain]
    # Keep selection deterministic and bounded for quick local regeneration.
    global compatible_pairs
    original_pairs = compatible_pairs
    def bounded_pairs(domain):
        return original_pairs(domain)[:args.worlds]
    compatible_pairs = bounded_pairs
    generate(domains, args.demos, args.overwrite)


if __name__ == "__main__":
    main()
