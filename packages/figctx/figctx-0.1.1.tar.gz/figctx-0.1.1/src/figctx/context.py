import matplotlib.pyplot as plt
from .palette import *
from contextlib import contextmanager
from cycler import cycler


def mti(mm):
    return mm / 25.4


# single figure context manager
@contextmanager
def single(width_mm, height_mm, save_to, nrows=1, ncols=1):
    
    color_cycle = cycler(color=palette_categorical)

    custom_rc = {
        'font.family': 'Arial',
        'font.size': 7,
        'axes.prop_cycle': color_cycle,
        'axes.linewidth': 1,
        'lines.linewidth': 1.5,
        'lines.markersize': 3.5,
        'figure.dpi': 500,
        'savefig.dpi': 500,
    }

    with plt.rc_context(rc=custom_rc):
        fig, axes = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            figsize=(mti(width_mm), mti(height_mm)),
            layout='constrained'
        )

        if isinstance(axes, (list, tuple, plt.Axes)):
            axs = axes.ravel() if hasattr(axes, 'ravel') else [axes]
        else:
            axs = axes

        for ax in axs:
            ax.tick_params(
                direction='in',
                width=1,
                length=3,
                pad=2
            )

        if len(axs) == 1:
            yield fig, axs[0]
        else:
            yield fig, axs

        fig.savefig(save_to)
        plt.close(fig) 


# multi figure context manager
@contextmanager
def multi(
    width_mm, height_mm,
    nrows, ncols,  # (nrows, ncols) subfigure grid
    width_ratios, height_ratios,
    save_to,
    wspace=0.08,
    hspace=0.08,
    constrained=True,
):

    color_cycle = cycler(color=palette_categorical)

    custom_rc = {
        'font.family': 'Arial',
        'font.size': 7,
        'axes.prop_cycle': color_cycle,
        'axes.linewidth': 1,
        'lines.linewidth': 1.5,
        'lines.markersize': 3.5,
        'figure.dpi': 500,
        'savefig.dpi': 500,
    }

    with plt.rc_context(rc=custom_rc):
        
        fig = plt.figure(figsize=(mti(width_mm), mti(height_mm))
                         , constrained_layout=constrained)

        subfigs = fig.subfigures(nrows, ncols, 
                                 wspace=wspace, hspace=hspace, 
                                 width_ratios=width_ratios, height_ratios=height_ratios)

        if nrows==1 and ncols==1:
            subfigs = [subfigs]

        yield fig, subfigs
        
        fig.savefig(save_to)
        plt.close(fig)


# Pennylane-fit circuit context
@contextmanager
def circuit(width_mm, height_mm): # pragma: no cover

    custom_rc = {
        'font.family': 'Arial',
        'font.size': 7,
        'axes.linewidth': 1,
        'lines.linewidth': 1.5,
        'figure.dpi': 500,
        'savefig.dpi': 500,
        'patch.facecolor': '#E4F1F7',
        'patch.edgecolor': '#0D4A70',
        'patch.linewidth': 1.5,
        'patch.force_edgecolor': True,
        'lines.color': '#0D4A70',
        'lines.linewidth': 1.5,
    }

    figsize=(mti(width_mm), mti(height_mm))

    with plt.rc_context(rc=custom_rc):
        fig, _ = plt.subplots()
        
        yield fig, figsize
        
        plt.close(fig) 