import datetime
import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .functions import Functions
from .loaders import Loaders
from .objects import LocalizationFile
from .objects import SpikesFile
from .plots import Plots


class ReportFunctions:

    @staticmethod
    def PDF_report(spikes_file, settings, output_path,
                   plots=["Spikegram", "Sonogram", "Histogram", "Average activity", "Difference between L/R"],
                   add_localization_report=False, localization_file=None, localization_settings=None,
                   localization_plots=["MSO spikegram", "MSO heatmap", "MSO histogram", "MSO localization"],
                   vector=False, verbose=False):
        """
		Generates a PDF report with the spikegram, sonogram, histogram, average activity and difference between L/R plots obtained from the input SpikesFile or path containing SpikeFiles.

		Parameters:
				spikes_file (SpikesFile or string): File or path to use.
				settings (MainSettings): Configuration parameters for the input file.
				output_path (string): Destination path.
				plots (string[]): List to select the plots to be included in the PDF report.
				add_localization_report (boolean, optional): If True, the localization plots will be included in the PDF report.
				localization_file (LocalizationFile, optional): If add_localization_report is set to True, this parameter is mandatory, and it should contain the localization information.
				localization_settings (LocalizationSettings, optional): If add_localization_report is set to True, this parameter is mandatory, and it should contain the localization settings.
				localization_plots (string[], optional): If add_localization_report is set to True, this parameter is mandatory, and it should contain the list of localization plots.
				vector (boolean, optional): Set to True if you want the Spikegram plot vectorized. Note: this may make your PDF heavy.
				verbose (boolean, optional): Set to True if you want the execution time of the function to be printed.

		Returns:
				None.

		Notes:
				If the path used as input is a folder instead of a spikes file, the PDF report is generated for every spikes file contained in the folder.
		"""

        # Set a non-interactive backend for matplotlib
        matplotlib.use('pdf')

        if isinstance(spikes_file, str):

            spikes_file_extension = os.path.splitext(spikes_file)

            if spikes_file_extension[1] == ".aedat":
                if add_localization_report == False:
                    spikes_file = Loaders.loadAEDAT(spikes_file, settings)
                elif add_localization_report != False and localization_file != None and localization_settings != None:
                    spikes_file, localization_file = Loaders.loadAEDATLocalization(spikes_file, settings,
                                                                                   localization_settings)
                else:
                    print("[Functions.PDF_report] > ParametersError: the input parameters are not correct.")
                    return None
            elif spikes_file_extension[1] == ".csv":
                if add_localization_report == False:
                    spikes_file = Loaders.loadCSV(spikes_file, delimiter=',')
                elif add_localization_report != False and localization_file != None and localization_settings != None:
                    spikes_file, localization_file = Loaders.loadCSVLocalization(spikes_file, delimiter=',')
                else:
                    print("[Functions.PDF_report] > ParametersError: the input parameters are not correct.")
                    return None
            elif spikes_file_extension[1] == ".txt":
                spikes_file, localization_file = Loaders.loadZynqGrabberData(spikes_file, settings,
                                                                             localization_settings)
            else:
                print("[Functions.PDF_report] > InputFileExtensionError: the extension of the input file is not valid.")
                return None
            if spikes_file.min_ts != 0:
                Functions.adapt_timestamps(spikes_file, settings)
            if add_localization_report == True:
                localization_file.timestamps = Functions.adapt_timestamps(localization_file.timestamps, settings)

        if isinstance(spikes_file, SpikesFile):
            pdf = PdfPages(output_path)
            figures = list()

            # Spikegram
            if "Spikegram" in plots:
                spk_fig = Plots.spikegram(spikes_file, settings)
                figures.append(spk_fig)

            # Sonogram
            if "Sonogram" in plots:
                sng_fig = Plots.sonogram(spikes_file, settings)
                figures.append(sng_fig)

            # Histogram
            if "Histogram" in plots:
                _, hst_fig = Plots.histogram(spikes_file, settings)
                figures.append(hst_fig)

            # Average activity
            if "Average activity" in plots:
                if settings.mono_stereo == 0:
                    _, avg_fig = Plots.average_activity(spikes_file, settings)
                else:
                    _, _, avg_fig = Plots.average_activity(spikes_file, settings)
                figures.append(avg_fig)

            # Difference between L/R
            if "Difference between L/R" in plots:
                dlr_fig = Plots.difference_between_LR(spikes_file, settings)
                figures.append(dlr_fig)

            if add_localization_report == True:
                if isinstance(localization_file, LocalizationFile):
                    # MSO spikegram
                    if any("MSO spikegram" in s for s in localization_plots):
                        mso_spikegram = Plots.mso_spikegram(localization_file, settings, localization_settings)
                        pdf.savefig(mso_spikegram)
                        plt.draw()
                    # MSO heatmap
                    if any("MSO heatmap" in s for s in localization_plots):
                        mso_heatmap = Plots.mso_heatmap(localization_file, localization_settings)
                        pdf.savefig(mso_heatmap)
                        plt.draw()
                    # MSO histogram
                    if any("MSO histogram" in s for s in localization_plots):
                        mso_histogram = Plots.mso_histogram(localization_file, settings, localization_settings)
                        pdf.savefig(mso_histogram)
                        plt.draw()
                    # MSO localization
                    if any("MSO localization" in s for s in localization_plots):
                        mso_localization = Plots.mso_localization_plot(localization_file, settings,
                                                                       localization_settings)
                        pdf.savefig(mso_localization)
                        plt.draw()
                else:
                    print("[Functions.PDF_report] > InputFileError: the input LocalizationFile is not valid.")

            for fig in figures:
                pdf.savefig(fig, dpi=150)
                plt.close(fig)

            d = pdf.infodict()
            d['Title'] = 'pyNAVIS report'
            d['Author'] = 'Juan P. Dominguez-Morales'
            d['Subject'] = 'pyNAVIS report'
            d['Keywords'] = 'pyNAVIS'
            d['CreationDate'] = datetime.datetime.today()
            d['ModDate'] = datetime.datetime.today()

            pdf.close()
            print("[Functions.PDF_report] > PDF report generated correctly")

        else:
            print("[Functions.PDF_report] > InputFileError: the input SpikesFile is not valid.")
