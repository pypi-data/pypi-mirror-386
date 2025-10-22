# encoding: utf-8
#
#  Project name: MXCuBE
#  https://github.com/mxcube.
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU General Lesser Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

"""
ESRF XRF scan procedure
Example xml_ configuration:

.. code-block:: xml

 <object class="ESRF.ESRFXRFSpectrum">
   <object href="/bliss" role="controller"/>
   <cfgfile>/users/blissadm/local/beamline_configuration/misc/15keV.cfg</cfgfile
>
   <default_integration_time>3</default_integration_time>
   <default_energy_range>[2.0, 15]</default_energy_range>
   <cfg_energies>[15]</cfg_energies>
 </object>
"""

__copyright__ = """ Copyright © by the MXCuBE collaboration """
__license__ = "LGPLv3+"

import logging
from ast import literal_eval
from pathlib import Path
from shutil import copy2
from unittest.mock import MagicMock
from warnings import warn

import numpy as np
from PyMca5.PyMca import (
    ClassMcaTheory,
    ConfigDict,
    QtMcaAdvancedFitReport,
)

from mxcubecore.HardwareObjects.abstract.AbstractXRFSpectrum import AbstractXRFSpectrum

# Next line is a trick to avoid core dump in QtMcaAdvancedFitReport
QtMcaAdvancedFitReport.qt = MagicMock()


class ESRFXRFSpectrum(AbstractXRFSpectrum):
    """ESRF implementation of the XRF spectrum procedure"""

    def __init__(self, name):
        super().__init__(name)
        self.cfgfile = None
        self.config_fit = None
        self.ctrl_hwobj = None
        self.mcafit = None
        self.default_erange = None
        self.cfg_energies = []

    def init(self):
        """Initialise the objects and the properties"""
        super().init()
        self.ctrl_hwobj = self.get_object_by_role("controller")
        self.cfgfile = self.get_property(
            "cfgfile",
            "/users/blissadm/local/beamline_configuration/misc/15keV.cfg",
        )
        self.config_fit = ConfigDict.ConfigDict()
        self.mcafit = ClassMcaTheory.McaTheory(self.cfgfile)
        self.default_erange = literal_eval(
            self.get_property("default_energy_range", "[2.0, 15.0]"),
        )
        self.cfg_energies = literal_eval(
            self.get_property("cfg_energies", "[7, 9, 12, 15]"),
        )

    def _doSpectrum(self, ctime, filename):
        """Deprecated method."""
        warn(
            "_doSpectrum is deprecated. use _execute_spectrum",
            DeprecationWarning,
        )
        return self._execute_spectrum(ctime, filename)

    def _execute_spectrum(
        self,
        integration_time: float | None = None,
        filename: str | None = None,
    ) -> bool:
        """Local XRF spectrum sequence.

        Args:
            integration_time: MCA integration time [s].
            filename: Data file (full path).
        Returns:
            Procedure executed correctly (True) or error (False)
        """
        filename = filename or self.spectrum_info_dict["filename"]
        integration_time = integration_time or self.default_integration_time

        # protect the detector
        self.ctrl_hwobj.detcover.set_in(20)
        try:
            current_transm = self.ctrl_hwobj.find_max_attenuation(
                ctime=float(integration_time),
                datafile=filename,
                roi=self.default_erange,
            )
            self.spectrum_info_dict["beamTransmission"] = current_transm
        except Exception as exp:
            logging.getLogger("user_level_log").exception(str(exp))
            self.spectrum_command_failed()
            return False

        # put away the fluo detector
        self.ctrl_hwobj.diffractometer.fldet_out()
        return True

    # Next methods are for fitting the data with pymca

    def mcafit_configuration(self, config: dict | None = None):
        """Configure the fitting parameters. The procedure is time consuming.
           It is only executed if the last configuration file is not the same.

        Args:
            config: Configuration dictionary, containing among others the
                    configuration file name.
        """
        change = False
        if not config or "file" not in config:
            cfgfile = self._get_cfgfile(self.spectrum_info_dict["energy"])
        else:
            cfgfile = config["file"]

        if self.cfgfile != cfgfile:
            self.cfgfile = cfgfile
            change = True
        self.config_fit.read(self.cfgfile)
        if "concentrations" not in self.config_fit:
            self.config_fit["concentrations"] = {}
            change = True
        if "attenuators" not in self.config_fit:
            self.config_fit["attenuators"] = {
                "Matrix": [1, "Water", 1.0, 0.01, 45.0, 45.0]
            }
            change = True
        if "flux" in config:
            self.config_fit["concentrations"]["flux"] = float(config["flux"])
            change = True
        if "time" in config:
            self.config_fit["concentrations"]["time"] = float(config["time"])
            change = True

        if change:
            self.mcafit.configure(self.config_fit)

    def spectrum_analyse(
        self,
        data: list | None = None,
        calib: list | None = None,
        config: dict | None = None,
    ) -> bool:
        """Execute the fitting. Write the fitted data files to the archive
        directory.

        Args:
            data: The raw data.
            calib: The mca calibration.
            config: The configuration dictionary.
        """

        if not config:
            config = {
                "energy": self.spectrum_info_dict["energy"],
                "att": self.spectrum_info_dict["beamTransmission"],
                "bsX": self.spectrum_info_dict["beamSizeHorizontal"],
                "bsY": self.spectrum_info_dict["beamSizeVertical"],
                "legend": self.spectrum_info_dict["annotatedPymcaXfeSpectrum"],
                "htmldir": Path(
                    self.spectrum_info_dict["annotatedPymcaXfeSpectrum"],
                ).parent,
            }

        self.mcafit_configuration(config)
        calib = calib or self.ctrl_hwobj.mca.calibration

        # the spectrum is read by the find_max_attenuation procedure.
        # We only need the data, do not to read it again
        data = data or self.ctrl_hwobj.mca.data

        try:
            if data[0].size == 2:
                xdata = np.array(data[:, 0]) * 1.0
                ydata = np.array(data[:, 1])
            else:
                xdata = data[0] * 1.0
                ydata = data[1]

            try:
                xmin = self.config_fit["fit"]["xmin"]
                xmax = self.config_fit["fit"]["xmax"]
            except KeyError:
                xmin = data[0][0]
                xmax = data[0][-1]
            self.mcafit.setData(xdata, ydata, xmin=xmin, xmax=xmax, calibration=calib)

            self.mcafit.estimate()

            fitresult = self.mcafit.startfit(digest=1)
            if fitresult:
                fitresult = {"fitresult": fitresult[0], "result": fitresult[1]}

                # create the gallery directory
                new_dir = Path(self.spectrum_info_dict["filename"]).parent / "gallery"
                if not self.create_directory(new_dir):
                    self.update_state(self.STATES.FAULT)
                    return False

                # write the csv file to pyarch and gallery
                csvname = self.spectrum_info_dict["fittedDataFileFullPath"]
                self._write_csv_file(fitresult["result"], csvname)
                copy2(csvname, new_dir / Path(csvname).name)

                # write html report to pyarch
                fname = Path(self.spectrum_info_dict["filename"]).name
                outfile = fname.split(".")[0]
                outdir = Path(
                    self.spectrum_info_dict["annotatedPymcaXfeSpectrum"],
                ).parent

                _kw = {
                    "outdir": str(outdir),
                    "outfile": outfile,
                    "fitresult": fitresult,
                    "plotdict": {"logy": False},
                }

                report = QtMcaAdvancedFitReport.QtMcaAdvancedFitReport(**_kw)
                text = report.getText()
                report.writeReport(text=text)

                # copy png file to galery
                copy2(
                    self.spectrum_info_dict["jpegScanFileFullPath"],
                    new_dir,
                )

                return True
            return False
        except Exception as exp:
            msg = f"XRFSpectrum: problem fitting {exp}\nPlease check the raw "
            msg += f"data file {self.spectrum_info_dict['scanFileFullPath']}"
            logging.getLogger("user_level_log").exception(msg)
            self.spectrum_command_failed()
            return False

    def _write_csv_file(self, fitresult: dict, fname: str | None = None):
        """Write fitted data to a csv file.

        Args:
            fitresult: Data as dictionary.
        Kwargs:
            fname: Filename to write to (full path).
        """
        fname = fname or self.spectrum_info_dict["fittedDataFileFullPath"]
        if Path(fname).exists():
            Path(fname).unlink()

        # get the significant peaks
        peaks_dict = {}
        pars_len = len(fitresult["parameters"])
        grp_len = len(fitresult["groups"])
        nglobal = pars_len - grp_len
        parameters = fitresult["fittedpar"][:nglobal] + [0.0] * grp_len

        for grp in fitresult["parameters"][nglobal:]:
            idx = fitresult["parameters"].index(grp)
            parameters[idx] = fitresult["fittedpar"][idx]
            xmatrix = fitresult["xdata"]
            ymatrix = self.mcafit.mcatheory(parameters, xmatrix)
            ymatrix.shape = [len(ymatrix), 1]
            label = "y" + grp
            if self.mcafit.STRIP:
                peaks_dict[label] = ymatrix + self.mcafit.zz
            else:
                peaks_dict[label] = ymatrix
            peaks_dict[label].shape = (len(peaks_dict[label]),)
            parameters[idx] = 0.0

        delimiter = ","
        header = f'"channel"{delimiter}"Energy"{delimiter}"counts"{delimiter}'
        header += f'"fit"{delimiter}"continuum"{delimiter}"pileup"'

        # add the peaks label
        for key in peaks_dict:
            header += delimiter + f'"{key}"'

        # logging.getLogger("user_level_log").info("Writing %s" % fname)
        with Path(fname).open("w") as csv_fd:
            csv_fd.write(header)
            csv_fd.write("\n")
            for i in range(fitresult["xdata"].size):
                csv_fd.write(
                    "%.7g%s%.7g%s%.7g%s%.7g%s%.7g%s%.7g"
                    % (
                        fitresult["xdata"][i],
                        delimiter,
                        fitresult["energy"][i],
                        delimiter,
                        fitresult["ydata"][i],
                        delimiter,
                        fitresult["yfit"][i],
                        delimiter,
                        fitresult["continuum"][i],
                        delimiter,
                        fitresult["pileup"][i],
                    ),
                )
                for val in peaks_dict.values():
                    csv_fd.write(f"{delimiter}{val[i]:.7g}")

                csv_fd.write("\n")

    def _get_cfgfile(self, energy: float) -> str:
        """Get the correct configuration file.

        Args:
            energy(float): The energy to choose which configuration file.
        """
        self.cfg_energies.sort()
        for egy in self.cfg_energies:
            if egy > energy:
                return str(Path(self.cfgfile).parent / f"{egy}keV.cfg")
        return str(self.cfgfile)
