"""
Backward.MappedInfoProxy.py
"""
from molass_legacy.Mapping.PeakMapper import MappedInfo

XR_METHOD_MAP = {'linear': 1, 'integral': 5}
UV_METHOD_MAP = {'linear': 1, 'uvdiff': 4, 'integral': 5}

def method_to_legacy_types(method):
    """
    Convert a method string to legacy options.
    
    Parameters
    ----------
    method : str or tuple of str
        The method(s) to convert. If a single string is provided, it is used for both XR and UV.

    Returns
    -------
    (int, int)
        A tuple of integers representing the legacy types for XR and UV.
    """
    if type(method) is str:
        methods = (method, method)
    else:
        methods = method
    return XR_METHOD_MAP.get(methods[0], 1), UV_METHOD_MAP.get(methods[1], 1)

class MappedInfoProxy(MappedInfo):
    """
    A proxy class for MappedInfo, which is used to store information about the
    mapping of data.

    Attributes
    ----------
    _A : float
        The slope of the linear mapping.
    _B : float
        The intercept of the linear mapping.
    opt_params : dict
        The optimization parameters for the mapping.
    """
    def __init__(self, ssd, mapping):
        """
        Initialize the proxy with a MappedInfo object.
        Parameters
        ----------
        ssd : SecSaxsData
            The SecSaxsData object containing the data.
        mapping : MappingInfo
            The MappingInfo object containing the mapping information.
        """
        self._A, self._B = mapping.slope, mapping.intercept
        from molass_legacy._MOLASS.SerialSettings import set_setting, UV_BASE_CONST, XRAY_BASE_CONST
        from molass_legacy.Mapping.MappingParams import get_mapper_opt_params
        """
        task: consistent set_setting() calls are required
        """
        method = ssd.get_baseline_method()  # ensure baseline method is set
        xr_type, uv_type = method_to_legacy_types(method)
        set_setting('use_xray_conc', False)
        set_setting('xray_baseline_opt', XRAY_BASE_CONST)
        set_setting('xray_baseline_type', xr_type)
        set_setting('uv_baseline_opt', UV_BASE_CONST)
        set_setting('uv_baseline_type', uv_type)
        self.opt_params = get_mapper_opt_params()

def make_mapped_info(ssd, mapping):
    """
    Create a MappedInfoProxy from the given mapping.
    This function creates a MappedInfoProxy object using the provided SecSaxsData
    and MappingInfo objects.

    Parameters
    ----------
    ssd : SecSaxsData
        The SecSaxsData object containing the data.
    mapping : MappingInfo
        The MappingInfo object containing the mapping information.
        
    Returns
    -------
    MappedInfoProxy
        The created MappedInfoProxy object.
    """
    return MappedInfoProxy(ssd, mapping)