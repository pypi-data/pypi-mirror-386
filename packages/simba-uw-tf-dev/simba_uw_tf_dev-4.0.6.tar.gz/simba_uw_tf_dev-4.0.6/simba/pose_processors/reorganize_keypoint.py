__author__ = "Simon Nilsson"

import glob
import os
from collections import OrderedDict
from datetime import datetime
from typing import Optional

import pandas as pd

from simba.utils.checks import (check_if_dir_exists,
                                check_if_filepath_list_is_empty)
from simba.utils.enums import Formats
from simba.utils.printing import stdout_success


class KeypointReorganizer(object):
    """
    Re-organizing the order of pose-estimated keypoints in directory containing
    CSV or H5 format files.

    :param str data_folder: Path to directory containing pose-estiation CSV or H5 data
    :param str pose_tool: Tool used to perform pose-estimation. E.g., 'DLC' or 'maDLC'.
    :param str file_format: File type of pose-estimation data.

    .. note::
       `GitHub tutorial/documentation <https://github.com/sgoldenlab/simba/blob/master/docs/Tutorial_tools.md#re-organize-tracking-data>`__.

    Examples
    ----------
    >>> keypoint_reorganizer = KeypointReorganizer(data_folder="test_data/misc_test_files", pose_tool='maDLC', file_format='h5')
    >>> keypoint_reorganizer.run(animal_list=['UM', 'LM', 'LM', 'UM', 'LM', 'UM', 'LM', 'LM', 'UM', 'LM', 'UM', 'UM', 'UM', 'UM', 'LM', 'LM'], bp_lst=['Lateral_left', 'Nose', 'Tail_base', 'Lateral_right', 'Ear_right', 'Center', 'Nose', 'Ear_left', 'Ear_right', 'Center', 'Tail_end', 'Ear_left', 'Tail_base', 'Lateral_left', 'Tail_end', 'Lateral_right'])
    >>> keypoint_reorganizer = KeypointReorganizer(data_folder="test_data/misc_test_files", pose_tool='DLC', file_format='csv')
    >>> keypoint_reorganizer.run(bp_lst=['Ear_left_1', 'Ear_right_1', 'Nose_1', 'Center_1', 'Lateral_left_1', 'Lateral_right_1', 'Tail_base_1', 'Ear_left_2', 'Ear_right_2', 'Nose_2', 'Center_2', 'Lateral_left_2', 'Lateral_right_2', 'Tail_base_2'], animal_list=None)
    """

    def __init__(
        self, data_folder: str, pose_tool: str, file_format: Optional[str] = None
    ):
        check_if_dir_exists(in_dir=data_folder)
        self.data_folder, self.pose_tool = data_folder, pose_tool
        self.file_format = file_format
        self.files_found = glob.glob(self.data_folder + "/*." + file_format)
        check_if_filepath_list_is_empty(
            self.files_found,
            error_msg=f"SIMBA ERROR: {self.data_folder} directory contains no {file_format} files.",
        )
        self.datetime = str(datetime.now().strftime("%Y%m%d%H%M%S"))

        if (file_format == Formats.H5.value) and (pose_tool == "DLC" or "maDLC"):
            first_df = pd.read_hdf(self.files_found[0])
            self.header_list = list(first_df.columns)
            animal_bp_tuple_list = []
            for header_val in self.header_list:
                new_value = (header_val[1], header_val[2])
                if new_value not in animal_bp_tuple_list:
                    animal_bp_tuple_list.append(new_value)
            animal_bp_tuple_list = list(set(animal_bp_tuple_list))
            self.animal_list = [x[0] for x in animal_bp_tuple_list]
            self.bp_list = [x[1] for x in animal_bp_tuple_list]

        elif (file_format == Formats.CSV.value) and (pose_tool == "DLC" or "maDLC"):
            first_df = pd.read_csv(self.files_found[0])
            if first_df.scorer.loc[2] == "coords":
                scorer = list(first_df.columns)
                scorer.remove("scorer")
                individuals = list(first_df.loc[0, :])
                individuals.remove("individuals")
                bodyparts = list(first_df.loc[1, :])
                bodyparts.remove("bodyparts")
                coords = list(first_df.loc[2, :])
                coords.remove("coords")
                self.header_list = list(zip(scorer, individuals, bodyparts, coords))
                animallist = list(zip(individuals, bodyparts))
                animal_bp_tuple_list = list(OrderedDict.fromkeys(animallist))
                self.animal_list = [x[0] for x in animal_bp_tuple_list]
                self.bp_list = [x[1] for x in animal_bp_tuple_list]
            else:
                self.animal_list = None
                scorer = list(first_df.columns)
                scorer.remove("scorer")
                bodyparts = list(first_df.loc[0, :])
                bodyparts.remove("bodyparts")
                self.bp_list = []
                for bp in bodyparts:
                    if bp not in self.bp_list:
                        self.bp_list.append(bp)
                coords = list(first_df.loc[1, :])
                coords.remove("coords")
                self.header_list = list(zip(scorer, bodyparts, coords))

        elif (file_format == Formats.CSV.value) and (pose_tool == "SLEAP"):
            print("s")

    def run(self, bp_lst: list, animal_list: list = None):
        save_directory = os.path.join(
            self.data_folder, "Reorganized_bp_{}".format(self.datetime)
        )
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        print(
            "Saving {} new pose-estimation files in {} directory...".format(
                str(len(self.files_found)), save_directory
            )
        )
        header_tuples = []
        if self.pose_tool == "maDLC":
            for animal_name, animal_bp in zip(animal_list, bp_lst):
                header_tuples.append(
                    (self.header_list[0][0], animal_name, animal_bp, "x")
                )
                header_tuples.append(
                    (self.header_list[0][0], animal_name, animal_bp, "y")
                )
                header_tuples.append(
                    (self.header_list[0][0], animal_name, animal_bp, "likelihood")
                )
            new_df_ordered_cols = pd.MultiIndex.from_tuples(
                header_tuples, names=["scorer", "individuals", "bodyparts", "coords"]
            )
        if self.pose_tool == "DLC":
            for animal_bp in bp_lst:
                header_tuples.append((self.header_list[0][0], animal_bp, "x"))
                header_tuples.append((self.header_list[0][0], animal_bp, "y"))
                header_tuples.append((self.header_list[0][0], animal_bp, "likelihood"))
            new_df_ordered_cols = pd.MultiIndex.from_tuples(
                header_tuples, names=["scorer", "bodyparts", "coords"]
            )

        for file_cnt, file_path in enumerate(self.files_found):
            df_save_path = os.path.join(save_directory, os.path.basename(file_path))
            if self.file_format == "h5":
                df = pd.read_hdf(file_path)
                df_reorganized = pd.DataFrame(df, columns=new_df_ordered_cols)
                df_reorganized.to_hdf(
                    df_save_path, key="re-organized", format="table", mode="w"
                )
            if self.file_format == "csv":
                df = pd.read_csv(file_path, header=[0, 1, 2])
                df_reorganized = pd.DataFrame(df, columns=new_df_ordered_cols)
                df_reorganized.to_csv(df_save_path)
            print(
                "Saved {}, Video {}/{}.".format(
                    os.path.basename(file_path),
                    str(file_cnt + 1),
                    str(len(self.files_found)),
                )
            )
        stdout_success(
            msg=f"{str(len(self.files_found))} new data files with reorganized body-parts saved in {save_directory} directory"
        )


# keypoint_reorganizer = KeypointReorganizer(data_folder="/Users/simon/Desktop/envs/troubleshooting/Termites_5/import_h5", pose_tool='SLEAP', file_format='csv')
# keypoint_reorganizer = KeypointReorganizer(data_folder="/Users/simon/Desktop/envs/troubleshooting/Termites_5/import_h5", pose_tool='SLEAP', file_format='SLEAP H5')
# keypoint_reorganizer = KeypointReorganizer(data_folder="/Users/simon/Desktop/troubleshooting/B1-MS_US/el_import", pose_tool='maDLC', file_format='h5')
# keypoint_reorganizer.run(animal_list=['UM', 'LM', 'LM', 'UM', 'LM', 'UM', 'LM', 'LM', 'UM', 'LM', 'UM', 'UM', 'UM', 'UM', 'LM', 'LM'], bp_lst=['Nose', 'Tail_base', 'Tail_base', 'Lateral_right', 'Ear_right', 'Center', 'Nose', 'Ear_left', 'Ear_right', 'Center', 'Tail_end', 'Ear_left', 'Tail_base', 'Lateral_left', 'Tail_end', 'Lateral_right'])

# keypoint_reorganizer = KeypointReorganizer(data_folder="//Users/simon/Desktop/simbapypi_dev/tests/test_data/misc_test_files", pose_tool='DLC', file_format='csv')
# keypoint_reorganizer.run(bp_lst=['Ear_left_1', 'Ear_right_1', 'Nose_1', 'Center_1', 'Lateral_left_1', 'Lateral_right_1', 'Tail_base_1', 'Ear_left_2', 'Ear_right_2', 'Nose_2', 'Center_2', 'Lateral_left_2', 'Lateral_right_2', 'Tail_base_2'], animal_list=None)
