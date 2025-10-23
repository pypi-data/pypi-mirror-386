from .__about__ import __version__

__all__ = ["__version__"]

# SPDX-FileCopyrightText: 2025-present Jan Huus <jhuus1@gmail.com>
#
# SPDX-License-Identifier: MIT

# This lets you do "from britekit import __version__" anywhere
try:
    from .__about__ import __version__  # type: ignore
except Exception:
    try:
        from importlib.metadata import version as _pkg_version  # type: ignore
        __version__ = _pkg_version("britekit")  # type: ignore[assignment]
    except Exception:
        __version__ = "0.0.0"

from britekit import commands
from britekit.core import util
from britekit.core.analyzer import Analyzer
from britekit.core.audio import Audio
from britekit.core.base_config import BaseConfig
from britekit.core.config_loader import get_config
from britekit.core.pickler import Pickler
from britekit.core.predictor import Predictor
from britekit.core.trainer import Trainer
from britekit.core.tuner import Tuner
from britekit.occurrence_db.occurrence_db import OccurrenceDatabase
from britekit.occurrence_db.occurrence_data_provider import OccurrenceDataProvider
from britekit.testing.per_minute_tester import PerMinuteTester
from britekit.testing.per_recording_tester import PerRecordingTester
from britekit.testing.per_segment_tester import PerSegmentTester
from britekit.training_db.extractor import Extractor
from britekit.training_db.training_db import TrainingDatabase
from britekit.training_db.training_data_provider import TrainingDataProvider

__all__ = [
    "__version__",
    "commands",
    "get_config",
    "util",
    "Analyzer",
    "Audio",
    "BaseConfig",
    "Extractor",
    "OccurrenceDatabase",
    "OccurrenceDataProvider",
    "Pickler",
    "PerMinuteTester",
    "PerRecordingTester",
    "PerSegmentTester",
    "Predictor",
    "Trainer",
    "TrainingDatabase",
    "TrainingDataProvider",
    "Tuner",
]
