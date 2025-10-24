'''
This module handles the widgets in the first tab of the GUI, which concern the loading of a image analysis / fcs analysis directory.
It also contains the widgets for bead normalization, he license display button, and GUI theme changes.



This file is licensed under the GPL3 license. No significant portion of the code here is known to be derived from another project 
(in the sense of needing to be separately / simulataneously licensed)
'''
import os
import sys
import shutil
from typing import Union
from pathlib import Path
import tkinter as tk
import zipfile

import requests
import customtkinter as ctk
import numpy as np
# import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image


from .._vendor import fcsparser

from ..Utils.sharedClasses import Project_logger, Analysis_logger, CtkSingletonWindow, overwrite_approval      # , DirectoryDisplay
from .bead_norm import CyTOF_bead_normalize
from ..ImageProcessing.ImageAnalysisClass import direct_to_Analysis, toggle_in_gui, imc_entrypoint
from ..ImageProcessing.ImageAnalysisWidgets import ImageProcessingWidgets 
from ..Analysis_widgets.Spatial_GUI import Spatial_py  
from ..Analysis_widgets.Analysis_GUI import Analysis_py_widgets 
from ..Pixel_Classification.Classifiers_GUI import Pixel_class_widgets
from ..Pixel_Classification.use_classifiers_GUI import Pixel_usage_widgets

__all__ = ["fetch_CyTOF_example", 
           "fetch_IMC_example"]

homedir = __file__.replace("\\","/")
homedir = homedir[:(homedir.rfind("/"))]
## do it twice to get up to the top level directory:
homedir = homedir[:(homedir.rfind("/"))] 
Theme_link = homedir + '/Assets/theme.txt'

class App(ctk.CTk):
    '''
    This is the main window for the GUI. It also contains the Tabholder class, which coordinates the tabs of the program
    '''
    def __init__(self, backend_process = None):
        super().__init__()
        self.napari_launch = backend_process
        self.light_dark = "dark"
        toggle = toggle_in_gui()
        if not toggle:    ## this horrible little construct ensures _in_gui is True even if reinitialized
            toggle_in_gui()
        ctk.set_appearance_mode("dark")
        if sys.platform == "win32":
            self.iconbitmap(homedir + "/Assets/Capture.ico")    ## Thanks to: https://www.freeconvert.com/jpg-to-ico for converting .jpg to 
                                                                            # .ico file
        with open(Theme_link) as theme:
            self.theme = theme.read()
        if len(self.theme) == 0:
            self.theme = "green"   ## green, dark-mode is the theme setup I primarily used in development
        elif (self.theme == "green") or (self.theme == "blue"):
            ctk.set_default_color_theme(self.theme)       ## green and blue are themes bundled with customtkinter (don't require a link)
        else:
            theme_dir = homedir +  "/Assets/ctkThemeBuilderThemes/"
            ctk.set_default_color_theme(theme_dir + self.theme + ".json")

        ### The 1200 by 1920 ratio is from the computer I was using to develop this program:
        dev_comp_height = 1200
        dev_comp_width = 1920
        instance_height = self.winfo_screenheight()
        instance_width = self.winfo_screenwidth()
        ratio_height = instance_height / dev_comp_height
        ratio_width = instance_width / dev_comp_width
        self.ratio = min(ratio_height,ratio_width)
        self.scaling = 1.1
        ctk.set_widget_scaling(self.ratio * 1.1)
        ctk.set_window_scaling(self.ratio * 1.1)   ### originally, PALMETOBUG was made into a rather small window, so scaling up is usual

        self.geometry("1600x1000+0+0")
        self.resizable(True,True)
        self.title("PalmettoBUG")

        self.Tabs = self.Tabholder(self)
        self.entrypoint = EntryPoint(self.Tabs)
        self.entrypoint.grid(row = 0, column = 0, padx = 10, pady = 10)

    def re__init__(self) -> None:
        self.Tabs.destroy()
        self.Tabs = self.Tabholder(self)
        self.entrypoint.destroy()
        self.entrypoint = EntryPoint(self.Tabs)
        self.entrypoint.grid(row = 0, column = 0, padx = 10, pady = 10)

    def destroy(self) -> None:   ## overwrite base class destroy method to ensure that matplotlib is closed
                         ## modified directly from the original customtkinter code for ctk.CTk.destroy()
        plt.close()
        self._disable_macos_dark_title_bar()

        # call destroy methods of super classes
        tk.Tk.destroy(self)
        ctk.windows.widgets.appearance_mode.CTkAppearanceModeBaseClass.destroy(self)
        ctk.windows.widgets.scaling.CTkScalingBaseClass.destroy(self)

    class Tabholder(ctk.CTkTabview):
        def __init__(self, master):
            super().__init__(master)
            self.start = self.add('Start')
            self.start.directory = None

            self.mcdprocessing = self.add('MCD / Image Processing')
            self.Pixel_Classification = self.add("Pixel Classification")

            self.py_exploratory = self.add('Analysis')

            self.Spatial = self.add('Spatial Analysis')
            self.set('Start')

            self.configure(width = 1550, height = 950)
            self.grid(row = 0, column = 0)

            self.px_classification = self.Px_secondary_Tabholder(self.Pixel_Classification)
            self.px_classification.grid()

            self.py_exploratory.analysiswidg = Analysis_py_widgets(self.py_exploratory)
            self.py_exploratory.analysiswidg.grid()

            self.image_proc_widg = ImageProcessingWidgets(self.mcdprocessing)
            self.image_proc_widg.grid()

            self.Spatial.widgets = Spatial_py(self.Spatial)
            self.Spatial.widgets.grid()

        class Px_secondary_Tabholder(ctk.CTkTabview):
            def __init__(self, master):
                super().__init__(master)
                self.master = master
                self.create = self.add("Create Pixel Classification")
                self.use_class = self.add("Use Pixel Classification outputs")
                self.set('Create Pixel Classification')
                self.configure(width = 1500, height = 925)
                self.grid(row = 0, column = 0)
                self.create.px_widg = Pixel_class_widgets(master = self.create)  
                self.create.px_widg.grid()
                self.use_class.px_widg = Pixel_usage_widgets(master = self.use_class) 
                self.use_class.px_widg.grid()

class EntryPoint(ctk.CTkFrame):
    '''
    This is the initial frame that helps the user provide the directory for data ingestion.

    It can always be returned to by the user to re-start the data ingestion / processing. 
    '''
    def __init__(self, Tabholder: App.Tabholder):
        super().__init__(Tabholder.start)
        self.master = Tabholder   ##### so: self.master.master  == the main App
        self.directory = None
        self.image_proc_widg = self.master.image_proc_widg
        self.configure(height = 400, width = 1600)

        ## widget set for the MCD entry point
        label = ctk.CTkLabel(master = self, text = "Directory structure options:" 
                                    "\n\n 1). A Directory containing a /raw sub-folder with .mcd files inside it"
                                    "\n  or with .tiff / .ome.tiff files inside it"
                                    "\n\n 2). a Directory containing a /main/Analysis_fcs folder \n with  .fcs files inside it")

        label.grid(column = 0, row = 0, padx = 2, pady = 2, rowspan = 3)
        label.configure(anchor = "w")

        ## widget set for the images-only entry point
        button_img = ctk.CTkButton(master = self, 
                    text = "Choose Image directory and begin", 
                    command = lambda: self.img_entry_func("", from_mcds = None))
        button_img.grid(column = 1, row = 1, padx = 10, pady = 3)

        ## widget set for FCS entry point
        button_fcs = ctk.CTkButton(master = self, text = "Choose FCS directory and begin", command = lambda: self.FCS_choice(""))
        button_fcs.grid(column = 1, row = 2, padx = 10, pady = 3)

        button_example = ctk.CTkButton(master = self, text = "Load Example Data", command = self.launchExampleDataWindow)
        button_example.grid(column = 0, row = 4, padx = 10, pady = 10) 

        ## The widget for the entry of the resolution of the images (can ignore for CyTOF / solution mode analyses)
        self.X_Y_entry = self.X_Y_res_frame(self)
        self.X_Y_entry.grid(column = 1, row = 4, padx = 10, pady = 10)

        label = ctk.CTkLabel(master = self, 
                             text = "Good Evening! I am the distinguished Mr. Palmett O. Bug, Esq." 
                                    "and gentleman. \n I am pleased to make your acquaintance. ")
        label.grid(column = 2, row = 0, padx = 5, pady = 5)

        self.display = self.display_image_button(self)
        self.display.grid(column = 2, row = 1, padx = 5, pady = 5, rowspan = 18)

        normalizer_button = ctk.CTkButton(master = self,text = "Launch Normalizer", command = lambda: self.normalize_fcs_choice(""))
        normalizer_button.grid(column = 2, row = 20, padx = 5, pady = 5)

        buttonConfig = ctk.CTkButton(master = self, text = "Launch GUI configuration window", command = self.call_configGUI)
        buttonConfig.grid(column = 3, row = 1, padx = 10, pady = 10)
        buttonConfig.configure(anchor = "e")

        button_baby = ctk.CTkButton(master = self, text = "See LICENSE Details", command = self.show_GPL)
        button_baby.grid(column = 3, row = 2, padx = 10, pady = 10) 
    
        self.after(200, lambda: self.focus())

    def show_GPL(self) -> None:
        return GPL_window(self)

    class display_image_button(ctk.CTkButton):
        def __init__(self, master):
            super().__init__(master)
            self.master = master
            image = Image.open(homedir + "/Assets/Capture3.jpg")
            self.configure(text = "", image = ctk.CTkImage(image, 
                                            size = (500,500)), 
                                            height = 550, 
                                            width = 550, 
                                            fg_color = "white", 
                                            hover = "white")

        #def update_image(self, image: Union[str, ctk.CTkImage]) -> None:
        #    if isinstance(image, str):
        #        image = Image.open(image)
        #        image = ctk.CTkImage(image, size = (550,550))
        #    self.configure(image = image)

    def call_configGUI(self) -> None:
        return configGUI_window(self.master.master)

    def launchExampleDataWindow(self):
       return LoadExampleDataWindow(self)

    class X_Y_res_frame(ctk.CTkFrame):
        '''
        The widget frame containing the entries for the X & Y resolutions of the images (can ignore if using CyTOF / solution mode)
        '''
        def __init__(self, master):
            super().__init__(master)
            self.master = master
            label = ctk.CTkLabel(master = self, text = "Enter X and Y resolution (in micrometers):")
            label.grid(column = 0, row = 0, columnspan = 2, padx = 10, pady = 10)
            
            self.entry_X = ctk.CTkEntry(master = self, textvariable = ctk.StringVar(value = "1.0"))
            self.entry_X.grid(column = 0, row = 1, padx = 10, pady = 10)

            self.entry_Y = ctk.CTkEntry(master = self, textvariable = ctk.StringVar(value = "1.0"))
            self.entry_Y.grid(column = 1, row = 1, padx = 10, pady = 10)

    def img_entry_func(self, directory: Union[str, None] = None, resolutions = None, from_mcds = None) -> None:
        '''
        This function directs the directory (and resolutions) into an experiment -- with MCD initial read-in -- 
        and sets up the Image processing Widgets 
        '''
        if resolutions is None:
            try:
                resX = float(self.X_Y_entry.entry_X.get())
                resY = float(self.X_Y_entry.entry_Y.get())
            except ValueError:
                tk.messagebox.showwarning("Warning!", message = "Resolution X / Y must be numbers!")
                return
        else:
            resX = float(resolutions[0])
            resY = float(resolutions[1])

        self.master.directory = directory.replace("\\","/")
        ### don't want the current directory to be searched (when entry field is blank)....
        if self.master.directory is None:
            self.master.directory = "not a directory"   ## if the directory remains None, odd behaviours can result 
                                                            # because of default arguments in downstram functions ---> 
                                                            # like the current directory being searched
        if len(self.master.directory) == 0:
            self.master.directory = tk.filedialog.askdirectory()
            if self.master.directory == "":
                return

        ## This is a check of the entered directory existing:
        try:
            files = [i for i in os.listdir(self.master.directory + "/raw") if ((i.lower().find(".mcd") != -1) or (i.lower().find(".tif") != -1))]
            if len(files) == 0:
                tk.messagebox.showwarning("Warning!", message = "There are no files in the raw folder!")
                return
        except FileNotFoundError:
            tk.messagebox.showwarning("Warning!", message = "This is not a valid directory!")
            return
        
        if from_mcds is None:
            example_files = sorted(os.listdir(self.master.directory + "/raw"))
            extensions = [i[(i.rfind(".") + 1):].lower() for i in example_files]
            if ("mcd" in extensions) and ("tif" not in extensions) and ("tiff" not in extensions):
                from_mcds = True
            elif (("tiff" in extensions) or ("tif" in extensions)) and ("mcd" not in extensions):
                from_mcds = False
            else:
                tk.messagebox.showwarning("Warning!", message = "The /raw sub-folder must contain .mcd or .tiff files, and ONLY .mcd or ONLY .tiff files (not a mixture)!")
                return

        Experiment = imc_entrypoint(directory = self.master.directory, 
                                      resolutions = [resX, resY], 
                                      from_mcds = from_mcds)

        self.master.px_classification.create.px_widg.set_directory(Experiment.directory_object)
        self.master.px_classification.use_class.px_widg.set_directory(Experiment.directory_object)
        self.master.px_classification.use_class.px_widg.add_experiment(experiment = Experiment)

        ## this removes any old widgets of a previously entered  MCD directory:
            ## edit 10-7-25 --> there should ALWAYS be a previously created image_proc_widg object
        self.image_proc_widg.destroy()
        self.image_proc_widg = ImageProcessingWidgets(self.master.mcdprocessing)
        self.image_proc_widg.grid(column = 0, row = 0)

        self.image_proc_widg.add_Experiment(Experiment, from_mcds = from_mcds)

        # Initialize the image processing widgets:                 
        self.image_proc_widg.initialize_buttons(self.master.directory) 

        ## set up project logger once setup is successful:
        project_log = Project_logger(self.master.directory).return_log()
        project_log.info(f"Start log in directory {self.master.directory}/Logs after loading from MCD files")
        self.master.set('MCD / Image Processing')
        return Experiment

    def normalize_fcs_choice(self, directory: Union[None, str] = None) -> None:
        self.master.py_exploratory.X = self.X_Y_entry.entry_X.get()
        self.master.py_exploratory.Y = self.X_Y_entry.entry_Y.get()
        self.master.directory = directory.replace("\\","/")

        if directory == "":
            self.master.directory = tk.filedialog.askdirectory()
            if self.master.directory == "":
                return
        try:
            beads_files = [i for i in os.listdir(self.master.directory + "/beads") if i.lower().find(".fcs") != -1]
            non_beads_files = [i for i in os.listdir(self.master.directory + "/no_beads") if i.lower().find(".fcs") != -1]
            if len(beads_files) == 0:
                tk.messagebox.showwarning("Warning!", message = "There are no FCS files in the /no_beads folder!")
                return
            if len(non_beads_files) == 0:
                tk.messagebox.showwarning("Warning!", message = "There are no FCS files in the /beads folder!")
                return
        except FileNotFoundError:
            tk.messagebox.showwarning("Warning!", message = "This is not a valid directory!")
            return 
        
        ### Launch a window for taking in user inputs as to which channels are beads channels and which are channels to normalize

        bead_1 = self.master.directory + "/beads/" + beads_files[0]
        _, beads_1 = fcsparser.parse(bead_1, channel_naming = "$PnS")
        channels = beads_1.columns
        # print(channels)
        self.channels_to_use = Channel_normalization_window(self, channels, self.master.directory)
        return self.channels_to_use

    def FCS_choice(self, directory: Union[None, str] = None) -> None:
        self.master.py_exploratory.X = self.X_Y_entry.entry_X.get()
        self.master.py_exploratory.Y = self.X_Y_entry.entry_Y.get()

        self.master.directory = directory.replace("\\","/")

        if self.master.directory is None:
            self.master.directory = "not a directory"
        if len(self.master.directory) == 0:
            self.master.directory = tk.filedialog.askdirectory()
            if self.master.directory == "":
                return
        try:
            fcs_files = [i for i in os.listdir(self.master.directory + "/main/Analysis_fcs") if i.lower().find(".fcs") != -1]
            if len(fcs_files) == 0:
                tk.messagebox.showwarning("Warning!", message = "There are no files in the /main/Analysis_fcs folder!")
                return
        except FileNotFoundError:
            tk.messagebox.showwarning("Warning!", message = "This is not a valid directory!")
            return   
        
        ## set up project logger:
        project_log = Analysis_logger(self.master.directory + "/main").return_log()
        table_launcher = direct_to_Analysis(self.master, self.master.directory)
        project_log.info(f"Start log of experiment from the directory {self.master.directory + '/main'}/Logs after loading .fcs for direct analysis")
        self.master.set('Analysis')
        self.master.master.Tabs.py_exploratory.analysiswidg.setup_dir_disp(self.master.directory + "/main")  
        self.master.master.Tabs.Spatial.widgets.setup_dir_disp(self.master.directory + "/main")
        return table_launcher


class configGUI_window(ctk.CTkToplevel, metaclass = CtkSingletonWindow):

    def __init__(self, App_instance: App):
        super().__init__()
        self.master = App_instance
        self.lt_drk = App_instance.light_dark

        label = ctk.CTkLabel(master = self, text = "Make changes to the GUI appearance:")
        label.grid(padx = 5, pady = 5)

        label1 = ctk.CTkLabel(master = self, text = "Select a Ratio to change the sizes of the widgets & window:")
        label1.grid(padx = 5, pady = 5)

        self.slider = ctk.CTkComboBox(master = self, 
                        values = ["0.85","0.9","0.95","1.0","1.05","1.1","1.15","1.2","1.25","1.3"], 
                        command = self.slider_moved)
        self.slider.grid(padx = 5, pady = 5)
        self.slider.set(App_instance.scaling)

        self.theme_dir = homedir +  "/Assets/ctkThemeBuilderThemes"
        to_display = [str(i).replace(".json","").replace("\\","/") for i in Path(self.theme_dir).rglob("[!.]*.json")]
        to_display = ["green","blue"] + [i[(i.rfind("/") + 1):] for i in to_display] 

        label2 = ctk.CTkLabel(master = self, text = "Change the color theme (note this may reset unsaved progress in an analysis):")
        label2.grid(padx = 5, pady = 5)

        self.combobox = ctk.CTkComboBox(master = self, values = to_display, command = self.change_theme)
        self.combobox.grid(padx = 5, pady = 5)
        self.combobox.set(App_instance.theme)

        self.light_dark = ctk.CTkButton(master = self, text = "Toggle theme light / dark", command = self.toggle_light_dark)
        self.light_dark.grid(padx = 5, pady = 5)

        self.after(200, lambda: self.focus())

    def re__init__(self) -> None:
        Appinstance = self.master
        self.destroy()
        return configGUI_window(Appinstance)
    
    def toggle_light_dark(self) -> None:
        if self.master.light_dark == "dark":
            ctk.set_appearance_mode("light")
            self.master.light_dark = "light"
        elif self.master.light_dark == "light":
            ctk.set_appearance_mode("dark")
            self.master.light_dark = "dark"
        self.after(200, lambda: self.focus())

    def slider_moved(self, scaling: float) -> None:
        scaling = float(scaling)
        ctk.set_widget_scaling(self.master.ratio * scaling)
        self.master.scaling = scaling

    def change_theme(self, new_theme: str) -> None:
        if new_theme in ["green", "blue"]:
            ctk.set_default_color_theme(new_theme) 
        else:
            ctk.set_default_color_theme(self.theme_dir + f"/{new_theme}.json") 
        with open(Theme_link, mode = 'w') as theme:
            theme.write(new_theme)
        self.master.theme = new_theme
        self.master.re__init__()
        return self.re__init__()

class GPL_window(ctk.CTkToplevel, metaclass = CtkSingletonWindow):

    def __init__(self, master):
        super().__init__(master)
        self.alt_license = None
        license_dir = homedir + "/Assets/LICENSE.txt"
        with open(license_dir) as file:
            self.license = file.read()

        label = ctk.CTkLabel(master = self, text = """Copyright Medical University of South Carolina 2024-2025 \n
                             
        While this project as a whole and all its scripts are licensed here under GPL-3 (see text box below)
        Much of this project is also heavily based on / derived from a number of existing open-source packages:
            \t Steinbock (https://github.com/BodenmillerGroup/steinbock), CATALYST (https://github.com/HelenaLC/CATALYST)
            \t Diffcyt (https://github.com/lmweber/diffcyt), QuPath (https://github.com/qupath/qupath/)
            \t opencv (https://github.com/opencv/opencv), spatstat (https://github.com/spatstat/spatstat.core), 
            \t spaceanova (https://github.com/sealx017/SpaceANOVA/), Premessa / Bead-normalization  (https://github.com/ParkerICI/premessa / https://github.com/nolanlab/bead-normalization)
            \t singletons (https://github.com/jmaroeder/python-singletons ), scikit-image (https://github.com/scikit-image/scikit-image),
            \t ctk_theme_builder (https://github.com/avalon60/ctk_theme_builder)

        Additionally, some packages' code is directly copied, with some modification inside PalmettoBUG itself ("vendored"):
            Vendored packages == fcsparser, fcsy, pyometiff, qnorm, readimc, and steinbock  (see _vendor folder inside PalmettoBUG package)

        The listed packages are noted because of their use beyond merely importation / use of API / use of documentation files for the many library dependencies of this project,
        and because of their extensive use in different parts of the program. See individual .py files for details & any other packages that parts of the program may have derived from.
        As far as I am aware, all imported libraries at runtime are themselves permissively or GPL-compatibly licensed, with the possible exception of opencv on MacOS and 
        Linux systems only -- opencv-python on those OS is bundled with OpenSSL 1.1.1, which is free & open-source but GPL incompatible. However, the OpenSSL library should not be 
        used / imported by PalmettoBUG at runtime.
            
        NOTE! The isoSegDenoise sister program is not licensed under GPL and contain segmentation options with non-commercial / academic
        use only restrictions. It is launched from PalmettoBUG in a separate process through command line. 
            """, 
            anchor = 'w', 
            justify = 'left')
        
        label.grid(pady = 5, padx = 5, column = 0, row = 0, columnspan = 2)

        self.button_main_license_text = ctk.CTkButton(master = self, 
                                                text = "Display Main License (GPL-3)", 
                                                state = 'disabled', 
                                                command = self.display_main)
        self.button_main_license_text.grid(pady = 5, padx = 5, column = 0, row = 1)

        self.button_alt_license_text = ctk.CTkButton(master = self, 
                                                text = "Display 3rd Party license details", 
                                                command = self.display_3rd)
        self.button_alt_license_text.grid(pady = 5, padx = 5, column = 1, row = 1)

        self.display = ctk.CTkTextbox(master = self, activate_scrollbars = True, wrap = 'none', width = 700, height = 500)
        self.display.grid(column = 0, row = 2)

        self.display.insert("0.0", self.license)
        self.display.configure(state = "disabled")

        self.after(200, lambda: self.focus())

    def display_main(self):
        ''''''
        self.button_alt_license_text.configure(state = 'normal')
        self.display.configure(state = 'normal')
        self.display.delete("0.0","end")
        self.display.insert("0.0", self.license)
        self.display.configure(state = "disabled")
        self.button_main_license_text.configure(state = 'disabled')

    def display_3rd(self):
        ''''''
        if self.alt_license is None:
            license_dir = homedir + "/Assets/Other_License_Details.txt"
            with open(license_dir) as file:
                self.alt_license = file.read()
        self.button_main_license_text.configure(state = 'normal')
        self.display.configure(state = 'normal')
        self.display.delete("0.0","end")
        self.display.insert("0.0", self.alt_license)
        self.display.configure(state = "disabled")
        self.button_alt_license_text.configure(state = 'disabled')

class Channel_normalization_window(ctk.CTkToplevel, metaclass = CtkSingletonWindow):
    def __init__(self, master, channels, directory: str):
        super().__init__(master)
        self.master = master
        self.directory = directory
        self.channels = channels   ## numpy array of strings

        self.scrollable_frame = ctk.CTkScrollableFrame(master = self, width = 350, height = 500)
        self.scrollable_frame.grid()

        self.bead_label = ctk.CTkLabel(master = self.scrollable_frame, text = str("Select \n Bead Channels:"))
        self.bead_label.grid(row = 1, column = 1, pady = 3, padx = 3)

        self.to_norm_label = ctk.CTkLabel(master = self.scrollable_frame, text = str("Select Channels \n to normalize:"))
        self.to_norm_label.grid(row = 1, column = 2, pady = 3, padx = 3)

        self.checkbox_beads_list = []
        self.checkbox_norm_list = []
        for ii,i in enumerate(channels):
            label = ctk.CTkLabel(master = self.scrollable_frame, text = str(i))
            label.grid(row = ii + 2, column = 0, pady = 3, padx = 3)

            checkbox_beads = ctk.CTkCheckBox(master = self.scrollable_frame, text = "", onvalue = True, offvalue = False)
            checkbox_beads.grid(row = ii + 2, column = 1, pady = 3, padx = 3)
            self.checkbox_beads_list.append(checkbox_beads)

            checkbox_to_norm = ctk.CTkCheckBox(master = self.scrollable_frame, text = "", onvalue = True, offvalue = False)
            checkbox_to_norm.grid(row = ii + 2, column = 2, pady = 3, padx = 3)
            if str(i) != "Time":
                checkbox_to_norm.select()
            self.checkbox_norm_list.append(checkbox_to_norm)

        label_straight = ctk.CTkLabel(master = self, 
            text = "Check to go straight to an analysis after normalization"
                "\nYou will be prompted first to select an empty directory \n to set up the new analysis in")
        label_straight.grid(column = 3)

        self.straight_to_analysis = ctk.CTkCheckBox(master = self, text = "", onvalue = True, offvalue = False)
        self.straight_to_analysis.grid(column = 3)

        self.run_button = ctk.CTkButton(master = self, 
                            text = "Perform Normalization!", 
                            command = lambda: self.accept_and_normalize(channels = self.retrieve_channels(),
                                                                    to_analysis = self.straight_to_analysis.get()))
        self.run_button.grid(row = ii + 3, column = 2, pady = 3, padx = 3)
        self.after(200, self.focus())

    def retrieve_channels(self) -> tuple[list, list]:
        bead_channels = np.array([i.get() for i in self.checkbox_beads_list])
        to_norm_channels = np.array([i.get() for i in self.checkbox_norm_list])
        bead_channels = self.channels[bead_channels]
        to_norm_channels = self.channels[to_norm_channels]
        return bead_channels, to_norm_channels

    def accept_and_normalize(self, channels: list[list[str], list[str]], to_analysis: bool = False) -> None:
        bead_channels, channels_to_normalize = channels
        if not overwrite_approval(self.directory + "/normalization", file_or_folder = "folder"):
            return

        if to_analysis:
            output_directory = self.norm_to_Analysis1()
            if output_directory == "":
                return
            if not overwrite_approval(output_directory + "/main/Analysis_fcs", file_or_folder = "folder"):
                return
        #### move functions into a separate file, likely, as done previously:
        CyTOF_bead_normalize(self.directory + "/beads", 
                                  self.directory + "/no_beads", 
                                  self.directory + "/normalization", 
                                  bead_channels, 
                                  channels_to_normalize = channels_to_normalize, 
                                  include_figures = True)
        if to_analysis:
          self.norm_to_Analysis2(self.directory + "/normalization", output_directory)
    
        self.destroy()

    def norm_to_Analysis1(self):
        output_dir = tk.filedialog.askdirectory()
        return output_dir
    
    def norm_to_Analysis2(self, norm_directory, output_directory):
        output_analysis_fcs = output_directory + "/main"
        if not os.path.exists(output_analysis_fcs):
            os.mkdir(output_analysis_fcs)
        shutil.copytree(norm_directory + "/normalized", output_analysis_fcs + "/Analysis_fcs")
        self.master.FCS_choice(output_directory)

class LoadExampleDataWindow(ctk.CTkToplevel, metaclass = CtkSingletonWindow):
    '''
    '''
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.dir = None

        grandlabel = ctk.CTkLabel(master = self, text = "Load Example data into a chosen directory:\n (chosen directory should usually be empty)")
        grandlabel.grid(padx = 3, pady = 3, column = 0, row = 0, columnspan = 2)

        label = ctk.CTkLabel(master = self, text = "Choose Directory:")
        label.grid(padx = 3, pady = 3, column = 0, row = 1)

        self.entry = ctk.CTkEntry(master = self, textvariable = ctk.StringVar(value = ""))
        self.entry.grid(padx = 3, pady = 3, column = 1, row = 1)

        button = ctk.CTkButton(master = self, text = "Launch directory selection", command = self.launch_dir_search)
        button.grid(padx = 3, pady = 3, column = 0, row = 2, columnspan = 2)

        spacer = ctk.CTkLabel(master = self, text = "")
        spacer.grid(padx = 3, pady = 3, column = 0, row = 3)

        button_CyTOF = ctk.CTkButton(master = self, text = "Load CyTOF (solution-mode) data", command = self.load_CyTOF)
        button_CyTOF.grid(padx = 3, pady = 3, column = 0, row = 4)

        button_IMC = ctk.CTkButton(master = self, text = "Load IMC (image-mode) data", command = self.load_IMC)
        button_IMC.grid(padx = 3, pady = 3, column = 1, row = 4)

        self.after(750, self.focus())

    def launch_dir_search(self):
        self.dir = tk.filedialog.askdirectory()
        self.entry.configure(textvariable = ctk.StringVar(value = self.dir))
        self.after(200, self.focus())

    def load_CyTOF(self):
        choice = self.entry.get()
        if choice == "":
            tk.messagebox.showwarning("No Directory Entered!", message = "No Directory Entered, please select one first!")
            return
        if not overwrite_approval(choice + "/main/Analysis_fcs", file_or_folder = "folder", custom_message = "Are you sure you want to overwrite files in this folder"
                                                                                                             "as well as the associated panel and metdata files?"):
            return
        fetch_CyTOF_example(choice)
        table_launcher = self.master.FCS_choice(choice + "/Example_CyTOF")
        self.withdraw()
        return table_launcher

    def load_IMC(self):
        choice = self.entry.get()
        if choice == "":
            tk.messagebox.showwarning("No Directory Entered!", message = "No Directory Entered, please select one first!")
            return
        if not overwrite_approval(choice + "/raw", file_or_folder = "folder", custom_message = "Are you sure you want to overwrite files in this folder \n "
                                                                                                "as well as the associated panels and metdata files?"):
            return
        fetch_IMC_example(choice)
        self.master.img_entry_func(choice + "/Example_IMC", from_mcds = None)
        self.withdraw()

def fetch_CyTOF_example(new_directory):
    '''
    This copies the CyTOF example data to the supplied new_directory, so that it is ready to loaded. As in: ::

        new_directory = ".../.../..."
        palmettobug.fetch_CyTOF_example(new_directory = new_directory)
        Analysis = palmettobug.Analysis()
        Analysis.load_data(new_directory)

    Calling this fetch function on an existing directory will cause the existing directory's /Analysis_fcs folder to be emptied and refilled with the example data!   
    '''
    if not os.path.exists(new_directory):
        raise Exception("Target directory does not exist")
    CyTOF_data = requests.get("https://zenodo.org/records/14983582/files/Example_CyTOF.zip?download=1")
    with open(new_directory + "/CyTOF_data.zip", 'wb') as write_to:
        write_to.write(CyTOF_data.content)
    zip_archive = zipfile.ZipFile(new_directory + "/CyTOF_data.zip")
    zip_archive.extractall(new_directory)

def fetch_IMC_example(new_directory):
    '''
    This copies the IMC example data to the supplied new_directory, so that it is ready to loaded by, As in: ::

        new_directory = ".../.../..."
        palmettobug.fetch_IMC_example(new_directory = new_directory)
        ImageAnalysis = palmettobug.ImageAnalysis(new_directory, [1.0,1.0], from_mcs = False)

    Calling this fetch function on an existing directory will caues the files in the /raw sub-folder ot be replaced with the exmaple data!
    '''
    if not os.path.exists(new_directory):
        raise Exception("Target directory does not exist")
    IMC_data = requests.get("https://zenodo.org/records/14983582/files/Example_IMC.zip?download=1", stream = True)
    with open(new_directory + "/IMC_data.zip", 'wb') as write_to:
        for i in IMC_data.iter_content(chunk_size = 1024**2):
            write_to.write(i)
    zip_archive = zipfile.ZipFile(new_directory + "/IMC_data.zip")
    zip_archive.extractall(new_directory)