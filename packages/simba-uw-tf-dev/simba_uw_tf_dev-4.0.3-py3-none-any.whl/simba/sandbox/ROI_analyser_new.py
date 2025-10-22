__author__ = "Simon Nilsson"

import os
from typing import List, Optional, Union

import numpy as np
import pandas as pd

from simba.mixins.config_reader import ConfigReader
from simba.mixins.feature_extraction_mixin import FeatureExtractionMixin
from simba.mixins.feature_extraction_supplement_mixin import \
    FeatureExtractionSupplemental
from simba.utils.checks import (check_if_dir_exists, check_all_file_names_are_represented_in_video_log, check_file_exist_and_readable, check_float, check_that_column_exist, check_valid_lst, check_valid_boolean, check_valid_dataframe, check_valid_array)
from simba.utils.data import detect_bouts, slice_roi_dict_for_video
from simba.utils.enums import Keys, ROI_SETTINGS, Formats
from simba.utils.errors import (CountError, MissingColumnsError, ROICoordinatesNotFoundError)
from simba.utils.printing import stdout_success, SimbaTimer
from simba.utils.read_write import get_fn_ext, read_data_paths, read_df
from simba.utils.warnings import NoDataFoundWarning
from simba.roi_tools.roi_utils import get_roi_dict_from_dfs

SHAPE_TYPE = "Shape_type"
TOTAL_ROI_TIME = 'TOTAL ROI TIME (S)'
ENTRY_COUNTS = 'ROI ENTRIES (COUNTS)'
FIRST_ROI_ENTRY_TIME = 'FIRST ROI ENTRY TIME (HH:MM:SS)'
LAST_ROI_ENTRY_TIME = 'LAST ROI ENTRY TIME (HH:MM:SS)'
MEAN_BOUT_TIME = 'MEAN ROI BOUT TIME (S)'
VELOCITY = 'AVERAGE ROI VELOCITY (CM/S)'
MOVEMENT = 'TOTAL ROI MOVEMENT (CM)'
MEASUREMENT = 'MEASUREMENT'



def movement_stats_from_bouts_df(bp_data: np.ndarray, bout_df: pd.DataFrame, fps: float, px_per_mm: float):
    check_valid_dataframe(df=bout_df, source=movement_stats_from_bouts_df.__name__, required_fields=['Event', 'Start_time', 'End Time', 'Start_frame', 'End_frame', 'Bout_time'])
    check_valid_array(data=bp_data, source=f'{movement_stats_from_bouts_df.__name__} bp_data', accepted_ndims=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, accepted_axis_1_shape=[2,])
    if len(bout_df['Event'].unique()) > 1:
        raise CountError(f'Computing movement stats from bouts_df only accepts a single unique event, got {len(bout_df["Event"].unique())}', source=movement_stats_from_bouts_df.__name__)
    if len(bout_df) == 0:
        movement, velocity = 0,  None
    else:
        distances, velocities = [], []
        roi_frames = bout_df[["Start_frame", "End_frame"]].values
        for event_start_frm, event_end_frm in roi_frames:
            event_pose = bp_data[event_start_frm:event_end_frm+1, :]
            if event_pose.shape[0] > 1:
                distance, velocity = FeatureExtractionSupplemental.distance_and_velocity(x=event_pose, fps=fps, pixels_per_mm=px_per_mm, centimeters=True)
                distances.append(distance)
                velocities.append(velocity)
        if len(distances) == 0:
            movement, velocity = 0, None
        else:
            movement, velocity = sum(distances), np.average(velocities)
    return movement, velocity

class ROIAggregateStatisticsAnalyzer(ConfigReader, FeatureExtractionMixin):
    """
    Analyzes region-of-interest (ROI) data from video tracking experiments.
    This class computes various statistics related to body-part movements inside defined ROIs,
    including entry counts, total time spent, and bout durations.


    :param config_path (str | os.PathLike): Path to the configuration file.
    :param data_path (str | os.PathLike | List[str], optional): Path(s) to the data files.
    :param threshold (float): Probability threshold for body-part inclusion.
    :param body_parts (List[str], optional): List of body parts to analyze.
    :param detailed_bout_data (bool): Whether to compute detailed bout data.
    :param calculate_distances (bool): Whether to compute distances traveled.
    :param total_time (bool): Whether to calculate total time spent in ROIs.
    :param entry_counts (bool): Whether to count entries into ROIs.
    :param first_entry_time (bool): Whether to record the first entry time.
    :param last_entry_time (bool): Whether to record the last entry time.
    :param mean_bout_time (bool): Whether to compute mean bout duration.
    :param transpose (bool): Whether to transpose the final results.
    :param detailed_bout_data_save_path (str | os.PathLike, optional): Path to save detailed bout data.
    :param save_path (str | os.PathLike, optional): Path to save summary statistics.
    """


    def __init__(self,
                 config_path: Union[str, os.PathLike],
                 data_path: Optional[Union[str, os.PathLike, List[str]]] = None,
                 threshold: float = 0.0,
                 body_parts: Optional[List[str]] = None,
                 detailed_bout_data: bool = False,
                 calculate_distances: bool = False,
                 total_time: bool = True,
                 entry_counts: bool = True,
                 first_entry_time: bool = False,
                 last_entry_time: bool = False,
                 mean_bout_time: bool = False,
                 transpose: bool = False,
                 detailed_bout_data_save_path: Optional[Union[str, os.PathLike]] = None,
                 save_path: Optional[Union[str, os.PathLike]] = None):

        check_file_exist_and_readable(file_path=config_path)
        ConfigReader.__init__(self, config_path=config_path)
        if not os.path.isfile(self.roi_coordinates_path):
            raise ROICoordinatesNotFoundError(expected_file_path=self.roi_coordinates_path)
        check_valid_lst(data=body_parts, source=f"{self.__class__.__name__} body-parts", valid_dtypes=(str,), valid_values=self.project_bps)
        #check_float(name="Body-part probability threshold", value=threshold, min_value=0.0, max_value=1.0)
        if len(set(body_parts)) != len(body_parts):
            raise CountError(msg=f"All body-part entries have to be unique. Got {body_parts}", source=self.__class__.__name__)
        if detailed_bout_data_save_path is not None:
            check_if_dir_exists(in_dir=os.path.dirname(detailed_bout_data_save_path))
        else:
            self.detailed_bout_data_save_path = os.path.join(self.logs_path, f'{"Detailed_ROI_data"}_{self.datetime}.csv')
        if save_path is not None:
            check_if_dir_exists(in_dir=os.path.dirname(save_path))
        else:
            save_path = f'{"ROI_descriptive statistics"}_{self.datetime}.csv'
        self.detailed_bout_data_save_path, self.save_path = detailed_bout_data_save_path, save_path
        check_valid_boolean(value=[detailed_bout_data], source=f'{self.__class__.__name__} detailed_bout_data', raise_error=True)
        check_valid_boolean(value=[total_time], source=f'{self.__class__.__name__} total_time', raise_error=True)
        check_valid_boolean(value=[entry_counts], source=f'{self.__class__.__name__} entry_counts', raise_error=True)
        check_valid_boolean(value=[first_entry_time], source=f'{self.__class__.__name__} first_entry_time', raise_error=True)
        check_valid_boolean(value=[last_entry_time], source=f'{self.__class__.__name__} last_entry_time', raise_error=True)
        check_valid_boolean(value=[mean_bout_time], source=f'{self.__class__.__name__} mean_bout_time', raise_error=True)
        check_valid_boolean(value=[calculate_distances], source=f'{self.__class__.__name__} calculate_distances', raise_error=True)
        check_valid_boolean(value=[transpose], source=f'{self.__class__.__name__} transpose', raise_error=True)
        self.read_roi_data()
        FeatureExtractionMixin.__init__(self)
        self.data_paths = read_data_paths(path=data_path, default=self.outlier_corrected_paths, default_name=self.outlier_corrected_dir, file_type=self.file_type)
        self.bp_dict, self.bp_lk = {}, {}
        for bp in body_parts:
            animal = self.find_animal_name_from_body_part_name(bp_name=bp, bp_dict=self.animal_bp_dict)
            self.bp_dict[animal] = [f'{bp}_{"x"}', f'{bp}_{"y"}', f'{bp}_{"p"}']
            self.bp_lk[animal] = bp
        self.roi_headers = [v for k, v in self.bp_dict.items()]
        self.roi_headers = [item for sublist in self.roi_headers for item in sublist]
        self.calculate_distances, self.threshold = calculate_distances, threshold
        self.detailed_bout_data = detailed_bout_data
        self.total_time, self.entry_counts = total_time, entry_counts
        self.first_entry_time, self.last_entry_time, self.mean_bout_time = first_entry_time, last_entry_time, mean_bout_time
        self.transpose = transpose
        self.detailed_dfs, self.detailed_df = [], []
        self.results = pd.DataFrame(columns=["VIDEO", "ANIMAL", "BODY-PART", "SHAPE", "SHAPE TYPE", "MEASUREMENT", "VALUE"])

    def __clean_results(self):
        if not self.total_time:
            self.results = self.results[self.results[MEASUREMENT] != TOTAL_ROI_TIME]
        if not self.entry_counts:
            self.results = self.results[self.results[MEASUREMENT] != ENTRY_COUNTS]
        if not self.first_entry_time:
            self.results = self.results[self.results[MEASUREMENT] != FIRST_ROI_ENTRY_TIME]
        if not self.last_entry_time:
            self.results = self.results[self.results[MEASUREMENT] != LAST_ROI_ENTRY_TIME]
        if not self.mean_bout_time:
            self.results = self.results[self.results[MEASUREMENT] != MEAN_BOUT_TIME]
        if not self.calculate_distances:
            self.results = self.results[self.results[MEASUREMENT] != VELOCITY]
            self.results = self.results[self.results[MEASUREMENT] != MOVEMENT]
        self.results = self.results.sort_values(by=["VIDEO", "ANIMAL", "BODY-PART", "SHAPE", "SHAPE TYPE", "MEASUREMENT"])
        if self.transpose:
            self.results['VALUE'] = pd.to_numeric(self.results['VALUE'], errors='coerce')
            self.results = self.results.pivot_table(index=["VIDEO"], columns=["ANIMAL", "SHAPE", "MEASUREMENT"], values="VALUE")
            self.results = self.results.fillna(value='None')
        else:
            self.results = self.results.set_index('VIDEO')

        if self.detailed_bout_data and (len(self.detailed_dfs) > 0):
            self.detailed_df = pd.concat(self.detailed_dfs, axis=0)
            self.detailed_df = self.detailed_df.rename(columns={"Event": "SHAPE NAME", "Start_time": "START TIME", "End Time": "END TIME", "Start_frame": "START FRAME", "End_frame": "END FRAME", "Bout_time": "DURATION (S)"})
            self.detailed_df["BODY-PART"] = self.detailed_df["ANIMAL"].map(self.bp_lk)
            self.detailed_df = self.detailed_df[["VIDEO", "ANIMAL", "BODY-PART", "SHAPE NAME", "START TIME", "END TIME", "START FRAME", "END FRAME", "DURATION (S)"]].reset_index(drop=True)

    def run(self):
        check_all_file_names_are_represented_in_video_log(video_info_df=self.video_info_df, data_paths=self.data_paths)
        for file_cnt, file_path in enumerate(self.data_paths):
            _, video_name, _ = get_fn_ext(file_path)
            video_timer = SimbaTimer(start=True)
            print(f"Analysing ROI data for video {video_name}... (Video {file_cnt+1}/{len(self.data_paths)})")
            video_settings, pix_per_mm, self.fps = self.read_video_info(video_name=video_name)
            self.sliced_roi_dict, video_shape_names = slice_roi_dict_for_video(data=self.roi_dict, video_name=video_name)
            if len(video_shape_names) == 0:
                NoDataFoundWarning(msg=f"Skipping video {video_name}: No user-defined ROI data found for this video...")
                continue
            else:
                self.sliced_roi_dict = get_roi_dict_from_dfs(rectangle_df=self.sliced_roi_dict[Keys.ROI_RECTANGLES.value],circle_df=self.sliced_roi_dict[Keys.ROI_CIRCLES.value],polygon_df=self.sliced_roi_dict[Keys.ROI_POLYGONS.value])
                self.data_df = read_df(file_path, self.file_type).reset_index(drop=True)
                check_that_column_exist(df=self.data_df, column_name=self.roi_headers, file_name=file_path)
                for animal_name, bp_cols in self.bp_dict.items():
                    p_arr = self.data_df[bp_cols[2]].values.astype(np.float32)
                    below_threshold_idx = np.argwhere(p_arr < self.threshold)
                    bp_arr = self.data_df[[bp_cols[0], bp_cols[1]]].values.astype(np.float32)
                    for roi_cnt, (roi_name, roi_data) in enumerate(self.sliced_roi_dict.items()):
                        if roi_data[SHAPE_TYPE] == ROI_SETTINGS.RECTANGLE.value:
                            roi_coords = np.array([[roi_data['topLeftX'], roi_data['topLeftY']], [roi_data['Bottom_right_X'], roi_data['Bottom_right_Y']]])
                            r = FeatureExtractionMixin.framewise_inside_rectangle_roi(bp_location=bp_arr, roi_coords=roi_coords)
                        elif roi_data[SHAPE_TYPE] == ROI_SETTINGS.CIRCLE.value:
                            circle_center = np.array([roi_data['Center_X'], roi_data['Center_Y']]).astype(np.int32)
                            r = FeatureExtractionMixin.is_inside_circle(bp=bp_arr, roi_center=circle_center, roi_radius=roi_data['radius'])
                        else:
                            vertices = roi_data['vertices'].astype(np.int32)
                            r = FeatureExtractionMixin.framewise_inside_polygon_roi(bp_location=bp_arr, roi_coords=vertices)
                        r[below_threshold_idx] = 0
                        self.data_df[roi_data['Name']] = r
                        roi_bouts = detect_bouts(data_df=self.data_df, target_lst=[roi_data["Name"]], fps=self.fps)
                        if len(roi_bouts) > 0:
                            total_time = roi_bouts['Bout_time'].sum()
                            entry_counts = len(roi_bouts)
                            first_entry_time = roi_bouts['Start_time'].values[0]
                            last_entry_time = roi_bouts['Start_time'].values[-1]
                            mean_bout_time = roi_bouts['Bout_time'].mean()
                            movement, velocity = movement_stats_from_bouts_df(bp_data=bp_arr, bout_df=roi_bouts, fps=self.fps, px_per_mm=pix_per_mm)
                            roi_bouts['VIDEO'] = video_name
                            roi_bouts['ANIMAL'] = animal_name
                            self.detailed_dfs.append(roi_bouts)
                        else:
                            total_time = 0
                            entry_counts = 0
                            first_entry_time = None
                            last_entry_time = None
                            mean_bout_time = None
                            movement, velocity = 0, None
                        self.results.loc[len(self.results)] = [video_name, animal_name, bp_cols[0][:-2], roi_name, roi_data[SHAPE_TYPE], 'TOTAL ROI TIME (S)', total_time]
                        self.results.loc[len(self.results)] = [video_name, animal_name, bp_cols[0][:-2], roi_name, roi_data[SHAPE_TYPE], 'ROI ENTRIES (COUNTS)', entry_counts]
                        self.results.loc[len(self.results)] = [video_name, animal_name, bp_cols[0][:-2], roi_name, roi_data[SHAPE_TYPE], 'FIRST ROI ENTRY TIME (HH:MM:SS)', first_entry_time]
                        self.results.loc[len(self.results)] = [video_name, animal_name, bp_cols[0][:-2], roi_name, roi_data[SHAPE_TYPE], 'LAST ROI ENTRY TIME (HH:MM:SS)', last_entry_time]
                        self.results.loc[len(self.results)] = [video_name, animal_name, bp_cols[0][:-2], roi_name, roi_data[SHAPE_TYPE], 'MEAN ROI BOUT TIME (S)', mean_bout_time]
                        self.results.loc[len(self.results)] = [video_name, animal_name, bp_cols[0][:-2], roi_name, roi_data[SHAPE_TYPE], 'AVERAGE ROI VELOCITY (CM/S)', velocity]
                        self.results.loc[len(self.results)] = [video_name, animal_name, bp_cols[0][:-2], roi_name, roi_data[SHAPE_TYPE], 'TOTAL ROI MOVEMENT (CM)', movement]
                video_timer.stop_timer()
                print(f'ROI analysis video {video_name} complete... (elapsed time: {video_timer.elapsed_time_str}s)')


    def save(self):
        self.__clean_results()
        if self.detailed_bout_data and len(self.detailed_df) > 0:
            self.detailed_df.to_csv(self.detailed_bout_data_save_path)
            print(f"Detailed ROI data saved at {self.detailed_bout_data_save_path}...")
        self.results.to_csv(self.save_path)
        self.timer.stop_timer()
        stdout_success(f'ROI statistics saved at {self.save_path}', elapsed_time=self.timer.elapsed_time_str)









analyzer = ROIAggregateStatisticsAnalyzer(config_path=r"C:\troubleshooting\mitra\project_folder\project_config.ini", body_parts=['Center'], first_entry_time=True, threshold=0.0, calculate_distances=True, transpose=False, detailed_bout_data=True)
analyzer.run()
analyzer.save()