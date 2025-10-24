import os
from typing import Union
from datetime import datetime
import subprocess
import pandas as pd
import glob

from simba.utils.cli.cli_tools import set_video_parameters

ACCEPTED_VIDEO_FORMATS= ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpeg', '.mpg', '.m4v', 'webm']

CONFIG_CREATOR_PATH = r'C:\projects\simba\simba\simba\utils\config_creator.py'
YOLO_INFERENCE_PATH = r'C:\projects\simba\simba\simba\model\yolo_pose_inference.py'
YOLO_IMPORTER_PATH = r'C:\projects\simba\simba\simba\pose_importers\simba_yolo_importer.py'
FEATURE_EXTRACTOR_PATH = r'C:\projects\simba\simba\simba\feature_extractors\aggression_feature_extractor.py'

YOLO_WEIGHTS_PATH = r"E:\maplight_videos\yolo_mdl\mdl\train\weights\best.pt"
KEYPOINT_NAMES = ('Nose', 'Left_ear', 'Right_ear', 'Left_side', 'Center', 'Right_side', 'Tail_base')

class Execute():
    def __init__(self,
                 video_dir: Union[str, os.PathLike]):

        video_paths = self.find_video_files(video_dir)
        timestamp_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")[:-3]
        if len(video_paths) == 0: raise FileNotFoundError(f'No video files found in {video_dir}')
        else: print(f'Analyzing {len(video_paths)} videos...')
        self.project_name = f'SimBA_project_{timestamp_str}'
        self.project_path = os.path.join(video_dir, self.project_name)
        self.project_config_path = os.path.join(video_dir, self.project_name, 'project_folder', 'project_config.ini')
        self.video_info_path = os.path.join(video_dir, self.project_name, 'project_folder', 'logs', 'video_info.csv')
        self.yolo_csv_dir = os.path.join(video_dir, self.project_name, 'yolo_data')
        self.video_dir, self.video_paths = video_dir, video_paths
        if not os.path.isdir(self.yolo_csv_dir):
            os.makedirs(self.yolo_csv_dir)

    def find_video_files(self, root_dir, extensions=None):
        if extensions is None:
            extensions = ACCEPTED_VIDEO_FORMATS
        video_files = []
        for dirpath, _, filenames in os.walk(root_dir):
            for file in filenames:
                if any(file.lower().endswith(ext) for ext in extensions):
                    video_files.append(os.path.join(dirpath, file))
        return video_files


    def run(self):

        ########## CREATE PROJECT
        print('Creating a new SimBA project...')
        create_project_args = ["--project_path", self.video_dir,
                               "--project_name", self.project_name,
                               "--target_list", 'ATTACK']
       # subprocess.run(["conda", "run", "-n", "simba_310", "python", CONFIG_CREATOR_PATH] + create_project_args)
        subprocess.Popen(
            ["conda", "run", "-n", "simba_310", "python", CONFIG_CREATOR_PATH] + create_project_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        ).wait()  # wait for it to finish, but doesn’t hang on I/O buffering



        ########## RUN YOLO
        print(f'Running YOLO tracking on {len(self.video_paths)} video(s)...')
        run_yolo_args = ["--weights", YOLO_WEIGHTS_PATH,
                         "--video_path", self.video_dir,
                         "--save_dir", self.yolo_csv_dir,
                         "--keypoint_names", ",".join(KEYPOINT_NAMES),
                         "--interpolate",
                         "--verbose",
                         "--smoothing", "100",
                         "--box_threshold", "0.1",
                         "--max_per_class", "1"]
        subprocess.run(["conda", "run", "--no-capture-output", "-n", "simba_310", "python", YOLO_INFERENCE_PATH] + run_yolo_args)

        EXPECTED_FLOAT_COLS = ["fps", "Resolution_width", "Resolution_height", "Distance_in_mm", "pixels/mm"]
        video_info_df = pd.DataFrame(columns=["Video", "fps", "Resolution_width", "Resolution_height", "Distance_in_mm", "pixels/mm"])
        csv_files = glob.glob(os.path.join(self.yolo_csv_dir, '**', '*.csv'), recursive=True)
        csv_files = [os.path.splitext(os.path.basename(p))[0] for p in csv_files]
        for video_name in csv_files:
            video_info_df.loc[len(csv_files)] = [video_name, 30, 500, 600, 987, 1.12]
        video_info_df[EXPECTED_FLOAT_COLS] = video_info_df[EXPECTED_FLOAT_COLS].apply(pd.to_numeric, errors="coerce")
        video_info_df = video_info_df.set_index("Video")
        video_info_df.to_csv(self.video_info_path)
        print(csv_files)

        ########## IMPORT YOLO
        print(f'Importing YOLO tracking data for {len(self.video_paths)} videos to SImBA project...')
        import_yolo_args = ["--data_dir", self.yolo_csv_dir,
                            "--config_path", self.project_config_path,
                            "--verbose",
                            "--px_per_mm", "1.12",
                            "--fps", "30"]
        subprocess.run(["conda", "run", "--no-capture-output", "-n", "simba_310", "python", YOLO_IMPORTER_PATH] + import_yolo_args)




