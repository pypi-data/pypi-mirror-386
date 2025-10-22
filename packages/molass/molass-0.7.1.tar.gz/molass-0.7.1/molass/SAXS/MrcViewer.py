"""
SAXS.MrcViewer.py
"""
import matplotlib.pylab as plt
from molass_legacy.Saxs.EdPlotter import ed_scatter

def show_mrc(mrc_file):
    """show_mrc(mrc_file)
    
    Displays a 3D scatter plot and a 2D projection of the data in an MRC file.

    Parameters
    ----------
    mrc_file : str
        Path to the MRC file to be displayed.

    Returns
    -------
    None
    """
    import mrcfile
    with mrcfile.open(mrc_file) as mrc:
        data = mrc.data
    plt.style.use('dark_background')        
    fig  = plt.figure(figsize=(16,7))
    ax1 = fig.add_subplot(121, projection='3d')
    ax2 = fig.add_subplot(122, aspect='equal')
    axes = [ax1, ax2]
    ed_scatter(fig, axes, data, mrc_file)
    plt.style.use('default')