import os
from tkinter import *
from tkinter import ttk
from typing import Optional, Union

from simba.mixins.config_reader import ConfigReader
from simba.mixins.pop_up_mixin import PopUpMixin
from simba.ui.tkinter_functions import (CreateLabelFrameWithIcon, FileSelect,
                                        FolderSelect, SimbaButton,
                                        SimbaCheckbox, SimBADropDown)
from simba.utils.checks import (check_file_exist_and_readable,
                                check_if_dir_exists, check_instance, check_int)
from simba.utils.enums import Formats, Options
from simba.utils.errors import InvalidInputError
from simba.utils.read_write import (copy_multiple_videos_to_project,
                                    copy_single_video_to_project)

#from simba.sandbox.tkinter_drag_and_drop import FileDropBox


class ImportVideosFrame(PopUpMixin, ConfigReader):

    """
    .. image:: _static/img/ImportVideosFrame.webp
       :width: 500
       :align: center

    :param Optional[Union[Frame, Canvas, LabelFrame, ttk.Frame]] parent_frm: Parent frame to insert the Import Videos frame into. If None, one is created.
    :param Optional[Union[str, os.PathLike]] config_path:
    :param Optional[int] idx_row: The row in parent_frm to insert the Videos frame into. Default: 0.
    :param Optional[int] idx_column: The column in parent_frm to insert the Videos frame into. Default: 0.

    :example:
    >>> ImportVideosFrame(config_path='/Users/simon/Desktop/envs/simba/troubleshooting/two_black_animals_14bp/project_folder/project_config.ini')
    """

    def __init__(self,
                 parent_frm: Optional[Union[Frame, Canvas, LabelFrame, ttk.Frame]] = None,
                 config_path: Optional[Union[str, os.PathLike]] = None,
                 idx_row: Optional[int] = 0,
                 idx_column: Optional[int] = 0):

        if parent_frm is None and config_path is None:
            raise InvalidInputError(msg='If parent_frm is None, please pass config_path', source=self.__class__.__name__)

        elif parent_frm is None and config_path is not None:
            PopUpMixin.__init__(self, config_path=config_path, title='IMPORT VIDEO FILES', icon='import')
            parent_frm = self.main_frm

        check_instance(source=f'{ImportVideosFrame} parent_frm', accepted_types=(Frame, Canvas, LabelFrame, ttk.Frame), instance=parent_frm)
        check_int(name=f'{ImportVideosFrame} idx_row', value=idx_row, min_value=0)
        check_int(name=f'{ImportVideosFrame} idx_column', value=idx_column, min_value=0)

        import_videos_frm = CreateLabelFrameWithIcon(parent=parent_frm, header="IMPORT VIDEOS", icon_name='import', relief='solid', padx=5, pady=5)
        if config_path is None:
            Label(import_videos_frm, text="Please CREATE PROJECT CONFIG before importing VIDEOS \n", font=Formats.FONT_REGULAR.value).grid(row=0, column=0, sticky=NW)
            import_videos_frm.grid(row=0, column=0, sticky=NW)
        else:
            ConfigReader.__init__(self, config_path=config_path, read_video_info=False)
            import_multiple_videos_frm = CreateLabelFrameWithIcon(parent=import_videos_frm, header="IMPORT MULTIPLE VIDEOS", icon_name='stack')
            self.video_directory_select = FolderSelect(import_multiple_videos_frm, "VIDEO DIRECTORY: ", lblwidth=25, entry_width=25)

            self.video_type = SimBADropDown(parent=import_multiple_videos_frm, dropdown_options=Options.VIDEO_FORMAT_OPTIONS.value, label="VIDEO FILE FORMAT: ", label_width=25, dropdown_width=25, value=Options.VIDEO_FORMAT_OPTIONS.value[0])
            import_multiple_btn = SimbaButton(parent=import_multiple_videos_frm, txt="Import MULTIPLE videos", txt_clr='blue', font=Formats.FONT_REGULAR.value, cmd=self.__run_video_import, cmd_kwargs={"multiple_videos": lambda: True})

            multiple_videos_symlink_cb, self.multiple_videos_symlink_var = SimbaCheckbox(parent=import_multiple_videos_frm, txt="Import SYMLINKS", txt_img='link')

            import_single_frm = CreateLabelFrameWithIcon(parent=import_videos_frm, header="IMPORT SINGLE VIDEO", icon_name='video')
            self.video_file_select = FileSelect(import_single_frm, "VIDEO PATH: ", title="Select a video file", lblwidth=25, file_types=[("VIDEO FILE", Options.ALL_VIDEO_FORMAT_STR_OPTIONS.value)], entry_width=25)
            import_single_btn = SimbaButton(parent=import_single_frm, txt="Import SINGLE video", txt_clr='blue', font=Formats.FONT_REGULAR.value, cmd=self.__run_video_import, cmd_kwargs={"multiple_videos": lambda: False})
            single_video_symlink_cb, self.single_video_symlink_var = SimbaCheckbox(parent=import_single_frm, txt="Import SYMLINKS", txt_img='link')

            import_videos_frm.grid(row=0, column=0, sticky=NW)
            import_multiple_videos_frm.grid(row=0, sticky=W)
            self.video_directory_select.grid(row=1, sticky=W)
            self.video_type.grid(row=2, sticky=W)
            multiple_videos_symlink_cb.grid(row=3, sticky=W)
            import_multiple_btn.grid(row=4, sticky=W)

            import_single_frm.grid(row=1, column=0, sticky=NW)
            self.video_file_select.grid(row=0, sticky=W)
            single_video_symlink_cb.grid(row=1, sticky=W)
            import_single_btn.grid(row=2, sticky=W)
            import_videos_frm.grid(row=idx_row, column=idx_column, sticky=NW)

            #video_drop_box = FileDropBox(parent=import_videos_frm)
            #video_drop_box.drop_box_frm.grid(row=2, column=1, sticky=NW)



        #parent_frm.mainloop()

    def __run_video_import(self, multiple_videos: bool):
        if multiple_videos:
            check_if_dir_exists(in_dir=self.video_directory_select.folder_path)
            copy_multiple_videos_to_project(config_path=self.config_path,
                                            source=self.video_directory_select.folder_path,
                                            symlink=self.multiple_videos_symlink_var.get(),
                                            file_type=self.video_type.getChoices())

        else:
            check_file_exist_and_readable(file_path=self.video_file_select.file_path)
            copy_single_video_to_project(simba_ini_path=self.config_path,
                                         symlink=self.single_video_symlink_var.get(),
                                         source_path=self.video_file_select.file_path)


#ImportVideosFrame(config_path=r"C:\troubleshooting\RAT_NOR\project_folder\project_config.ini")