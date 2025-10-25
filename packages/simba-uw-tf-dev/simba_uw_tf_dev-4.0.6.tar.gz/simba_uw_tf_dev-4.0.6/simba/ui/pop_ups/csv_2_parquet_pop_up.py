from tkinter import *

from simba.mixins.pop_up_mixin import PopUpMixin
from simba.ui.tkinter_functions import FolderSelect, SimbaButton
from simba.utils.enums import Formats
from simba.utils.read_write import (convert_csv_to_parquet,
                                    convert_parquet_to_csv)


class Csv2ParquetPopUp(PopUpMixin):
    def __init__(self):
        PopUpMixin.__init__(self, title="Convert CSV directory to parquet", size=(300, 300))
        frm = LabelFrame(self.main_frm, font=Formats.FONT_REGULAR.value, text="Select CSV directory", padx=5, pady=5)
        folder_path = FolderSelect(frm, "CSV folder path", title=" Select CSV folder")
        run_btn = SimbaButton(parent=frm, txt="Convert CSV to parquet", font=Formats.FONT_REGULAR.value, cmd=convert_csv_to_parquet, cmd_kwargs={'directory': lambda: folder_path.folder_path})
        frm.grid(row=1, sticky=W, pady=10)
        folder_path.grid(row=0, sticky=W)
        run_btn.grid(row=1, sticky=W, pady=10)


class Parquet2CsvPopUp(PopUpMixin):
    def __init__(self):
        PopUpMixin.__init__(self, title="Convert parquet directory to CSV", size=(300, 300))
        frm = LabelFrame(self.main_frm, text="Select parquet directory", padx=5, pady=5, font=Formats.FONT_REGULAR.value)
        folder_path = FolderSelect(frm, "Parquet folder path", title=" Select parquet folder")
        run_btn = Button(frm, text="Convert parquet to CSV", font=Formats.FONT_REGULAR.value, command=lambda: convert_parquet_to_csv(directory=folder_path.folder_path))
        frm.grid(row=1, sticky=W, pady=10)
        folder_path.grid(row=0, sticky=W)
        run_btn.grid(row=1, sticky=W, pady=10)
