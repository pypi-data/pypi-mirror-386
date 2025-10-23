# File name starts with _ to keep it out of typeahead for API users.
# Defer some imports to improve --help performance.
import logging
from pathlib import Path
from typing import Optional

import click

from britekit.core.config_loader import get_config
from britekit.core import util


def pickle(
    cfg_path: Optional[str]=None,
    classes_path: Optional[str]=None,
    db_path: Optional[str]=None,
    output_path: Optional[str]=None,
    root_dir: str="",
    max_per_class: Optional[int]=None,
    spec_group: Optional[str]=None,
) -> None:
    """
    Convert database spectrograms to a pickle file for use in training.

    This command extracts spectrograms from the training database and saves them in a pickle file
    that can be efficiently loaded during model training. It can process all classes in the database
    or specific classes specified by a CSV file.

    Args:
        cfg_path (str, optional): Path to YAML file defining configuration overrides.
        classes_path (str, optional): Path to CSV file containing class names to include.
                                     If omitted, includes all classes in the database.
        db_path (str, optional): Path to the training database. Defaults to cfg.train.train_db.
        output_path (str, optional): Output pickle file path. Defaults to "data/training.pkl".
        max_per_class (int, optional): Maximum number of spectrograms to include per class.
        spec_group (str): Spectrogram group name to extract from. Defaults to 'default'.
    """
    from britekit.core.pickler import Pickler

    cfg = get_config(cfg_path)
    if db_path is None:
        db_path = cfg.train.train_db

    if output_path is None:
        output_path = str(Path(root_dir) / "data" / "training.pkl")

    pickler = Pickler(db_path, output_path, classes_path, max_per_class, spec_group)
    pickler.pickle()


@click.command(
    name="pickle",
    short_help="Convert database records to a pickle file for use in training.",
    help=util.cli_help_from_doc(pickle.__doc__),
)
@click.option(
    "-c",
    "--cfg",
    "cfg_path",
    type=click.Path(exists=True),
    required=False,
    help="Path to YAML file defining config overrides.",
)
@click.option(
    "--classes",
    "classes_path",
    required=False,
    help="Path to CSV containing class names to pickle (optional). Default is all classes.",
)
@click.option(
    "-d", "--db", "db_path", required=False, help="Path to the training database."
)
@click.option(
    "-o",
    "--output",
    "output_path",
    required=False,
    help='Output file path. Default is "data/training.pkl".',
)
@click.option(
    "--root",
    "root_dir",
    default=".",
    type=click.Path(file_okay=False),
    help="Root directory containing data directory.",
)
@click.option(
    "-m",
    "--max",
    "max_per_class",
    required=False,
    type=int,
    help="Maximum spectrograms per class.",
)
@click.option(
    "--sgroup",
    "spec_group",
    required=False,
    default="default",
    help="Spectrogram group name. Defaults to 'default'.",
)
def _pickle_cmd(
    cfg_path: Optional[str],
    classes_path: Optional[str],
    db_path: Optional[str],
    output_path: Optional[str],
    root_dir: str,
    max_per_class: Optional[int],
    spec_group: Optional[str],
) -> None:
    util.set_logging()
    pickle(
        cfg_path,
        classes_path,
        db_path,
        output_path,
        root_dir,
        max_per_class,
        spec_group,
    )
