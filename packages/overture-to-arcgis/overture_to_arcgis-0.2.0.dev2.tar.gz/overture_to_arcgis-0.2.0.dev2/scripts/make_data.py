"""
Licensing

Copyright 2020 Esri

Licensed under the Apache License, Version 2.0 (the "License"); You
may not use this file except in compliance with the License. You may
obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied. See the License for the specific language governing
permissions and limitations under the License.

A copy of the license is available in the repository's
LICENSE file.
"""
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path
import importlib.util
import sys

# path to the root of the project
dir_prj = Path(__file__).parent.parent

# if the project package is not installed in the environment
if importlib.util.find_spec('overture_to_arcgis') is None:
    
    # get the relative path to where the source directory is located
    src_dir = dir_prj / 'src'

    # throw an error if the source directory cannot be located
    if not src_dir.exists():
        raise EnvironmentError('Unable to import overture_to_arcgis.')

    # add the source directory to the paths searched when importing
    sys.path.insert(0, str(src_dir))

# import overture_to_arcgis
import overture_to_arcgis
from overture_to_arcgis.utils import get_logger

# read and configure 
config = ConfigParser()
config.read('config.ini')

log_level = config.get('DEFAULT', 'LOG_LEVEL')
input_data = dir_prj / config.get('DEFAULT', 'INPUT_DATA')
output_data = dir_prj / config.get('DEFAULT', 'OUTPUT_DATA')

# get datestring for file naming yyyymmddThhmmss
date_string = datetime.now().strftime("%Y%m%dT%H%M%S")

# path to save log file
log_dir = dir_prj / 'data' / 'logs'

if not log_dir.exists():
    log_dir.mkdir(parents=True)

log_file = log_dir / f'{Path(__file__).stem}_{date_string}.log'

# use the log level from the config to set up logging
logger = get_logger(logger_name=f"{Path(__file__).stem}", level=log_level)

logger.info(f'Starting data processing for {dir_prj.name}')
### Main processing - put your data processing code here ###
