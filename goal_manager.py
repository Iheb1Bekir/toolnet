import json
import re
from datetime import datetime
from pathlib import Path


USER_GOALS_DIR = Path("jsons/user_goals")


def list_user_goals():
    USER_GOALS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(str(path).replace("\\", "/") for path in USER_GOALS_DIR.glob("*.json"))


def load_user_goal(path):
    normalized = Path(path)
    if normalized.parent != USER_GOALS_DIR or normalized.suffix != ".json":
        raise ValueError("Invalid user goal path")
    if not normalized.exists():
        raise FileNotFoundError(path)
    with normalized.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    actions = data.get("actions")
    if not isinstance(actions, list) or not all(
        isinstance(action, dict) and isinstance(action.get("name"), str)
        and isinstance(action.get("args", []), list) for action in actions
    ):
        raise ValueError("User goal contains invalid actions")
    return data


def save_user_goal(name, world, actions):
    clean_name = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip()).strip("._-")
    if not clean_name:
        raise ValueError("Goal name is required")
    if not isinstance(actions, list) or not actions:
        raise ValueError("At least one action is required")
    normalized_actions = []
    for action in actions:
        if not isinstance(action, dict) or not isinstance(action.get("name"), str):
            raise ValueError("Invalid action")
        arguments = action.get("args", [])
        if not isinstance(arguments, list):
            raise ValueError("Invalid action arguments")
        normalized_actions.append({"name": action["name"], "args": arguments})

    USER_GOALS_DIR.mkdir(parents=True, exist_ok=True)
    path = USER_GOALS_DIR / f"{clean_name}.json"
    data = {
        "name": name.strip(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "world": world,
        "actions": normalized_actions,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    return str(path).replace("\\", "/"), data
