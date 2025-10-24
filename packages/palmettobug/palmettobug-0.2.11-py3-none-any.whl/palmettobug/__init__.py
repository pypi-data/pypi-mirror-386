'''
Welcome to PalmettoBUG! 

PalmettoBUG's analysis functions are available either thorugh the GUI, or through scripting.
To launch the GUI, run the command 'palmettobug' in a CLI environment where PalmettoBUG is installed, or use the function 
PalmettoBUG.run_GUI() in a script.


License: GPL3
Author: Ben Caiello
Institution: FlowCytometry and Cell Sorting Shared Resource of the Hollings Cancer Center at the Medical University of South Carolina


This script contains the code for exporting the various functions / classes of PalmettoBUG's non-GUI API
'''

from .Executable import run_GUI    ## might as well create an additional launch point for the GUI program

from .Entrypoint.app_and_entry import fetch_CyTOF_example, fetch_IMC_example
from .Entrypoint.bead_norm import CyTOF_bead_normalize

from .ImageProcessing.ImageAnalysisClass import (ImageAnalysis, 
                                               mask_expand, 
                                               imc_entrypoint, 
                                               read_txt_file, 
                                               txt_folder_to_tiff_folder,
                                               setup_for_FCS)

from .Pixel_Classification.Classifiers import SupervisedClassifier, UnsupervisedClassifier, plot_pixel_heatmap, plot_class_centers, segment_class_map_folder
from .Pixel_Classification.use_classifiers import (plot_classes,
                                                   merge_classes, 
                                                   merge_folder,
                                                   slice_folder,
                                                   mode_classify_folder,
                                                   secondary_flowsom,
                                                   classify_from_secondary_flowsom,
                                                   extend_masks_folder, 
                                                   )
                 
from .Analysis_functions.WholeClassAnalysis import WholeClassAnalysis
from .Analysis_functions.Analysis import Analysis
#from .Analysis_functions.SpatialANOVA import SpatialANOVA, plot_spatial_stat_heatmap, do_functional_ANOVA, do_K_L_g
from .Analysis_functions.SpatialAnalysis import SpatialAnalysis

from .Utils.sharedClasses import TableLaunch_nonGUI as TableLaunch
from .Utils.sharedClasses import run_napari

__version__ = '0.2.11'
__all__ = ["run_GUI",
           "CyTOF_bead_normalize",
           "ImageAnalysis",
           "mask_expand",
           "imc_entrypoint",
           "read_txt_file",
           "txt_folder_to_tiff_folder",
           "setup_for_FCS",
           "SupervisedClassifier",
           "UnsupervisedClassifier",
           "plot_pixel_heatmap",
           "plot_class_centers",
           "plot_classes",
           "segment_class_map_folder",
           "extend_masks_folder",
           "slice_folder",
           "secondary_flowsom",
           "classify_from_secondary_flowsom",
           "mode_classify_folder",
           "merge_classes",
           "merge_folder",
           "WholeClassAnalysis",
           "Analysis",
           "SpatialAnalysis",
           "TableLaunch",
           "run_napari",
           "fetch_CyTOF_example",
           "fetch_IMC_example",
           "print_license",
           "print_3rd_party_license_info"
           ]

homedir = __file__.replace("\\","/")
homedir = homedir[:(homedir.rfind("/"))]

print("The PalmettoBUG package is copyrighted 2024-2025 by the Medical University of South Carolina and licensed under the GPL-3 license."
    "\nIt is free & open source software, can  be redistributed in compliance with the GPL3 license, and comes with absolutely no warranty."
    "\nIn python, use palmettobug.print_license() to see the license, or use palmettobug.print_3rd_party_license_info() to print information"
    "\nabout the licenses and copyright of 3rd party software used in PalmettoBUG itself or in the creation of PalmettoBUG.")

def print_license():
    license_dir = homedir + "/Assets/LICENSE.txt"
    with open(license_dir) as file:
        license = file.read()
    print(license)


def print_3rd_party_license_info():
    license_dir = homedir + "/Assets/Other_License_Details.txt"
    with open(license_dir) as file:
        license = file.read()
    print(license)
