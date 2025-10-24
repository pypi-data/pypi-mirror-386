from functools import partialmethod, wraps
from itertools import cycle

import matplotlib.pyplot as plt
import numpy as np

from astropy.timeseries import LombScargle

from .setup_logger import setup_logger
from .config import config
from .stats import wmean


def plot_settings(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # with plt.style.context('fast'):
        theme = 'dark_background' if config.dark_plots else 'fast'
        with plt.style.context(theme):
            return func(*args, **kwargs)
    return wrapper



class BlittedCursor:
    """ A cross-hair cursor using blitting for faster redraw. """
    def __init__(self, axes, vertical=True, horizontal=True, show_text=None,
                 transforms_x=None, transforms_y=None):
        import matplotlib # delay import
        if isinstance(axes, matplotlib.axes.Axes):
            axes = [axes]
        self.axes = axes
        self.background = None
        self.vertical = vertical
        self.horizontal = horizontal
        
        self.transforms_x = [lambda x:x for _ in axes] if transforms_x is None else transforms_x
        self.transforms_y = [lambda x:x for _ in axes] if transforms_y is None else transforms_y

        if horizontal:
            self.horizontal_line = [ax.axhline(color='k', lw=0.8, ls='--') for ax in axes]
        if vertical:
            self.vertical_line = [ax.axvline(color='k', lw=0.8, ls='--') for ax in axes]

        self.show_text = show_text
        if show_text is not None: # text location in axes coordinates
            self.text = [ax.text(0.72, 0.9, '', transform=ax.transAxes) for ax in axes]

        self._creating_background = False
        for ax in axes:
            ax.figure.canvas.mpl_connect('draw_event', self.on_draw)

    def on_draw(self, event):
        self.create_new_background()

    def set_cross_hair_visible(self, visible):
        if self.horizontal:
            need_redraw = [line.get_visible() != visible for line in self.horizontal_line]
        else:
            need_redraw = [line.get_visible() != visible for line in self.vertical_line]
        if self.horizontal:
            [line.set_visible(visible) for line in self.horizontal_line]
        if self.vertical:
            [line.set_visible(visible) for line in self.vertical_line]
        if self.show_text:
            self.text.set_visible(visible)
        return need_redraw

    def create_new_background(self):
        if self._creating_background:
            # discard calls triggered from within this function
            return
        self._creating_background = True
        self.set_cross_hair_visible(False)
        for ax in self.axes:
            ax.figure.canvas.draw()
        self.backgrounds = [ax.figure.canvas.copy_from_bbox(ax.bbox) for ax in self.axes]
        self.set_cross_hair_visible(True)
        self._creating_background = False

    def on_mouse_move(self, event):
        if self.background is None:
            self.create_new_background()
        if not event.inaxes:
            need_redraw = self.set_cross_hair_visible(False)
            if any(need_redraw):
                for ax, bkgd in zip(self.axes, self.backgrounds):
                    ax.figure.canvas.restore_region(bkgd)
                    ax.figure.canvas.blit(ax.bbox)
        else:
            self.set_cross_hair_visible(True)
            # update the line positions
            x, y = event.xdata, event.ydata
            X = [trans(x) for trans in self.transforms_x]
            Y = [trans(y) for trans in self.transforms_y]
            if self.horizontal:
                [line.set_ydata([y]) for line, y in zip(self.horizontal_line, Y)]
            if self.vertical:
                [line.set_xdata([x]) for line, x in zip(self.vertical_line, X)]
            if self.show_text:
                self.text.set_text(f'x={x:1.2f}, y={y:1.2f}')

            for ax, bkgd in zip(self.axes, self.backgrounds):
                ax.figure.canvas.restore_region(bkgd)
                if self.horizontal:
                    [ax.draw_artist(line) for line in self.horizontal_line]
                if self.vertical:
                    [ax.draw_artist(line) for line in self.vertical_line]
                if self.show_text:
                    ax.draw_artist(self.text)
                ax.figure.canvas.blit(ax.bbox)

def clickable_legend(fig, ax, leg):
    from matplotlib.text import Text
    handles, labels = ax.get_legend_handles_labels()
    for text in leg.get_texts():
        text.set_picker(True)

    def on_pick_legend(event):
        artist = event.artist
        if isinstance(artist, Text):
            try:
                h = handles[labels.index(artist.get_text())]
                alpha_text = {None:0.2, 1.0: 0.2, 0.2:1.0}[artist.get_alpha()]
                alpha_point = {None: 0.0, 1.0: 0.0, 0.2: 1.0}[artist.get_alpha()]
                try:
                    h[0].set_alpha(alpha_point)
                    h[2][0].set_alpha(alpha_point)
                except TypeError:
                    h.set_alpha(alpha_point)

                artist.set_alpha(alpha_text)
                fig.canvas.draw()
            except ValueError:
                pass
    return on_pick_legend

@plot_settings
def plot(self, ax=None, show_masked=False, instrument=None, time_offset=0,
         remove_50000=False, tooltips=True, show_title=False, show_legend=True, label=None, 
         jitter=None, N_in_label=False, versus_n=False, show_histogram=False, bw=False, **kwargs):
    """ Plot the RVs

    Args:
        ax (Axes, optional):
            Axis to plot to. Defaults to None.
        show_masked (bool, optional):
            Show masked points. Defaults to False.
        instrument (str, optional):
            Which instrument to plot. Defaults to None, or plot all instruments.
        time_offset (int, optional):
            Value to subtract from time. Defaults to 0.
        remove_50000 (bool, optional):
            Whether to subtract 50000 from time. Defaults to False.
        tooltips (bool, optional):
            Show information upon clicking a point. Defaults to True.
        show_title (bool, optional):
            Show the star name in the plot title. Defaults to False.
        show_legend (bool, optional):
            Show legend. Defaults to True.
        N_in_label (bool, optional):
            Show number of observations in legend. Defaults to False.
        versus_n (bool, optional):
            Plot RVs vs observation index instead of time. Defaults to False.
        show_histogram (bool, optional)
            Whether to show a panel with the RV histograms (per intrument).
            Defaults to False.
        bw (bool, optional):
            Adapt plot to black and white. Defaults to False.

    Returns:
        Figure: the figure
        Axes: the axis
    """
    logger = setup_logger()
    if self.N == 0:
        if self.verbose:
            logger.error('no data to plot')
        return

    if ax is None:
        if show_histogram:
            fig, (ax, axh) = plt.subplots(1, 2, constrained_layout=True, gridspec_kw={'width_ratios': [3, 1]})
        else:
            fig, ax = plt.subplots(1, 1, constrained_layout=True)
    elif ax == -1:
        ax = plt.gca()
        fig = ax.figure
    else:
        if show_histogram:
            ax, axh = ax
        fig = ax.figure

    kwargs.setdefault('ls', '')
    kwargs.setdefault('capsize', 0)
    kwargs.setdefault('ms', 4)

    if remove_50000:
        time_offset = 50000

    strict = kwargs.pop('strict', False)
    instruments = self._check_instrument(instrument, strict=strict)
    marker = kwargs.pop('marker', 'o')

    if bw:
        markers = cycle((marker, 'P', 's', '^', '*'))
    else:
        markers = cycle((marker,) * len(instruments))

    try:
        zorders = cycle(-np.argsort([getattr(self, i).error for i in instruments])[::-1])
    except AttributeError:
        zorders = cycle([1] * len(instruments))

    containers = {}
    for _i, inst in enumerate(instruments):
        s = self if self._child else getattr(self, inst)
        if s.mask.sum() == 0:
            continue

        if label is None:
            _label = f'{inst:10s} ({s.N})' if N_in_label else inst
            if not self.only_latest_pipeline:
                i, p = _label.split('_', 1)
                p = p.replace('_', '.')
                _label = f'{i}-{p}'
        else:
            if isinstance(label, list):
                _label = label[_i]
            else:
                _label = label

        if versus_n:
            x = np.arange(1, s.mtime.size + 1)
        else:
            x = s.mtime - time_offset

        container = ax.errorbar(x, s.mvrad, s.msvrad, label=_label, 
                                picker=True, marker=next(markers), zorder=next(zorders), **kwargs)


        containers[inst] = list(container)

        if show_histogram:
            kw = dict(histtype='step', bins='doane', orientation='horizontal')
            hlabel = f'{s.mvrad.std():.2f} {self.units}'
            axh.hist(s.mvrad, **kw, label=hlabel)

        if show_masked:
            if versus_n:
                pass
            else:
                ax.errorbar(s.time[~s.mask] - time_offset, s.vrad[~s.mask], s.svrad[~s.mask],
                            **kwargs, color=container[0].get_color())

    if show_masked:
        if versus_n:
            pass
            # ax.errorbar(self.time[~self.mask] - time_offset, self.vrad[~self.mask], self.svrad[~self.mask],
            #             label='masked', fmt='x', ms=10, color='k', zorder=-2)
        else:
            ax.errorbar(self.time[~self.mask] - time_offset, self.vrad[~self.mask], self.svrad[~self.mask],
                        label='masked', fmt='x', ms=10, color='k', zorder=-2)

    if show_legend:
        leg = ax.legend()
        on_pick_legend = clickable_legend(fig, ax, leg)
        plt.connect('pick_event', on_pick_legend)

    if tooltips:
        from matplotlib.lines import Line2D
        from matplotlib.collections import LineCollection
        annotations = []
        axes_artists = []
        selected_inds = []
        selected_insts = []

        def _cleanup():
            for text in annotations:
                text.remove()
                annotations.remove(text)
            for art in axes_artists:
                art.remove()
                axes_artists.remove(art)
            for ind in selected_inds:
                selected_inds.remove(ind)

        def on_press(event):
            # print('press', event.key)
            if event.key in ('r',):
                for i, inst in zip(selected_inds, selected_insts):
                    i = self._index_from_instrument_index(i, inst)
                    self.remove_point(i)
                _cleanup()
                fig.canvas.draw_idle()
            if event.key == 'escape':
                _cleanup()
                kp_cid = None
                for k, _f in fig.canvas.callbacks.callbacks['key_press_event'].items():
                    if _f._obj == on_press:
                        kp_cid = k
                if kp_cid is not None:
                    fig.canvas.callbacks.disconnect(k)
                fig.canvas.draw_idle()

        def on_pick_point(event):
            _cleanup()            
            artist = event.artist
            if isinstance(artist, (Line2D, LineCollection)):
                # print(event.ind, artist)
                if isinstance(artist, Line2D):
                    ind = event.ind
                    matching_instrument = [k for k, v in containers.items() if artist in v]
                    if len(matching_instrument) == 0:
                        return
                    inst = matching_instrument[0]

                    _s = getattr(self, inst)

                    if event.ind.size > 1:
                        mint, maxt = _s.mtime[ind].min(), _s.mtime[ind].max()
                        miny, maxy = _s.mvrad[ind].min(), _s.mvrad[ind].max()
                        axins = ax.inset_axes([0.1, 0.5, 0.5, 0.4],
                            xlim=(mint - 0.1 * (maxt - mint), maxt + 0.1 * (maxt - mint)), 
                            ylim=(miny - 0.1 * (maxy - miny), maxy + 0.1 * (maxy - miny)), 
                            xticklabels=[], yticklabels=[]
                            )
                        axins.errorbar(_s.mtime[ind], _s.mvrad[ind], _s.msvrad[ind], fmt='o', ms=3,
                                       color=artist.get_color())
                        axins.margins(x=0.5)
                        axins.autoscale_view()
                        rectangle_patch, connector_lines = ax.indicate_inset_zoom(axins, edgecolor="black")
                        axes_artists.append(axins)
                        axes_artists.append(rectangle_patch)
                        for line in connector_lines:
                            axes_artists.append(line)
                    else:
                        ind = event.ind[0]
                        selected_inds.append(ind)
                        selected_insts.append(inst)
                        # print(_s.mtime[ind], _s.mvrad[ind], _s.msvrad[ind])

                        text = f'{inst} ({ind})\n'
                        text += f'{_s.mtime[ind]:9.5f}\n'
                        text += f'RV: {_s.mvrad[ind]:.1f} ± {_s.msvrad[ind]:.1f}'

                        annotations.append(
                            ax.annotate(text, (_s.mtime[ind], _s.mvrad[ind]), xycoords='data',
                                        xytext=(5, 10), textcoords='offset points', fontsize=9,
                                        bbox={'boxstyle': 'round', 'fc': 'w'}, arrowprops=dict(arrowstyle="-"))
                        )
                    # ax.annotate(f'{inst}', (0.5, 0.5), xycoords=artist, ha='center', va='center')
                    fig.canvas.draw()
                    # print(event.ind, artist.get_label())

                    _ = fig.canvas.mpl_connect('key_press_event', on_press)

        plt.connect('pick_event', on_pick_point)


    if show_histogram:
        axh.legend()

    ax.minorticks_on()

    ax.set_ylabel(f'RV [{self.units}]')
    if versus_n:
        ax.set_xlabel('observation')
    else:
        if remove_50000:
            ax.set_xlabel('BJD - 2450000 [days]')
        else:
            ax.set_xlabel('BJD - 2400000 [days]')

    if show_title:
        ax.set_title(self.star, loc='right')

    # from matplotlib.backend_tools import ToolBase, ToolToggleBase
    # tm = fig.canvas.manager.toolmanager
    # class InfoTool(ToolToggleBase):
    #     description = "Show extra information about each observation"
    #     image = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'info.svg'))
    #     # def enable(self, *args, **kwargs):
    #     #     self.figure.add_axes([1, 0, 0.3, 1])
    #     #     self.figure.canvas.draw_idle()
    # from PIL import UnidentifiedImageError
    # try:
    #     tm.add_tool("infotool", InfoTool)
    #     fig.canvas.manager.toolbar.add_tool(tm.get_tool("infotool"), "toolgroup")
    #     raise UnidentifiedImageError
    # except AttributeError:
    #     pass
    # except UnidentifiedImageError:
    #     pass


    if config.return_self:
        return self
    
    if show_histogram:
        return fig, (ax, axh)
    
    return fig, ax


# @plot_fast
def plot_quantity(self, quantity, ax=None, show_masked=False, instrument=None,
                  time_offset=0, remove_50000=False, tooltips=False, show_legend=True,
                  N_in_label=False, **kwargs):
    logger = setup_logger()
    if self.N == 0:
        if self.verbose:
            logger.error('no data to plot')
        return

    if not hasattr(self, quantity):
        logger.error(f"cannot find '{quantity}' attribute")
        return

    if ax is None:
        fig, ax = plt.subplots(1, 1, constrained_layout=True)
    else:
        fig = ax.figure

    kwargs.setdefault('marker', 'o')
    kwargs.setdefault('ls', '')
    kwargs.setdefault('capsize', 0)
    kwargs.setdefault('ms', 4)

    if remove_50000:
        time_offset = 50000

    instruments = self._check_instrument(instrument)

    for inst in instruments:
        s = self if self._child else getattr(self, inst)
        label = f'{inst:10s} ({s.N})' if N_in_label else inst
        if not self.only_latest_pipeline:
            i, p = label.split('_', 1)
            p = p.replace('_', '.')
            label = f'{i}-{p}'

        y = getattr(s, quantity).copy()
        try:
            ye = getattr(s, quantity + '_err').copy()
        except AttributeError:
            ye = np.zeros_like(y)

        if (nans := np.isnan(y)).any():
            if self.verbose:
                logger.warning(f'{nans.sum()} NaN values for {inst}')
            ye[nans] = np.nan

        if np.isnan(y).all() or np.isnan(ye).all():
            lines, *_ = ax.errorbar([], [], [],
                                    label=label, picker=True, **kwargs)
            continue

        lines, *_ = ax.errorbar(s.mtime - time_offset, y[s.mask], ye[s.mask],
                                label=label, picker=True, **kwargs)

        if show_masked:
            ax.errorbar(s.time[~s.mask] - time_offset, y[~s.mask], ye[~s.mask],
                        **kwargs, color=lines.get_color())

    if show_masked:
        ax.errorbar(self.time[~self.mask] - time_offset,
                    getattr(self, quantity)[~self.mask],
                    getattr(self, quantity + '_err')[~self.mask],
                    label='masked', fmt='x', ms=10, color='k', zorder=-2)

    if show_legend:
        leg = ax.legend()
        on_pick_legend = clickable_legend(fig, ax, leg)
        plt.connect('pick_event', on_pick_legend)

    ax.minorticks_on()

    delta = 'Δ' if self._did_adjust_means else ''

    ylabel = {
        quantity.lower(): quantity,
        'fwhm': f'{delta}FWHM [{self.units}]',
        'bispan': f'{delta}BIS [{self.units}]',
        'rhk': r"$\log$ R'$_{HK}$",
        'berv': 'BERV [km/s]',
    }

    ax.set_ylabel(ylabel[quantity.lower()])

    if remove_50000:
        ax.set_xlabel('BJD - 2450000 [days]')
    else:
        ax.set_xlabel('BJD - 2400000 [days]')

    if config.return_self:
        return self
    else:
        return fig, ax


plot_fwhm = partialmethod(plot_quantity, quantity='fwhm')
plot_bispan = partialmethod(plot_quantity, quantity='bispan')
plot_contrast = partialmethod(plot_quantity, quantity='contrast')
plot_rhk = partialmethod(plot_quantity, quantity='rhk')
plot_berv = partialmethod(plot_quantity, quantity='berv')


def plot_xy(self, x, y, ax=None, instrument=None, show_legend=True, **kwargs):
    logger = setup_logger()
    if self.N == 0:
        if self.verbose:
            logger.error('no data to plot')
        return

    if ax is None:
        fig, ax = plt.subplots(1, 1, constrained_layout=True)
    else:
        fig = ax.figure

    kwargs.setdefault('marker', 'o')
    kwargs.setdefault('ls', '')
    kwargs.setdefault('capsize', 0)
    kwargs.setdefault('ms', 4)

    instruments = self._check_instrument(instrument)

    for inst in instruments:
        s = self if self._child else getattr(self, inst)
        label = inst

        missing = False
        try:
            xdata = getattr(s, x).copy()
        except AttributeError:
            missing = True
        try:
            e_xdata = getattr(s, x + '_err').copy()
        except AttributeError:
            e_xdata = np.zeros_like(xdata)

        try:
            ydata = getattr(s, y).copy()
        except AttributeError:
            missing = True
        try:
            e_ydata = getattr(s, y + '_err').copy()
        except AttributeError:
            e_ydata = np.zeros_like(ydata)

        if missing:
            lines, *_ = ax.errorbar([], [], [],
                                    label=label, picker=True, **kwargs)
            continue

        ax.errorbar(xdata[s.mask], ydata[s.mask], e_xdata[s.mask], e_ydata[s.mask],
                    label=label, **kwargs)

    # if show_masked:
    #     ax.errorbar(self.time[~self.mask] - time_offset,
    #                 getattr(self, quantity)[~self.mask],
    #                 getattr(self, quantity + '_err')[~self.mask],
    #                 label='masked', fmt='x', ms=10, color='k', zorder=-2)

    if show_legend:
        leg = ax.legend()
        on_pick_legend = clickable_legend(fig, ax, leg)
        plt.connect('pick_event', on_pick_legend)

    ax.minorticks_on()

    delta = 'Δ' if self._did_adjust_means else ''

    # ylabel = {
    #     quantity.lower(): quantity,
    #     'fwhm': f'{delta}FWHM [{self.units}]',
    #     'bispan': f'{delta}BIS [{self.units}]',
    #     'rhk': r"$\log$ R'$_{HK}$",
    #     'berv': 'BERV [km/s]',
    # }

    # ax.set_ylabel(ylabel[quantity.lower()])

    if config.return_self:
        return self
    else:
        return fig, ax


# @plot_fast
def gls(self, ax=None, label=None, instrument=None, 
        fap=True, fap_method='baluev', adjust_means=config.adjust_means_gls,
        picker=True, **kwargs):
    """
    Calculate and plot the Generalised Lomb-Scargle periodogram of the radial
    velocities.

    Args:
        ax (matplotlib.axes.Axes):
            The matplotlib axes to plot on. If None, a new figure will be
            created.
        label (str):
            The label to use for the plot.
        instrument (str or list):
            Which instruments' data to include in the periodogram. Default is
            all instruments.
        fap (bool or float):
            Whether to show the false alarm probability. A value (not a
            percentage) can be provided to display a given FAP. Default is True.
        fap_method (str):
            Method used to estimate the FAP, passed directly to
            `astropy.timeseries.LombScargle`. Default is 'baluev'.
        adjust_means (bool):
            Whether to adjust (subtract) the weighted means of each instrument.
            Default is `config.adjust_means_gls`.
    """
    logger = setup_logger()
    if self.N == 0:
        if self.verbose:
            logger.error('no data to compute gls')
        return

    if not self._did_adjust_means and not adjust_means:
        logger.warning('gls() called before adjusting instrument means, '
                       'consider using the `adjust_means` argument')

    if instrument is not None:
        strict = kwargs.pop('strict', False)
        instrument = self._check_instrument(instrument, strict=strict, log=True)
        if instrument is None:
            return

        instrument_mask = np.isin(self.instrument_array, instrument)
        t = self.time[instrument_mask & self.mask].copy()
        y = self.vrad[instrument_mask & self.mask].copy()
        e = self.svrad[instrument_mask & self.mask].copy()
        if self.verbose:
            logger.info(f'calculating periodogram for instrument {instrument}')

        if adjust_means and not self._child:
            if self.verbose:
                logger.info('adjusting instrument means before gls')
            means = np.zeros_like(y)
            for i in instrument:
                mask = self.instrument_array[instrument_mask & self.mask] == i
                if len(y[mask]) > 0:
                    means = means + wmean(y[mask], e[mask]) * mask
            y = y - means

    else:
        t = self.time[self.mask].copy()
        y = self.vrad[self.mask].copy()
        e = self.svrad[self.mask].copy()

        if adjust_means and not self._child:
            if self.verbose:
                logger.info('adjusting instrument means before gls')
            means = np.zeros_like(y)
            for i in self.instruments:
                mask = self.instrument_array[self.mask] == i
                if len(y[mask]) > 0:
                    means = means + wmean(y[mask], e[mask]) * mask
            y = y - means

    self._gls = gls = LombScargle(t, y, e)

    maximum_frequency = kwargs.pop('maximum_frequency', 1.0)
    minimum_frequency = kwargs.pop('minimum_frequency', None)
    samples_per_peak = kwargs.pop('samples_per_peak', 10)
    kw = {
        'maximum_frequency': maximum_frequency,
        'minimum_frequency': minimum_frequency,
        'samples_per_peak': samples_per_peak
    }

    freq, power = gls.autopower(**kw)

    show_peak_fap = kwargs.pop('show_peak_fap', False)

    if ax is None:
        fig, ax = plt.subplots(1, 1, constrained_layout=True)
    else:
        fig = ax.figure

    if kwargs.pop('fill_between', False):
        kwargs.pop('lw', None)
        ax.fill_between(1/freq, 0, power, label=label, lw=0, **kwargs)
        ax.set_xscale('log')
    else:
        ax.semilogx(1/freq, power, picker=picker, label=label, **kwargs)

    if fap:
        fap_level = 0.01
        if isinstance(fap, float):
            fap_level = fap

        fap = gls.false_alarm_level(fap_level, method=fap_method, **kw)

        # if fap > 0.05 and fap_method == 'baluev':
        #     logger.warning('FAP is high (>5%), the analytical estimate may be underestimated. Using the bootstrap method instead.')
        #     fap = gls.false_alarm_level(fap_level, method='bootstrap')

        ax.axhline(fap, color='k', alpha=0.2, zorder=-1)

    if show_peak_fap:
        peak_per = 1/freq[np.argmax(power)]
        peak_power = np.max(power)
        peak_fap = gls.false_alarm_probability(peak_power, method=fap_method, **kw)
        ax.plot(peak_per, peak_power, 'o', color='r', zorder=1)
        ax.annotate(f'{peak_per:1.3f} days\nFAP: {peak_fap:1.1e}', (peak_per, peak_power), 
                    va='top', textcoords='offset points', xytext=(10, 0), zorder=1)

    ax.set(xlabel='Period [days]', ylabel='Normalized power', ylim=(0, None))
    ax.minorticks_on()

    if label is not None:
        ax.legend()

    if ax.get_legend() is not None:
        from matplotlib.text import Text
        leg = ax.get_legend()
        for text in leg.get_texts():
            text.set_picker(True)

        def on_pick_legend(event):
            handles, labels = ax.get_legend_handles_labels()
            artist = event.artist
            if isinstance(artist, Text):
                # print('handles:', handles)
                # print('labels:', labels)
                # print(artist.get_text())
                try:
                    h = handles[labels.index(artist.get_text())]
                    alpha_text = {None:0.2, 1.0: 0.2, 0.2:1.0}[artist.get_alpha()]
                    alpha_point = {None: 0.0, 1.0: 0.0, 0.2: 1.0}[artist.get_alpha()]
                    h.set_alpha(alpha_point)
                    artist.set_alpha(alpha_text)
                    fig.canvas.draw()
                except ValueError:
                    pass

        if 'pick_event' not in fig.canvas.callbacks.callbacks:
            plt.connect('pick_event', on_pick_legend)


    if config.return_self:
        return self
    else:
        return fig, ax


# @plot_fast
def gls_quantity(self, quantity, ax=None, instrument=None,
                 fap=True, fap_method='baluev',
                 adjust_means=True, picker=True, **kwargs):
    """
    Calculate and plot the Generalised Lomb-Scargle periodogram of the given
    quantity (e.g. fwhm, rhk, etc.)

    Args:
        quantity (str):
            The quantity to calculate for which to compute the periodogram.
        ax (matplotlib.axes.Axes):
            The matplotlib axes to plot on. If None, a new figure will be
            created.
        instrument (str or list):
            Which instruments' data to include in the periodogram. Default is
            all instruments.
        fap (bool or float):
            Whether to show the false alarm probability. A value (not a
            percentage) can be provided to display a given FAP. Default is True.
        fap_method (str):
            Method used to estimate the FAP, passed directly to
            `astropy.timeseries.LombScargle`. Default is 'baluev'.
        adjust_means (bool):
            Whether to adjust (subtract) the weighted means of each instrument.
            Default is `config.adjust_means_gls`.
    """
    logger = setup_logger()
    if not hasattr(self, quantity):
        if self.verbose:
            logger.error(f"cannot find '{quantity}' attribute")
        return

    if self.N == 0:
        if self.verbose:
            logger.error('no data to compute gls')
        return

    if not self._did_adjust_means and not adjust_means:
        logger.warning('gls() called before adjusting instrument means, '
                       'consider using the `adjust_means` argument')

    strict = kwargs.pop('strict', False)
    instrument = self._check_instrument(instrument, strict=strict, log=True)
    if instrument is None:
        return

    instrument_mask = np.isin(self.instrument_array, instrument)
    final_mask = instrument_mask & self.mask

    t = self.time[final_mask].copy()
    y = getattr(self, quantity)[final_mask].copy()
    try:
        ye = getattr(self, quantity + '_err')[final_mask].copy()
    except AttributeError:
        ye = None

    if self.verbose:
        logger.info(f'calculating periodogram for instrument {instrument}')

    nan_mask = np.isnan(y)
    if nan_mask.any():
        if self.verbose:
            logger.warning(f'{quantity} contains NaNs, ignoring them')

    if adjust_means and not self._child:
        if self.verbose:
            logger.info('adjusting instrument means before gls')
        means = np.zeros_like(y)
        for i in instrument:
            mask = (self.instrument_array[final_mask] == i) & ~nan_mask
            if len(y[mask]) > 0:
                # print(wmean(y[mask], ye[mask]))
                means += wmean(y[mask], ye[mask]) * mask
        y = y - means

    t = t[~nan_mask]
    y = y[~nan_mask]
    ye = ye[~nan_mask]

    if len(y) == 0:
        logger.error('no data left to compute gls after removing NaNs')
        return

    if ax is None:
        fig, ax = plt.subplots(1, 1, constrained_layout=True)
    else:
        fig = ax.figure

    maximum_frequency = kwargs.pop('maximum_frequency', 1.0)
    minimum_frequency = kwargs.pop('minimum_frequency', None)
    samples_per_peak = kwargs.pop('samples_per_peak', 10)
    kw = {
        'maximum_frequency': maximum_frequency,
        'minimum_frequency': minimum_frequency,
        'samples_per_peak': samples_per_peak
    }

    gls = LombScargle(t, y, ye)
    freq, power = gls.autopower(**kw)

    ax.semilogx(1/freq, power, picker=picker, **kwargs)

    if fap:
        fap_level = 0.01
        if isinstance(fap, float):
            fap_level = fap

        fap = gls.false_alarm_level(fap_level, method=fap_method, **kw)

        # if fap > 0.05 and fap_method == 'baluev':
        #     logger.warning('FAP is high (>5%), the analytical estimate may be underestimated. Using the bootstrap method instead.')
        #     fap = gls.false_alarm_level(fap_level, method='bootstrap', **kw)

        ax.axhline(fap, color='k', alpha=0.2, zorder=-1)

    ax.set(xlabel='Period [days]', ylabel='Normalized power', ylim=(0, None))
    ax.minorticks_on()

    if config.return_self:
        return self
    else:
        return fig, ax


gls_fwhm = partialmethod(gls_quantity, quantity='fwhm')
gls_bispan = partialmethod(gls_quantity, quantity='bispan')
gls_rhk = partialmethod(gls_quantity, quantity='rhk')



def window_function(self, ax1=None, ax2=None, instrument=None, crosshair=False, **kwargs):
    """
    Calculate and plot the window function of the observed times.

    Args:
        ax1 (matplotlib.axes.Axes):
            An axes to plot the window function vs period. If None, a new figure
            will be created.
        ax2 (matplotlib.axes.Axes):
            An axes to plot the periodogram vs frequency. If None, a new figure
            will be created.
        instrument (str or list):
            Which instruments' data to include in the window function.
        crosshair (bool):
            If True, a crosshair will be drawn on the plot.
    """
    logger = setup_logger()

    if self.N == 0:
        if self.verbose:
            logger.error('no data to compute window function')
        return

    if ax1 is None:
        fig, (ax1, ax2) = plt.subplots(2, 1, constrained_layout=True)
    else:
        fig = ax1.figure

    if instrument is not None:
        strict = kwargs.pop('strict', False)
        instrument = self._check_instrument(instrument, strict=strict)
        if instrument is not None:
            instrument_mask = np.isin(self.instrument_array, instrument)
            t = self.time[instrument_mask & self.mask]
            ye = self.svrad[instrument_mask & self.mask]
            if self.verbose:
                logger.info(f'calculating window function for instrument {instrument}')
    else:
        t = self.time[self.mask]
        ye = self.svrad[self.mask]

    wf = LombScargle(t, np.ones_like(t), ye / np.std(ye),
                     fit_mean=False, center_data=False)

    freq, power = wf.autopower(maximum_frequency=1.1, 
                               samples_per_peak=20, method='cython')
    ax1.semilogx(1/freq, power, **kwargs)
    ax1.set(xlabel='Period [days]', ylabel='Window function')

    ax2.plot(freq, power, **kwargs)
    ax2.set(xlabel='Frequency [1/day]', ylabel='Window function')

    for x in (365.25, 1.0, 1 - 1.0/365.25):
        ax1.axvline(x, color='k', alpha=0.2, zorder=-1)
        ax2.axvline(1/x, color='k', alpha=0.2, zorder=-1)
    
    if crosshair:
        blitted_cursor = BlittedCursor((ax1, ax2), horizontal=False,
                                    transforms_x=(lambda x:x, lambda x:1/x))
        fig.canvas.mpl_connect('motion_notify_event', blitted_cursor.on_mouse_move)
        return fig, (ax1, ax2), blitted_cursor
        # from matplotlib.widgets import MultiCursor
        # cursor = MultiCursor(fig.canvas, (ax1, ax2), color='r',
        #                      lw=0.5, horizOn=False, vertOn=True)
        # return fig, (ax1, ax2), (cursor)
    else:
        return fig, (ax1, ax2)

def histogram_svrad(self, ax=None, instrument=None, label=None):
    """ Plot an histogram of the radial velocity uncertainties. 
    
    Args:
        ax (matplotlib.axes.Axes):
            The matplotlib axes to plot on. If None, a new figure will be
            created.
        instrument (str or list):
            Which instruments' data to include in the histogram.
        label (str):
            The label to use for the plot.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, constrained_layout=True)
    else:
        fig = ax.figure

    instruments = self._check_instrument(instrument)

    for inst in instruments:
        s = self if self._child else getattr(self, inst)

        if label is None:
            _label = inst
            if not self.only_latest_pipeline:
                i, p = _label.split('_', 1)
                p = p.replace('_', '.')
                _label = f'{i}-{p}'
        else:
            _label = label

        kw = dict(bins=40, histtype='step', density=False, lw=2)
        ax.hist(s.msvrad, label=_label, **kw)
    ax.legend()
    ax.set(xlabel=f'RV uncertainty [m/s]', ylabel='Number')

