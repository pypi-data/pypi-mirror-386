__author__ = "Simon Nilsson"

import functools
import multiprocessing
import os
import platform
import shutil
from typing import Dict, Optional, Tuple, Union

import cv2
import numpy as np
import pandas as pd

from simba.mixins.config_reader import ConfigReader
from simba.mixins.plotting_mixin import PlottingMixin
from simba.roi_tools.ROI_analyzer import ROIAnalyzer
from simba.utils.checks import (check_file_exist_and_readable, check_float,
                                check_if_keys_exist_in_dict, check_int,
                                check_video_and_data_frm_count_align)
from simba.utils.data import (create_color_palettes, detect_bouts,
                              slice_roi_dict_for_video)
from simba.utils.enums import Formats, Paths, TagNames, TextOptions
from simba.utils.errors import NoFilesFoundError
from simba.utils.printing import SimbaTimer, log_event, stdout_success
from simba.utils.read_write import (concatenate_videos_in_folder,
                                    find_core_cnt, get_fn_ext,
                                    get_video_meta_data)
from simba.utils.warnings import DuplicateNamesWarning

pd.options.mode.chained_assignment = None

SHOW_BODY_PARTS = 'show_body_part'
SHOW_ANIMAL_NAMES = 'show_animal_name'
STYLE_KEYS = [SHOW_BODY_PARTS, SHOW_ANIMAL_NAMES]


def _roi_plotter_mp(data: pd.DataFrame,
                   loc_dict: dict,
                   scalers: dict,
                   video_meta_data: dict,
                   save_temp_directory: str,
                   shape_meta_data: dict,
                   video_shape_names: list,
                   input_video_path: str,
                   body_part_dict: dict,
                   roi_analyzer_data: object,
                   colors: list,
                   style_attr: dict,
                   animal_ids: list,
                   threshold: float):

    def __insert_texts(shape_df):
        for animal_name in animal_ids:
            for _, shape in shape_df.iterrows():
                shape_name, shape_color = shape["Name"], shape["Color BGR"]
                cv2.putText(border_img, loc_dict[animal_name][shape_name]["timer_text"], loc_dict[animal_name][shape_name]["timer_text_loc"], TextOptions.FONT.value, scalers["font_size"], shape_color, TextOptions.TEXT_THICKNESS.value)
                cv2.putText(border_img, loc_dict[animal_name][shape_name]["entries_text"], loc_dict[animal_name][shape_name]["entries_text_loc"], TextOptions.FONT.value, scalers["font_size"], shape_color, TextOptions.TEXT_THICKNESS.value)
        return border_img

    fourcc = cv2.VideoWriter_fourcc(*Formats.MP4_CODEC.value)
    group_cnt = int(data["group"].values[0])
    start_frm, current_frm, end_frm = data.index[0], data.index[0], data.index[-1]
    save_path = os.path.join(save_temp_directory, f"{group_cnt}.mp4")
    writer = cv2.VideoWriter(save_path, fourcc, video_meta_data["fps"], (video_meta_data["width"] * 2, video_meta_data["height"]))
    cap = cv2.VideoCapture(input_video_path)
    cap.set(1, start_frm)

    while current_frm <= end_frm:
        ret, img = cap.read()
        border_img = cv2.copyMakeBorder(img, 0, 0, 0, int(video_meta_data["width"]), borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])
        border_img = __insert_texts(roi_analyzer_data.video_recs)
        border_img = __insert_texts(roi_analyzer_data.video_circs)
        border_img = __insert_texts(roi_analyzer_data.video_polys)

        for _, row in roi_analyzer_data.video_recs.iterrows():
            top_left_x, top_left_y, shape_name = (row["topLeftX"], row["topLeftY"], row["Name"])
            bottom_right_x, bottom_right_y = (row["Bottom_right_X"], row["Bottom_right_Y"],)
            thickness, color = row["Thickness"], row["Color BGR"]
            cv2.rectangle(border_img, (int(top_left_x), int(top_left_y)), (int(bottom_right_x), int(bottom_right_y)), color, int(thickness))

        for _, row in roi_analyzer_data.video_circs.iterrows():
            center_x, center_y, radius, shape_name = (row["centerX"], row["centerY"], row["radius"], row["Name"])
            thickness, color = row["Thickness"], row["Color BGR"]
            cv2.circle(border_img, (center_x, center_y), radius, color, int(thickness))

        for _, row in roi_analyzer_data.video_polys.iterrows():
            vertices, shape_name = row["vertices"], row["Name"]
            thickness, color = row["Thickness"], row["Color BGR"]
            cv2.polylines(border_img, [vertices], True, color, thickness=int(thickness))

        for animal_cnt, animal_name in enumerate(animal_ids):
            if style_attr[SHOW_BODY_PARTS] or style_attr[SHOW_ANIMAL_NAMES]:
                bp_data = data.loc[current_frm, body_part_dict[animal_name]].values
                if threshold < bp_data[2]:
                    if style_attr[SHOW_BODY_PARTS]:
                        cv2.circle(border_img, (int(bp_data[0]), int(bp_data[1])), scalers["circle_size"], colors[animal_cnt], -1)
                    if style_attr[SHOW_ANIMAL_NAMES]:
                        cv2.putText(border_img, animal_name, (int(bp_data[0]), int(bp_data[1])), TextOptions.FONT.value, scalers["font_size"], colors[animal_cnt], TextOptions.TEXT_THICKNESS.value)

            for shape_name in video_shape_names:
                timer = round(data.loc[current_frm, f"{animal_name}_{shape_name}_cum_sum_time"], 2)
                entries = data.loc[current_frm, f"{animal_name}_{shape_name}_cum_sum_entries"]
                cv2.putText(border_img, str(timer), loc_dict[animal_name][shape_name]["timer_data_loc"], TextOptions.FONT.value, scalers["font_size"], shape_meta_data[shape_name]["Color BGR"], TextOptions.TEXT_THICKNESS.value)
                cv2.putText(border_img, str(entries), loc_dict[animal_name][shape_name]["entries_data_loc"], TextOptions.FONT.value, scalers["font_size"], shape_meta_data[shape_name]["Color BGR"], TextOptions.TEXT_THICKNESS.value)
        writer.write(border_img)
        current_frm += 1
        print(f"Multi-processing video frame {current_frm} on core {group_cnt}...")
    cap.release()
    writer.release()

    return group_cnt


class ROIPlotMultiprocess(ConfigReader, PlottingMixin):
    """
    Visualize the ROI data (number of entries/exits, time-spent-in ROIs).

    .. note::
       `ROI tutorials <https://github.com/sgoldenlab/simba/blob/master/docs/ROI_tutorial_new.md>`__.

    .. image:: _static/img/roi_visualize.png
        :width: 400
        :align: center

    :param str config_path: Path to SimBA project config file in Configparser format
    :param str video_path: Name of video to create ROI visualizations for
    :param dict style_attr: User-defined visualization settings.
    :param int core_cnt: Number of cores to use. Default to -1 representing all available cores

    :example:
    >>> test = ROIPlotMultiprocess(config_path=r'/Users/simon/Desktop/envs/simba/troubleshooting/two_black_animals_14bp/project_folder/project_config.ini',
    >>>                            video_path="/Users/simon/Desktop/envs/simba/troubleshooting/two_black_animals_14bp/project_folder/videos/Together_1.avi",
    >>>                            core_cnt=7,
    >>>                            style_attr={'show_body_parts': True, 'show_animal_name': True},
    >>>                            body_parts={'Animal_1': 'Nose_1', 'Animal_2': 'Nose_2'})
    >>> test.run()
    """

    def __init__(self,
                 config_path: Union[str, os.PathLike],
                 video_path: Union[str, os.PathLike],
                 style_attr: Dict[str, bool],
                 body_parts: Optional[dict] = None,
                 threshold: Optional[float] = 0.0,
                 core_cnt: Optional[int] = -1):

        # if platform.system() == "Darwin":
        #     multiprocessing.set_start_method("spawn", force=True)
        ConfigReader.__init__(self, config_path=config_path)
        PlottingMixin.__init__(self)
        log_event(logger_name=str(__class__.__name__), log_type=TagNames.CLASS_INIT.value, msg=self.create_log_msg_from_init_args(locals=locals()))
        check_float(name=f'{self.__class__.__name__} threshold', value=threshold, min_value=0.0, max_value=1.0)
        check_int(name=f'{self.__class__.__name__} core_cnt', value=core_cnt, min_value=-1)
        if core_cnt == -1: core_cnt = find_core_cnt()[0]
        check_if_keys_exist_in_dict(data=style_attr, key=STYLE_KEYS, name=f'{self.__class__.__name__} style_attr')
        check_file_exist_and_readable(file_path=video_path)
        _, self.video_name, _ = get_fn_ext(video_path)

        settings = None
        if body_parts: settings = {"body_parts": body_parts, 'threshold': threshold}
        self.roi_analyzer = ROIAnalyzer(ini_path=config_path, data_path="outlier_corrected_movement_location", settings=settings)
        if not body_parts: self.animal_id_lst = self.roi_analyzer.multi_animal_id_list
        else: self.animal_id_lst = list(body_parts.keys())
        self.roi_analyzer.files_found = [os.path.join(self.roi_analyzer.input_folder, f"{self.video_name}.{self.roi_analyzer.file_type}")]
        if not os.path.isfile(self.roi_analyzer.files_found[0]):
            raise NoFilesFoundError(msg=f"SIMBA ERROR: Could not find the file at path {self.roi_analyzer.files_found[0]}. Please make sure you have corrected body-part outliers or indicated that you want to skip outlier correction", source=self.__class__.__name__,)
        self.roi_analyzer.run()
        self.roi_entries_df = self.roi_analyzer.detailed_df
        self.data_df, self.style_attr = self.roi_analyzer.data_df, style_attr
        self.out_parent_dir = os.path.join(self.project_path, Paths.ROI_ANALYSIS.value)
        if not os.path.exists(self.out_parent_dir):
            os.makedirs(self.out_parent_dir)
        self.video_save_path = os.path.join(self.out_parent_dir, f"{self.video_name}.mp4")
        self.read_roi_data()
        self.shape_columns = []
        _, self.shape_names = slice_roi_dict_for_video(data=self.roi_dict, video_name=self.video_name)
        for animal in self.animal_id_lst:
            for shape_name in self.shape_names:
                self.data_df[f"{animal}_{shape_name}"] = 0; self.shape_columns.append(f"{animal}_{shape_name}")
        self.bp_dict = self.roi_analyzer.bp_dict
        self.__insert_data()
        self.video_path = video_path
        self.cap = cv2.VideoCapture(self.video_path)
        self.video_meta_data = get_video_meta_data(self.video_path)
        self.temp_folder = os.path.join(self.out_parent_dir, self.video_name, "temp")
        if os.path.exists(self.temp_folder):
            shutil.rmtree(self.temp_folder)
        os.makedirs(self.temp_folder)
        self.core_cnt, self.threshold = core_cnt, threshold

    def __insert_data(self):
        roi_entries_dict = self.roi_entries_df[["ANIMAL", "SHAPE", "ENTRY FRAMES", "EXIT FRAMES"]].to_dict(orient="records")
        for entry_dict in roi_entries_dict:
            entry, exit = int(entry_dict["ENTRY FRAMES"]), int(entry_dict["EXIT FRAMES"])
            entry_dict["frame_range"] = list(range(entry, exit + 1))
            col_name = entry_dict["ANIMAL"] + "_" + entry_dict["SHAPE"]
            self.data_df[col_name][self.data_df.index.isin(entry_dict["frame_range"])] = 1

    def __calc_text_locs(self) -> dict:
        loc_dict = {}
        line_spacer = TextOptions.FIRST_LINE_SPACING.value
        for animal_cnt, animal_name in enumerate(self.animal_id_lst):
            loc_dict[animal_name] = {}
            for shape in self.shape_names:
                loc_dict[animal_name][shape] = {}
                loc_dict[animal_name][shape]["timer_text"] = f"{shape} {animal_name} timer:"
                loc_dict[animal_name][shape]["entries_text"] = f"{shape} {animal_name} entries:"
                loc_dict[animal_name][shape]["timer_text_loc"] = ((self.video_meta_data["width"] + TextOptions.BORDER_BUFFER_X.value), (self.video_meta_data["height"] - (self.video_meta_data["height"] + TextOptions.BORDER_BUFFER_Y.value) + self.scalers["space_size"] * line_spacer))
                loc_dict[animal_name][shape]["timer_data_loc"] = (int(self.border_img_w - (self.border_img_w / 8)), (self.video_meta_data["height"] - (self.video_meta_data["height"] + TextOptions.BORDER_BUFFER_Y.value) + self.scalers["space_size"] * line_spacer))
                line_spacer += TextOptions.LINE_SPACING.value
                loc_dict[animal_name][shape]["entries_text_loc"] = ((self.video_meta_data["width"] + TextOptions.BORDER_BUFFER_X.value), (self.video_meta_data["height"] - (self.video_meta_data["height"] + TextOptions.BORDER_BUFFER_Y.value) + self.scalers["space_size"] * line_spacer))
                loc_dict[animal_name][shape]["entries_data_loc"] = (int(self.border_img_w - (self.border_img_w / 8)), (self.video_meta_data["height"]- (self.video_meta_data["height"] + TextOptions.BORDER_BUFFER_Y.value) + self.scalers["space_size"] * line_spacer))
                line_spacer += TextOptions.LINE_SPACING.value
        return loc_dict

    def __create_counters(self) -> dict:
        cnt_dict = {}
        for animal_cnt, animal_name in enumerate(self.animal_id_lst):
            cnt_dict[animal_name] = {}
            for shape in self.shape_names:
                cnt_dict[animal_name][shape] = {}
                cnt_dict[animal_name][shape]["timer"] = 0
                cnt_dict[animal_name][shape]["entries"] = 0
                cnt_dict[animal_name][shape]["entry_status"] = False
        return cnt_dict
    #
    def __calculate_cumulative(self):
        for animal_name in self.animal_id_lst:
            for shape in self.shape_names:
                self.data_df[f"{animal_name}_{shape}_cum_sum_time"] = (self.data_df[f"{animal_name}_{shape}"].cumsum() / self.video_meta_data['fps'])
                roi_bouts = list(detect_bouts(data_df=self.data_df, target_lst=[f"{animal_name}_{shape}"], fps=self.video_meta_data['fps'])["Start_frame"])
                self.data_df[f"{animal_name}_{shape}_entry"] = 0
                self.data_df.loc[roi_bouts, f"{animal_name}_{shape}_entry"] = 1
                self.data_df[f"{animal_name}_{shape}_cum_sum_entries"] = (self.data_df[f"{animal_name}_{shape}_entry"].cumsum())


    def __create_shape_dicts(self):
        shape_dicts = {}
        for df in [self.roi_analyzer.video_recs, self.roi_analyzer.video_circs, self.roi_analyzer.video_polys]:
            if not df["Name"].is_unique:
                df = df.drop_duplicates(subset=["Name"], keep="first")
                DuplicateNamesWarning('Some of your ROIs with the same shape has the same names. E.g., you have two rectangles named "My rectangle". SimBA prefers ROI shapes with unique names. SimBA will keep one of the unique shape names and drop the rest.', source=self.__class__.__name__)
            d = df.set_index("Name").to_dict(orient="index")
            shape_dicts = {**shape_dicts, **d}
        return shape_dicts

    def __get_bordered_img_size(self) -> Tuple[int, int]:
        cap = cv2.VideoCapture(self.video_path)
        cap.set(1, 1)
        _, img = self.cap.read()
        bordered_img = cv2.copyMakeBorder(img, 0, 0, 0, int(self.video_meta_data["width"]), borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])
        cap.release()
        return bordered_img.shape[0], bordered_img.shape[1]

    def run(self):
        video_timer = SimbaTimer(start=True)
        max_dim = max(self.video_meta_data["width"], self.video_meta_data["height"])
        self.scalers = {}
        self.scalers["circle_size"] = int(TextOptions.RADIUS_SCALER.value / (TextOptions.RESOLUTION_SCALER.value / max_dim))
        self.scalers["font_size"] = float(TextOptions.FONT_SCALER.value / (TextOptions.RESOLUTION_SCALER.value / max_dim))
        self.scalers["space_size"] = int(TextOptions.SPACE_SCALER.value / (TextOptions.RESOLUTION_SCALER.value / max_dim))
        color_lst = create_color_palettes(self.roi_analyzer.animal_cnt, int((len(self.roi_analyzer.bp_names) / 3)))[0]
        self.border_img_h, self.border_img_w = self.__get_bordered_img_size()
        self.loc_dict = self.__calc_text_locs()
        self.cnt_dict = self.__create_counters()
        self.shape_dicts = self.__create_shape_dicts()
        self.__calculate_cumulative()
        check_video_and_data_frm_count_align(video=self.video_path, data=self.data_df, name=self.video_name, raise_error=False)
        data_lst = np.array_split(self.data_df.fillna(0), self.core_cnt)
        for cnt in range(len(data_lst)):
            data_lst[cnt]["group"] = cnt

        print(f"Creating ROI images, multiprocessing (determined chunksize: {self.multiprocess_chunksize}, cores: {self.core_cnt})...")
        del self.roi_analyzer.logger
        with multiprocessing.Pool(self.core_cnt, maxtasksperchild=self.maxtasksperchild) as pool:
            constants = functools.partial(_roi_plotter_mp,
                                          loc_dict=self.loc_dict,
                                          scalers=self.scalers,
                                          video_meta_data=self.video_meta_data,
                                          save_temp_directory=self.temp_folder,
                                          body_part_dict=self.bp_dict,
                                          input_video_path=self.video_path,
                                          roi_analyzer_data=self.roi_analyzer,
                                          video_shape_names=self.shape_names,
                                          shape_meta_data=self.shape_dicts,
                                          colors=color_lst,
                                          style_attr=self.style_attr,
                                          animal_ids=self.animal_id_lst,
                                          threshold=self.threshold)

            for cnt, result in enumerate(pool.imap(constants, data_lst, chunksize=self.multiprocess_chunksize)):
                print(f'Image batch {result+1} / {len(data_lst)} complete...')

            print(f"Joining {self.video_name} multi-processed ROI video...")
            concatenate_videos_in_folder(in_folder=self.temp_folder, save_path=self.video_save_path, video_format="mp4")
            video_timer.stop_timer()
            pool.terminate()
            pool.join()
            stdout_success(msg=f"Video {self.video_name} created. ROI video saved at {self.video_save_path}", elapsed_time=video_timer.elapsed_time_str, source=self.__class__.__name__, )

# test = ROIPlotMultiprocess(config_path=r'/Users/simon/Desktop/envs/simba/troubleshooting/mouse_open_field/project_folder/project_config.ini',
#                            video_path="/Users/simon/Desktop/envs/simba/troubleshooting/mouse_open_field/project_folder/videos/SI_DAY3_308_CD1_PRESENT.mp4",
#                            core_cnt=7,
#                            style_attr={'show_body_part': True, 'show_animal_name': False},
#                            body_parts={'Animal_1': 'Nose'})
# test.run()

# test = ROIPlotMultiprocess(config_path=r'/Users/simon/Desktop/envs/simba/troubleshooting/two_black_animals_14bp/project_folder/project_config.ini',
#                            video_path="/Users/simon/Desktop/envs/simba/troubleshooting/two_black_animals_14bp/project_folder/videos/Together_1.avi",
#                            core_cnt=7,
#                            style_attr={'show_body_parts': True, 'show_animal_name': True},
#                            body_parts={'Animal_1': 'Nose_1', 'Animal_2': 'Nose_2'})
# test.run()



#
# test = ROIPlotMultiprocess(ini_path=r'/Users/simon/Desktop/envs/simba/troubleshooting/RAT_NOR/project_folder/project_config.ini',
#                video_path="2022-06-20_NOB_DOT_4.mp4",
#                core_cnt=7,
#                style_attr={'Show_body_part': True, 'Show_animal_name': True}, body_parts={'Animal_1': 'Nose'})
# test.run()
#

#
# test = ROIPlotMultiprocess(ini_path=r'/Users/simon/Desktop/envs/simba/troubleshooting/spontenous_alternation/project_folder/project_config.ini',
#                video_path="F1 HAB.mp4",
#                core_cnt=5,
#                style_attr={'Show_body_part': True, 'Show_animal_name': True})
# test.run()
#
# get_video_meta_data(video_path='/Users/simon/Desktop/envs/simba/troubleshooting/RAT_NOR/project_folder/frames/output/ROI_analysis/2022-06-20_NOB_DOT_4.mp4')
# get_video_meta_data(video_path='/Users/simon/Desktop/envs/simba/troubleshooting/two_black_animals_14bp/project_folder/videos/Together_1.avi')

# test = ROIPlot(ini_path=r'/Users/simon/Desktop/troubleshooting/train_model_project/project_folder/project_config.ini', video_path=r"Together_1.avi")
# test.insert_data()
# test.visualize_ROI_data()

# test = ROIPlot(ini_path=r"Z:\DeepLabCut\DLC_extract\Troubleshooting\ROI_2_animals\project_folder\project_config.ini", video_path=r"Z:\DeepLabCut\DLC_extract\Troubleshooting\ROI_2_animals\project_folder\videos\Video7.mp4")
# test.insert_data()
# test.visualize_ROI_data()
#
# test = ROIPlotMultiprocess(ini_path=r'/Users/simon/Desktop/envs/troubleshooting/two_black_animals_14bp/project_folder/project_config.ini',
#                            video_path="Together_1.avi",
#                            style_attr={'Show_body_part': True, 'Show_animal_name': False},
#                            core_cnt=5)
# test.run()


# test = ROIPlotMultiprocess(ini_path=r'/Users/simon/Desktop/envs/troubleshooting/DLC_2_Black_animals/project_folder/project_config.ini',
#                            video_path="Together_1.avi",
#                            style_attr={'Show_body_part': True, 'Show_animal_name': False},
#                            core_cnt=5)
# test.run()
