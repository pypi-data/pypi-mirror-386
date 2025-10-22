# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import logging
import subprocess
from pathlib import Path

from fm_tools.fmtoolversion import FmToolVersion

from .engine import CACHE_MOUNT_LOCATION, Engine

logger = logging.getLogger(__name__)


def run_smoke_test(fm_data, shelve_space, config):
    if not shelve_space.exists() or not shelve_space.is_dir():
        raise ValueError(f"Invalid shelve space path: {shelve_space}")

    engine = Engine.from_config(fm_data, config)

    tool_dir = shelve_space.relative_to(config.cache_location)
    engine.work_dir = CACHE_MOUNT_LOCATION / tool_dir

    # Check for smoketest.sh first, then smoke_test.sh
    if (shelve_space / "smoketest.sh").exists():
        command = "./smoketest.sh"
    elif (shelve_space / "smoke_test.sh").exists():
        command = "./smoke_test.sh"
    else:
        raise ValueError(f"Smoke test script not found in {shelve_space}. Expected ./smoketest.sh or ./smoke_test.sh")

    engine.run(command)


def run_smoke_test_gitlab_ci(fm_data: FmToolVersion, tool_dir: Path):
    """
    Run smoke test in GitLab CI mode.
    This mode directly installs required packages using apt instead of building/pulling images.

    Args:
        fm_data: The FmToolVersion object containing tool information
        tool_dir: The directory containing the tool's smoke_test.sh script
    """
    # Get required packages from fm_data
    required_packages = fm_data.get_images().required_packages

    if required_packages:
        logger.info("Installing required packages: %s", " ".join(required_packages))

        # Install packages
        try:
            subprocess.run(["apt", "install", "-y", *required_packages], check=True)
            logger.info("Successfully installed packages: %s", " ".join(required_packages))
        except subprocess.CalledProcessError:
            logger.error("Failed to install packages.")
            raise
    else:
        logger.info("No required packages specified for this tool")

    # Run the smoke test script
    # Check for smoketest.sh first, then smoke_test.sh
    smoke_test_script = tool_dir / "smoketest.sh"
    if not smoke_test_script.exists():
        smoke_test_script = tool_dir / "smoke_test.sh"

    if not smoke_test_script.exists():
        raise ValueError(
            f"Smoke test script not found in downloaded tool directory: {tool_dir}. "
            f"Expected ./smoketest.sh or ./smoke_test.sh"
        )

    logger.info("Running smoke test script: %s", smoke_test_script)
    try:
        subprocess.run([f"./{smoke_test_script.name}"], cwd=tool_dir, check=True)
        logger.info("Smoke test completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error("Smoke test failed with return code %d", e.returncode)
        raise
