import os
import sys
import argparse
import logging
from enum import Enum

import numpy as np

from wearablepermed_utils import __version__

__author__ = "Miguel Angel Salinas Gancedo<uo34525@uniovi.es>, Alejandro Castellanos Alonso<uo265351@uniovi.es>, Antonio Miguel López Rodriguez<amlopez@uniovi.es>"
__copyright__ = "Uniovi"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

# ---- Python API ----

class ML_Model(Enum):
    ESANN = 'ESANN'
    CAPTURE24 = 'CAPTURE24'
    RANDOM_FOREST = 'RandomForest'
    XGBOOST = 'XGBoost'

class ML_Sensor(Enum):
    PI = 'thigh'
    M = 'wrist'
    C = 'hip'

def parse_ml_model(value):
    try:
        """Parse a comma-separated list of CML Models lor values into a list of ML_Sensor enums."""
        values = [v.strip() for v in value.split(',') if v.strip()]
        result = []
        invalid = []
        for v in values:
            try:
                result.append(ML_Model(v))
            except ValueError:
                invalid.append(v)
        if invalid:
            valid = ', '.join(c.value for c in ML_Model)
            raise argparse.ArgumentTypeError(
                f"Invalid color(s): {', '.join(invalid)}. "
                f"Choose from: {valid}"
            )
        return result
    except ValueError:
        valid = ', '.join(ml_model.value for ml_model in ML_Model)
        raise argparse.ArgumentTypeError(f"Invalid ML Model '{value}'. Choose from: {valid}")
    
def parse_ml_sensor(value):
    try:
        """Parse a comma-separated list of CML Models lor values into a list of ML_Sensor enums."""
        values = [v.strip() for v in value.split(',') if v.strip()]
        result = []
        invalid = []
        for v in values:
            try:
                result.append(ML_Sensor(v))
            except ValueError:
                invalid.append(v)
        if invalid:
            valid = ', '.join(c.value for c in ML_Sensor)
            raise argparse.ArgumentTypeError(
                f"Invalid color(s): {', '.join(invalid)}. "
                f"Choose from: {valid}"
            )
        return result
    except ValueError:
        valid = ', '.join(ml_model.value for ml_model in ML_Sensor)
        raise argparse.ArgumentTypeError(f"Invalid ML Model '{value}'. Choose from: {valid}")
    
def parse_args(args):
    """Parse command line parameters

    Args:hip
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Machine Learning Model Trainer")
   
    parser.add_argument(
        "-dataset-folder",
        "--dataset-folder",
        dest="dataset_folder",
        required=True,
        help="Choose the dataset root folder."
    )   
    parser.add_argument(
        "-ml-models",
        "--ml-models",
        type=parse_ml_model,
        nargs='+',
        dest="ml_models",        
        required=True,
        help=f"Available ML models: {[c.value for c in ML_Model]}."
    )
    parser.add_argument(
        "-ml-sensors",
        "--ml-sensors",
        type=parse_ml_sensor,
        nargs='+',
        dest="ml_sensors",        
        required=True,
        help=f"Available ML sensors: {[c.value for c in ML_Sensor]}."
    )    
    parser.add_argument(
        "-output-folder",
        "--output-folder",
        dest="output_folder",
        required=True,
        help="Select output folder."
    )       
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO.",
        action="store_const",
        const=logging.INFO,
    )
  
    return parser.parse_args(args)

def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )

def convolution_model_selected(models):
    for model in models:
        if model.value in [ML_Model.CAPTURE24.value, ML_Model.ESANN.value]:
            return True
        
    return False

def feature_model_selected(models):
    for model in models:
        if model.value in [ML_Model.RANDOM_FOREST.value, ML_Model.XGBOOST.value]:
            return True
        
    return False

def check_segment_body_availability(sensors, dataset_folder):
    participant_files = [
        f for f in os.listdir(dataset_folder) 
        if os.path.isfile(os.path.join(dataset_folder, f)) and
           f.endswith(".npz") and "_tot" in f and
           any(sensor in f for sensor in ['_' + item for item in [sensor.name for sensor in sensors]])
    ]

    participant_files = np.array([participant_file.split("_tot")[0] for participant_file in participant_files])

        # Get unique values
    participant_files = np.unique(participant_files)

    segment_bodies=np.empty(3, dtype='U2')
    for i, sensor in enumerate(sensors):
        if sensor.value  == 'thigh':
            segment_bodies[i] = 'PI'
        elif sensor.value == 'wrist':
            segment_bodies[i] = 'M'
        elif sensor.value == 'hip':
            segment_bodies[i]='C'

    segment_body_available = 0
    for participant_file in participant_files:
        segment_body = participant_file.split("_")[2]

        if  segment_body in segment_bodies:
            segment_body_available = segment_body_available + 1
    
    if segment_body_available < len(sensors):
        return False
    
    return True

def combine_participant_dataset(dataset_folder, models, sensors, output_folder):
    participant_files = [
        f for f in os.listdir(dataset_folder) 
        if os.path.isfile(os.path.join(dataset_folder, f)) and
           f.endswith(".npz") and "_tot" in f and
           any(sensor in f for sensor in ['_' + item for item in [sensor.name for sensor in sensors]])
    ]

    participant_files = sorted(participant_files)
    
    # get the first file top get the participant ID    
    participant_files = sorted(participant_files)

    if len(participant_files)>0: 
        tokens = participant_files[0].split("_")
        participant_id = tokens[0] + "_" + tokens[1]

    participant_dataset = []
    participant_label_dataset = []
    participant_metadata_dataset = []

    participant_feature_dataset = []
    participant_feature_label_dataset = []
    participant_feature_metadata_dataset = []
    
    for participant_file in participant_files:
        # aggregate convolution datasets
        if "features" not in participant_file and convolution_model_selected(models):
                participant_sensor_file = os.path.join(dataset_folder, participant_file)
                participant_sensor_dataset = np.load(participant_sensor_file)
                
                participant_dataset.append(participant_sensor_dataset["WINDOW_CONCATENATED_DATA"])
                participant_label_dataset.append(participant_sensor_dataset["WINDOW_ALL_LABELS"])
                participant_metadata_dataset.append(participant_sensor_dataset["WINDOW_ALL_METADATA"])        

        # aggregate feature datasets
        if "features" in participant_file and "mets" not in participant_file and feature_model_selected(models) and "tot" in participant_file:
                participant_sensor_feature_file = os.path.join(dataset_folder, participant_file)
                participant_sensor_feature_dataset = np.load(participant_sensor_feature_file)
                
                participant_feature_dataset.append(participant_sensor_feature_dataset["WINDOW_CONCATENATED_DATA"])
                participant_feature_label_dataset.append(participant_sensor_feature_dataset["WINDOW_ALL_LABELS"])
                participant_feature_metadata_dataset.append(participant_sensor_feature_dataset["WINDOW_ALL_METADATA"])

    if len(participant_dataset) > 0:
        participant_dataset = np.concatenate(participant_dataset, axis=1)
        participant_label_dataset = participant_label_dataset[:participant_dataset.shape[0]][0]
        participant_metadata_dataset = participant_metadata_dataset[:participant_dataset.shape[0]][0]

        participant_sensor_all_file = os.path.join(dataset_folder, participant_id + '_all.npz')

        np.savez(
            participant_sensor_all_file,
            WINDOW_CONCATENATED_DATA=participant_dataset,
            WINDOW_ALL_LABELS=participant_label_dataset,
            WINDOW_ALL_METADATA=participant_metadata_dataset)
    
    if len(participant_feature_dataset) > 0:
        participant_feature_dataset = np.concatenate(participant_feature_dataset, axis=1)
        participant_feature_label_dataset = participant_feature_label_dataset[:participant_feature_dataset.shape[0]][0]
        participant_feature_metadata_dataset = participant_feature_metadata_dataset[:participant_feature_dataset.shape[0]][0]
                
        participant_sensor_feature_all_file = os.path.join(dataset_folder, participant_id + "_all_features.npz")

        np.savez(
            participant_sensor_feature_all_file, 
            WINDOW_CONCATENATED_DATA=participant_feature_dataset,
            WINDOW_ALL_LABELS=participant_feature_label_dataset,
            WINDOW_ALL_METADATA=participant_feature_metadata_dataset) 
                                            
def main(args):
    args = parse_args(args)
    setup_logging(args.loglevel)

    _logger.info("Agregator starts here")

    # Participant datasets agregation
    if len(args.ml_sensors[0]) > 0:
        # check if all segment bodies indicated by user are available in the datasets
        if (check_segment_body_availability(args.ml_sensors[0], args.dataset_folder) == False):
            return

        combine_participant_dataset(args.dataset_folder, args.ml_models[0], args.ml_sensors[0], args.output_folder)

    _logger.info("Agregator end here")

def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])

if __name__ == "__main__":
    run()
