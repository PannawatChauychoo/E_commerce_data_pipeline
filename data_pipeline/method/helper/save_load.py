# io_parquet.py  ───────────────  DROP-IN MODULE  ───────────────
from __future__ import annotations

import datetime as dt
import gzip
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable

from helper.datetime_conversion import dt_to_str, str_to_dt

"""
Save and load agents for simulation in JSON format
- Save by timestamp and keep 5 newest files
- Load the file with the newest timestamp

Why JSON?
- Easy to dump dictionary data
- Little compatibility issues
- Can convert to Parquet in the future
"""

KEEP_newest = 5  # how many checkpoint files to retain
PATTERN = "agent_*.jsonl.gz"  # assumes “agents_YYYYMMDD_HHMMSS.parquet”
METADATA_PATTERN = "metadata.json"

test_file = "./data_source/agm_agent_save_test"
prod_file = "./data_source/agm_agent_save"


def save_agent(root: Path, agents: Iterable[Any], run_id: str) -> Path:
    """
    Saving the agent states into the folder
    """
    print("Saving agents.......")
    agent_file_path = root / f"agent_{run_id}.jsonl.gz"
    agent_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Checking if there is saved files already
    with gzip.open(agent_file_path, "wt", encoding="utf-8", compresslevel=5) as f:
        for agent in agents:
            row = agent.to_row()
            if not isinstance(row, dict):
                raise TypeError("agent.to_row() must return a dict")
            json.dumps(
                row
            )  # will raise if not serializable            f.write(json.dumps(row, separators=(",", ":")) + "\n")
            f.write(json.dumps(row, separators=(",", ":")) + "\n")

    return agent_file_path


def save_metadata(
    root: Path, run_id: str, finished_sim_date: dt.datetime, date_simulated: int
) -> Path:
    """
    Saving metadata by adding it to the file
    """
    print("Saving meta data...")
    meta_data = {
        "start_sim_date": dt_to_str(finished_sim_date - dt.timedelta(date_simulated)),
        "finished_sim_date": dt_to_str(finished_sim_date),
        "actual_date": dt.datetime.now(),
        "run_id": run_id,
        "date_simulated": date_simulated,
    }
    meta_file_path = root / METADATA_PATTERN
    with open(meta_file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(meta_data, separators=(",", ":"), default=str) + "\n")

    return meta_file_path


def save_agents(
    model,
    keep_last: int = KEEP_newest,
    mode="test",
):
    """ "
    Dump all agents to Parquet and enforce a file-retention policy.
    Returns the path of the newly written checkpoint.
    Input:
        - model -> simulation model instance
        - root -> file_path to save the agent state
    """

    if mode.lower() == "test":
        root = Path(test_file)
    else:
        root = Path(prod_file)

    run_id = model.run_id
    ts = dt_to_str(dt.datetime.now(dt.timezone.utc))
    file_path = root / f"run_ts={ts}"

    saved_agent_path = save_agent(
        file_path, agents=model.schedule.agents, run_id=run_id
    )
    metadata_path = save_metadata(
        file_path,
        run_id=run_id,
        finished_sim_date=model.current_date,
        date_simulated=model.max_steps,
    )

    print("Saving successful!")

    # Clean up old files (leave newest N)
    files = sorted(
        (p for p in root.glob("run_ts=*") if p.is_dir()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )  # newest → oldest
    for old in files[keep_last:]:
        shutil.rmtree(old, ignore_errors=True)

    # Checking if there are <= 5 folders and there are 2 files in each folder
    existing_folders = [f for f in root.iterdir() if f.is_dir()]
    assert len(existing_folders) <= 5, print(
        f"There are more than 5 checkpoint folders at {len(existing_folders)} folders"
    )

    for folder in existing_folders:
        agent_check = next(folder.glob(PATTERN), None)
        assert agent_check is not None, print(
            f"Agent checkpoint not found in {str(folder)}"
        )
        meta_data_check = next(folder.glob(METADATA_PATTERN), None)
        assert meta_data_check is not None, print(
            f"Metadata not found in {str(folder)}"
        )

    return (saved_agent_path, metadata_path)


def load_agents_from_newest(model, model_agent_classes, mode="test"):
    """
    Find the newest agents_*.jsonl.gz, rebuild every agent, and register them with model.schedule.
    Start from the metadata date.
    Returns the path that was loaded, or None.
    """
    if mode.lower() == "test":
        root = test_file
    else:
        root = prod_file

    agent_ids = []
    folder_path = Path(root)

    if not folder_path.exists():
        return None, [], {}

    runs = [p for p in folder_path.glob("run_ts=*") if p.is_dir()]
    if not runs:
        return None, [], {}

    newest_run_folder = max(runs)

    print("Loading agents...")
    metadata_path = next(newest_run_folder.glob(METADATA_PATTERN), None)
    if metadata_path is None:
        raise FileNotFoundError(f"No metadata found in {str(newest_run_folder)}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = [json.loads(line) for line in f]
    newest_metadata = max(metadata, key=lambda x: x["finished_sim_date"])
    newest_runid = str(newest_metadata["run_id"])

    newest_agent_file = PATTERN.replace("*", newest_runid)
    agent_folder_path = next(newest_run_folder.glob(newest_agent_file), None)
    print(f"Loading {newest_agent_file} with {newest_metadata}...")
    if agent_folder_path is None:
        raise FileNotFoundError(
            f"No agent file found in {str(newest_run_folder)} with {newest_runid} id"
        )

    with gzip.open(agent_folder_path, "rt", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            agent_type_str = rec.pop("type")
            cls = model_agent_classes.get(agent_type_str)

            if cls is None:
                print("Class object is missing. Did you pass in the class_registry?")

            ag = cls.from_row(rec)
            agent_ids.append(getattr(ag, "unique_id", None))
            model.schedule.add(ag)

    print("Agents loaded successfully!")

    return newest_agent_file, agent_ids, newest_metadata
