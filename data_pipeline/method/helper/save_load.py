# io_parquet.py  ───────────────  DROP-IN MODULE  ───────────────
from __future__ import annotations

import datetime as dt
import gzip
import json
from pathlib import Path

"""
Save and load agents for simulation in JSON format
- Save by timestamp and keep 5 latest files
- Load the file with the newest timestamp

Why JSON?
- Easy to dump dictionary data
- Little compatibility issues
- Can convert to Parquet in the future
"""

KEEP_LATEST = 5  # how many checkpoint files to retain
PATTERN = "agents_*.jsonl.gz"  # assumes “agents_YYYYMMDD_HHMMSS.parquet”
test_file = "./data_source/agm_agent_save_test"
prod_file = "./data_source/agm_agent_save"


def save_agents_to_json(
    model,
    keep_last: int = KEEP_LATEST,
    mode="test",
) -> Path:
    """
    Dump all agents to Parquet and enforce a file-retention policy.
    Returns the path of the newly written checkpoint.
    Input:
        - model -> simulation model instance
        - root -> file_path to save the agent state
    """

    if mode.lower() == "test":
        root = test_file
    else:
        root = prod_file

    print("Saving agents.......")
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")

    file_path = Path(root) / f"agents_{ts}.jsonl.gz"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with gzip.open(file_path, "wt", encoding="utf-8", compresslevel=5) as f:
        for ag in model.schedule.agents:
            row = ag.to_row()
            # Check
            bad = [
                (k, type(v))
                for k, v in row.items()
                if not isinstance(v, (str, int, float, bool, list, dict))
            ]
            if not bad:
                file_path.unlink()
                print(f"Non-serializable items detected: {bad} for agent: {row}")
                raise AssertionError

            f.write(json.dumps(row, separators=(",", ":")) + "\n")

    print("Saving successful!")
    # Clean up old files (leave newest N)
    files = sorted(
        file_path.glob(PATTERN), key=lambda p: p.stat().st_mtime, reverse=True
    )  # newest → oldest
    for old in files[keep_last:]:
        old.unlink(missing_ok=True)

    return file_path


def load_agents_from_latest_json(model, model_agent_classes, mode="test"):
    """
    Find the newest agents_*.parquet, rebuild every agent, and register them with model.schedule.
    Returns the path that was loaded, or None.
    """
    if mode.lower() == "test":
        root = test_file
    else:
        root = prod_file

    agent_ids = []
    folder_path = Path(root)

    if not folder_path.exists():
        return None, []

    if not any(folder_path.iterdir()):
        return None, []

    try:
        latest_file = max(
            folder_path.glob(PATTERN), key=lambda p: p.stat().st_mtime
        )  # Redudancy for robust
    except ValueError:
        print("No saved files yet")
        return None, []

    print("Loading agents......")
    with gzip.open(latest_file, "rt", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            agent_type_str = rec.pop("type")
            cls = model_agent_classes.get(agent_type_str)

            if cls is None:
                print("Class object is missing. Did you pass in the class_registry?")

            ag = cls.from_row(rec)
            agent_ids.append(getattr(ag, "unique_id", None))
            model.schedule.add(ag)
    print("Agents loaded!")

    return latest_file, agent_ids
