# File name starts with _ to keep it out of typeahead for API users.
# Defer some imports to improve --help performance.
import os
from pathlib import Path
import time
from typing import Optional

import click

from britekit.core.config_loader import get_config
from britekit.core.exceptions import InferenceError
from britekit.core.util import cli_help_from_doc


def analyze(
    cfg_path: Optional[str] = None,
    input_path: str = "",
    output_path: str = "",
    rtype: str = "both",
    min_score: Optional[float] = None,
    num_threads: Optional[int] = None,
    overlap: Optional[float] = None,
    segment_len: Optional[float] = None,
):
    """
    Run inference on audio recordings to detect and classify sounds.

    This command processes audio files or directories and generates predictions
    using a trained model or ensemble. The output can be saved as Audacity labels,
    CSV files, or both.

    Args:
        cfg_path (str): Path to YAML configuration file defining model and inference settings.
        input_path (str): Path to input audio file or directory containing audio files.
        output_path (str): Path to output directory where results will be saved.
        rtype (str): Output format type. Options are "audacity", "csv", or "both".
        min_score (float, optional): Confidence threshold. Predictions below this value are excluded.
        num_threads (int, optional): Number of threads to use for processing. Default is 3.
        overlap (float, optional): Spectrogram overlap in seconds for sliding window analysis.
        segment_len (float, optional): Fixed segment length in seconds. If specified, labels are
                                     fixed-length; otherwise they are variable-length.
    """

    # defer slow imports to improve --help performance
    import logging
    from britekit.core import util
    from britekit.core.analyzer import Analyzer

    util.set_logging()
    cfg = get_config(cfg_path)
    try:
        if rtype not in {"audacity", "csv", "both"}:
            logging.error(f"Error. invalid rtype value: {rtype}")
            quit()

        if output_path:
            if not os.path.exists(output_path):
                os.makedirs(output_path)
        else:
            if os.path.isdir(input_path):
                output_path = input_path
            else:
                output_path = str(Path(input_path).parent)

        if min_score is not None:
            cfg.infer.min_score = min_score

        if num_threads is not None:
            cfg.infer.num_threads = num_threads

        if overlap is not None:
            cfg.infer.overlap = overlap

        if segment_len is not None:
            cfg.infer.segment_len = segment_len

        device = util.get_device()
        logging.info(f"Using {device.upper()} for inference")

        start_time = time.time()
        analyzer = Analyzer()
        analyzer.run(input_path, output_path, rtype)
        elapsed_time = util.format_elapsed_time(start_time, time.time())
        logging.info(f"Elapsed time = {elapsed_time}")
    except InferenceError as e:
        logging.error(e)


@click.command(
    name="analyze",
    short_help="Run inference.",
    help=cli_help_from_doc(analyze.__doc__),
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
    "-i",
    "--input",
    "input_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    help="Path to input directory or recording.",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Path to output directory (optional, defaults to input directory).",
)
@click.option(
    "-r",
    "--rtype",
    type=str,
    default="both",
    help='Output format type. Options are "audacity", "csv", or "both". Default="both".',
)
@click.option(
    "-m",
    "--min_score",
    "min_score",
    type=float,
    help="Threshold, so predictions lower than this value are excluded.",
)
@click.option(
    "--threads",
    "num_threads",
    type=int,
    help="Number of threads (optional, default = 3)",
)
@click.option(
    "--overlap",
    "overlap",
    type=float,
    help="Number of threads (optional, default = 3)",
)
@click.option(
    "--seg",
    "segment_len",
    type=float,
    help="Optional segment length in seconds. If specified, labels are fixed-length. Otherwise they are variable-length.",
)
def _analyze_cmd(
    cfg_path: str,
    input_path: str,
    output_path: str,
    rtype: str,
    min_score: Optional[float] = None,
    num_threads: Optional[int] = None,
    overlap: Optional[float] = None,
    segment_len: Optional[float] = None,
):
    analyze(
        cfg_path,
        input_path,
        output_path,
        rtype,
        min_score,
        num_threads,
        overlap,
        segment_len,
    )
