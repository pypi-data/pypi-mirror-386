# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import dbm
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple, Union, cast

from fm_tools.benchexec_helper import DataModel
from fm_tools.files import unzip
from fm_tools.fmtoolversion import FmToolVersion

from fm_weck.run_result import RunResult
from fm_weck.tmp_file import NTempFile

from .config import Config, parse_fm_data
from .engine import Engine
from .file_util import copy_ensuring_unix_line_endings

logger = logging.getLogger(__name__)


def check_cache_entry(shelve_space: Path, checksum: str, config: Config) -> bool:
    checksum_file = config.get_checksum_db()

    if sys.version_info < (3, 11):
        # Python 3.10 and below only support strings as path to dbm.open
        checksum_file = str(checksum_file.resolve())

    try:
        with dbm.open(checksum_file, "r") as db:
            # dbm returns bytes, so we need to encode the checksum
            # we use utf-8 encoding to ensure consistency
            return db[shelve_space.name] == checksum.encode("utf-8")
    except dbm.error:
        logger.debug("Checksum file does not exist")
        return False
    except KeyError:
        logger.debug("Checksum does not exist")
        return False


def update_checksum(shelve_space: Path, checksum: str, config: Config):
    checksum_file = config.get_checksum_db()

    if sys.version_info < (3, 11):
        # Python 3.10 and below only support strings as path to dbm.open
        checksum_file = str(checksum_file.resolve())

    with dbm.open(checksum_file, "c") as db:
        logger.debug("Updating checksum for %s", shelve_space.name)
        logger.debug("Checksum: %s", checksum)
        # dbm only stores bytes, so we need to encode the checksum
        # we use utf-8 encoding to ensure consistency
        db[shelve_space.name] = checksum.encode("utf-8")


def setup_fm_tool(
    fm_tool: Union[Path, FmToolVersion],
    version: Optional[str],
    configuration: Config,
    offline_mode: bool = False,
) -> Tuple[FmToolVersion, Path]:
    # Don't explicitly disallow non-FmToolVersion here; Pythonic Users might want to exchange the FmToolVersion object
    # by a class with the same interface
    fm_data = parse_fm_data(fm_tool, version) if isinstance(fm_tool, (Path, str)) else fm_tool
    fm_data = cast(FmToolVersion, fm_data)

    shelve_space = configuration.get_shelve_space_for(fm_data)
    logger.debug("Using shelve space %s", shelve_space)
    skip_download = offline_mode

    if (not offline_mode) and shelve_space.exists() and shelve_space.is_dir():
        logger.debug("Shelve space already exists, testing checksum")
        checksum = fm_data.get_archive_location().resolve().checksum
        if checksum is None:
            logger.warning("No checksum available for %s, skipping cache check", fm_data.get_tool_name_with_version())
            skip_download = False
        else:
            skip_download = check_cache_entry(shelve_space, checksum, configuration)

    if not skip_download:
        if sys.platform != "win32":
            fm_data.download_and_install_into(shelve_space)
            checksum = fm_data.get_archive_location().resolve().checksum
            if checksum is None:
                logger.warning(
                    "No checksum available for %s, skipping checksum update", fm_data.get_tool_name_with_version()
                )
            else:
                update_checksum(shelve_space, checksum, configuration)

            # On Windows, we need to download the tool first and then unzip it
            # This is because the unzip operation might fail due to a permission error
        else:
            dl_loc = NTempFile(f"{fm_data.get_tool_name_with_version()}-dl.zip")
            fm_data.download_into(dl_loc.name)

            success = False
            last_error = None

            logging.info("Unzipping downloaded archive...")

            # On Windows, the unzip operation might fail due to a permission error.
            # Retrying the operation a few times mitigates this issue.
            for _ in range(100):
                try:
                    unzip(dl_loc.name, shelve_space)
                    success = True
                    break
                except PermissionError as e:
                    last_error = e
                    continue

            if not success:
                logger.error("Failed to unzip downloaded archive")
                raise last_error

        checksum = fm_data.get_archive_location().resolve().checksum
        if checksum is None:
            logger.warning(
                "No checksum available for %s, skipping checksum update", fm_data.get_tool_name_with_version()
            )
        else:
            update_checksum(shelve_space, checksum, configuration)
        map_doi(fm_data, shelve_space)

    tool_info_module = fm_data.get_toolinfo_module()

    if (not offline_mode) or tool_info_module._trivially_resolved():
        tool_info_module.resolve(target_dir=shelve_space)
    else:
        file_name = tool_info_module.raw.rpartition("/")[-1]
        tool_info_module._target_location = target = shelve_space / file_name
        tool_info_module.resolved = "." + target.stem

    if tool_info_module._target_location:
        sys.path.insert(0, str(tool_info_module._target_location.parent))

    return fm_data, shelve_space


def install_fm_tool(
    fm_tool: Union[Path, FmToolVersion], version: Optional[str], configuration: Config, install_path: Path
) -> None:
    fm_data = parse_fm_data(fm_tool, version) if isinstance(fm_tool, (Path, str)) else fm_tool
    shelve_space = install_path.resolve() if install_path else configuration.get_shelve_space_for(fm_data)

    logger.debug("Installing tool into %s", shelve_space)
    fm_data.download_and_install_into(shelve_space)


def run_guided(
    fm_tool: Union[Path, FmToolVersion],
    version: Optional[str],
    configuration: Config,
    prop: Optional[Path],
    program_files: list[Path],
    additional_args: list[str],
    witness: Optional[Path] = None,
    data_model: Optional[DataModel] = None,
    offline_mode: bool = False,
    log_output_to: Optional[Path] = None,
    output_files_to: Optional[Path] = None,
    timeout_sec: Optional[float] = None,
    print_tool_output_to_console: bool = True,
) -> RunResult:
    property_path = None
    if prop is not None:
        try:
            # the source path might not be mounted in the contianer, so we
            # copy the property to the weck_cache which should be mounted
            source_property_path = prop
            property_path = configuration.get_shelve_path_for_property(source_property_path)
            copy_ensuring_unix_line_endings(source_property_path, property_path)
        except KeyError:
            logger.error("Unknown property %s", prop)
            return RunResult(command=[], exit_code=1, raw_output="Unknown property")

    configuration.make_script_available()

    fm_data, shelve_space = setup_fm_tool(fm_tool, version, configuration, offline_mode)
    engine = Engine.from_config(fm_data, configuration)

    if log_output_to is not None:
        engine.set_log_file(log_output_to)

    if output_files_to is not None:
        engine.set_output_dir(output_files_to)
    engine.print_output_to_stdout = print_tool_output_to_console

    current_dir = Path.cwd().resolve()
    os.chdir(shelve_space)
    command = fm_data.command_line(
        Path("."),
        input_files=program_files,
        working_dir=engine.get_workdir(),
        property=property_path,
        data_model=data_model,
        options=additional_args,
        add_options_from_fm_data=True,
    )
    os.chdir(current_dir)

    # There are two ways to pass the witness
    # 1. Through the task options in BenchExec using {"witness": filename} and adding the witness to the input files
    # 2. Replacing the placeholder in FM-Data "${witness}" with the correct path
    #
    # We are using the second approach here, in order to avoid modifying FM-Data
    if witness is not None:
        assert any(c == "${witness}" for c in command), "The version given does not support witness files"
        command = [str(witness) if c == "${witness}" else c for c in command]

    logger.debug("Assembled command from fm-tools: %s", command)

    engine.use_overlay(shelve_space.name)

    return engine.run(*command, timeout_sec=timeout_sec)


def run_manual(
    fm_tool: Union[Path, FmToolVersion],
    version: Optional[str],
    configuration: Config,
    command: list[str],
    offline_mode: bool = False,
    use_overlay: bool = False,
    log_output_to: Optional[Path] = None,
    output_files_to: Optional[Path] = None,
    timeout_sec: Optional[float] = None,
    print_tool_output_to_console: bool = True,
) -> RunResult:
    fm_data, shelve_space = setup_fm_tool(fm_tool, version, configuration, offline_mode)
    engine = Engine.from_config(fm_data, configuration)

    if log_output_to is not None:
        engine.set_log_file(log_output_to)

    if output_files_to is not None:
        engine.set_output_dir(output_files_to)

    if use_overlay:
        configuration.make_script_available()
        current_dir = Path.cwd().resolve()
        os.chdir(shelve_space)
        executable = fm_data.get_executable_path(Path("."))
        os.chdir(current_dir)

        logger.debug("Running with overlay...")
        engine.use_overlay(shelve_space.name)
    else:
        executable = fm_data.get_executable_path(shelve_space)

    if log_output_to is not None:
        engine.set_log_file(log_output_to)

    if output_files_to is not None:
        engine.set_output_dir(output_files_to)

    engine.print_output_to_stdout = print_tool_output_to_console

    execution_result = engine.run(str(executable), *command, timeout_sec=timeout_sec)

    return execution_result


### Move to cache_mgr.py after merge to main ###
def map_doi(fm_data: FmToolVersion, tool_path: Path):
    doi_map = tool_path.parent / "doi_map.json"

    if os.path.exists(doi_map):
        with open(doi_map, "r") as file:
            data = json.load(file)
    else:
        data = {}

    doi = str(tool_path).split("/")[-1]
    if doi not in data:
        data[doi] = []
    if fm_data.get_tool_name_with_version() not in data[doi]:
        data[doi].append(fm_data.get_tool_name_with_version())

    with open(doi_map, "w") as file:
        json.dump(data, file, indent=2)


### Move to cache_mgr.py after merge to main ###
