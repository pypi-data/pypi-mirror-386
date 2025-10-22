"""
    DataUtils.PfBeamline.py
"""
import os

BEAMLINE_NAME = {
    "QEPB0040" : "PF BL-10C",
    "QEP01069" : "PF BL-15A2",
    "QEP03487" : "SPring-8 BL38B1",
    "FLMS00687" : "SPring-8 BL38B1",
    }

class BeamlineInfo:
    """
    A class to hold information about a beamline.
    """
    def __init__(self, **entries): 
        """Initialize the BeamlineInfo object.

        Parameters
        ----------
        **entries : dict
            Keyword arguments to initialize the beamline information.
        """
        self.__dict__.update(entries)

    def get_concfactor(self):
        """
        Get the concentration factor, which is the product of path length and extinction.

        Returns
        -------
        float
            The concentration factor.
        """
        return self.path_length * self.extinction

    def __str__(self):
        return str(self.__dict__)

def get_beamlineinfo_from_folder(folder):
    """
    Get beamline information from a folder containing UV data files.

    Parameters
    ----------
    folder : str
        The folder path containing the UV data files.

    Returns
    -------
    BeamlineInfo
        The beamline information object."""
    from glob import glob
    from molass_legacy.SerialAnalyzer.SerialDataUtils import get_uv_filename

    uv_device_id = None
    beamline = None
    file = get_uv_filename(folder)
    if file is not None:
        uvfile_path = os.path.join(folder, file)
        with open(uvfile_path) as fh:
            for k, line in enumerate(fh):
                if line.find('Spectrometers') >= 0:
                    uv_device_id = line.strip().split()[-1]
                    beamline = BEAMLINE_NAME.get(uv_device_id)
                    break

    return BeamlineInfo(uv_device_id=uv_device_id, name=beamline)

def get_beamlineinfo_from_settings():
    """
    Get beamline information from settings.
    
    Returns
    -------
    BeamlineInfo
        The beamline information object.
    """
    from molass_legacy._MOLASS.SerialSettings import get_setting
    uv_device_id = get_setting("uv_device_no")
    beamline = BEAMLINE_NAME.get(uv_device_id)
    path_length = get_setting('path_length')
    extinction = get_setting('extinction')
    return BeamlineInfo(uv_device_id=uv_device_id,
                        name=beamline,
                        path_length=path_length,
                        extinction=extinction,
                        )