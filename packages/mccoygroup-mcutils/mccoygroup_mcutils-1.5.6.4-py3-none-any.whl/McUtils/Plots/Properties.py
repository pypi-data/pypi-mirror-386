"""
Handles all the nastiness of Matplotlib properties so that we can use a more classically python plotting method
"""

from .. import Devutils as dev
from .Backends import DPI_SCALING
from .Styling import Styled, PlotLegend

__all__ = [
    "GraphicsPropertyManager",
    "GraphicsPropertyManager3D"
]

__reload_hook__ = [".Styling"]

class GraphicsPropertyManager:
    """
    Manages properties for Graphics objects so that concrete GraphicsBase instances don't need to duplicate code, but
    at the same time things that build off of GraphicsBase don't need to implement all of these properties
    """

    def __init__(self, graphics, figure, axes, managed=False):
        self.graphics = graphics
        self.managed = managed # if there's an external manager
        self.figure = figure
        self.axes = axes
        self._figure_label = None
        self._plot_label = None
        self._style_lists = None
        self._plot_legend = None
        self._legend_style = None
        self._axes_labels = None
        self._frame = None
        self._frame_style = None
        self._plot_range = None
        self._ticks = None
        self._scale = None
        self._ticks_style = None
        self._ticks_label_style = None
        self._aspect_ratio = None
        self._image_size = None
        self._padding = None
        self._background = None
        self._colorbar = None
        self._cbar_obj = None
        self._spacings = None

    @property
    def figure_label(self):
        return self._figure_label
    @figure_label.setter
    def figure_label(self, label):
        self._figure_label = label
        if not self.managed:
            if label is None:
                self.figure.set_figure_label("")
            elif isinstance(label, Styled):
                self.figure.set_figure_label(*label.val, **label.opts)
            else:
                self.figure.set_figure_label(label)

    @property
    def plot_label(self):
        return self._plot_label
    @plot_label.setter
    def plot_label(self, label):
        self._plot_label = label
        if label is None:
            self.axes.set_plot_label("")
        elif isinstance(label, Styled):
            self.axes.set_plot_label(*label.val, **label.opts)
        elif Styled.could_be(label):
            label = Styled.construct(label)
            self.axes.set_plot_label(*label.val, **label.opts)
        else:
            self.axes.set_plot_label(label)

    @property
    def style_list(self):
        return self._style_lists
    @style_list.setter
    def style_list(self, props):
        if props is not None:
            updated = False
            if self._style_lists is None:
                updated = True
                self._style_lists = props
            else:
                for k,v in props.items():
                    if (
                            k not in self._style_lists
                            or v != self._style_lists[k]
                    ):
                        # print(k, v, self._style_lists[k], v == self._style_lists[k])
                        self._style_lists[k] = v
                        updated = True
            if updated:
                self.axes.set_style_list(props)

    # set plot legend
    @property
    def plot_legend(self):
        return self._plot_legend
    @plot_legend.setter
    def plot_legend(self, legend):
        self._plot_legend = legend

        if PlotLegend.could_be_legend(legend):
            self._plot_legend = PlotLegend.construct(legend)
        elif legend is True:
            pass
        else:
            raise NotImplementedError("inferred legends not properly supported..")
            artists = self.graphics.artists
            if artists is not None:
                if legend is None:
                    for a in artists:
                        a.remove_label("")
                elif legend is True:
                    pass
                elif isinstance(legend, Styled):
                    for a in artists:
                        a.set_label(legend.val, **legend.opts)
                elif Styled.could_be(legend):
                    legend = Styled.construct(legend)
                    for a in artists:
                        a.set_label(legend.val, **legend.opts)
                else:
                    for a in artists:
                        a.set_label(legend)

    @property
    def legend_style(self):
        return self._legend_style
    @legend_style.setter
    def legend_style(self, style):
        self._legend_style = style


    # # set axes labels
    # @property
    # def axes(self):
    #     return self._axes
    # @axes.setter
    # def axes(self, axes):
    #     ...

    # set axes labels
    @property
    def axes_labels(self):
        return self._axes_labels
    @axes_labels.setter
    def axes_labels(self, labels):
        if self._axes_labels is None:
            self._axes_labels = (self.axes.get_xlabel(), self.axes.get_ylabel())
        try:
            xlab, ylab = labels
        except ValueError:
            xlab, ylab = labels = (labels, self._axes_labels[1])

        self._axes_labels = tuple(labels)
        if xlab is None:
            self.axes.set_xlabel("")
        elif isinstance(xlab, Styled):
            self.axes.set_xlabel(xlab.val[0], **xlab.opts)
        elif Styled.could_be(xlab):
            xlab = Styled.construct(xlab)
            self.axes.set_xlabel(*xlab.val, **xlab.opts)
        else:
            self.axes.set_xlabel(xlab)
        if ylab is None:
            self.axes.set_ylabel("")
        elif isinstance(ylab, Styled):
            self.axes.set_ylabel(*ylab.val, **ylab.opts)
        elif Styled.could_be(ylab):
            ylab = Styled.construct(ylab)
            self.axes.set_ylabel(*ylab.val, **ylab.opts)
        else:
            self.axes.set_ylabel(ylab)

    # set plot ranges
    @property
    def plot_range(self):
        if self._plot_range is None:
            pr = (list(sorted(self.axes.get_xlim())), list(sorted(self.axes.get_ylim())))
        else:
            pr = self._plot_range
        return pr
    @plot_range.setter
    def plot_range(self, ranges):
        if self._plot_range is None:
            self._plot_range = (self.axes.get_xlim(), self.axes.get_ylim())
        try:
            x, y = ranges
        except ValueError:
            x, y = ranges = (self._plot_range[0], ranges)
        else:
            if isinstance(x, int) or isinstance(x, float):
                x, y = ranges = (self._plot_range[0], ranges)

        self._plot_range = tuple(ranges)

        if isinstance(x, Styled):  # name feels wrong here...
            self.axes.set_xlim(*x.val, **x.opts)
        elif Styled.could_be(x):
            x = Styled.construct(x)
            self.axes.set_xlim(*x.val, **x.opts)
        elif x is not None:
            self.axes.set_xlim(x)
        if isinstance(y, Styled):
            self.axes.set_ylim(*y.val, **y.opts)
        elif Styled.could_be(y):
            y = Styled.construct(y)
            self.axes.set_ylim(*y.val, **y.opts)
        elif y is not None:
            self.axes.set_ylim(y)


    @property
    def absolute_plot_range(self):
        a, b = self.plot_range
        if a is None:
            a = self.axes.get_xlim()
        if b is None:
            b = self.axes.get_ylim()
        return a, b

    # set plot ticks
    @property
    def ticks(self):
        return self._ticks
    def _set_ticks(self, x,
                   *,
                   set_ticks, set_locator, set_minor_locator,
                   set_formatter, set_minor_formatter,
                   **opts):
        #TODO: make this backend independent
        import matplotlib.ticker as ticks
        inherit_opts = dict(
            set_ticks = set_ticks,
            set_locator = set_locator,
            set_minor_locator = set_minor_locator,
            set_formatter=set_formatter,
            set_minor_formatter=set_minor_formatter
        )

        if isinstance(x, Styled):
            self._set_ticks(*x.val,
                            **inherit_opts,
                            **dict(opts, **x.opts)
                            )
        elif Styled.could_be(x):
            x = Styled.construct(x)
            self._set_ticks(*x.val,
                            **inherit_opts,
                            **dict(opts, **x.opts)
                            )
        elif isinstance(x, ticks.Locator):
            if set_locator is not None:
                set_locator(x)

            minor = opts.get('minor', False)
            if minor is not False and minor is not None:
                if minor is True:
                    minor = ticks.AutoMinorLocator()
                elif dev.is_list_like(minor):
                    minor = ticks.FixedLocator(minor)
                elif dev.is_number(minor):
                    minor = ticks.MultipleLocator(minor)
                if set_minor_locator is not None:
                    set_minor_locator(minor)

            labels = opts.get('labels', True)
            if labels is not True:
                if isinstance(labels, str):
                    labels = ticks.StrMethodFormatter(labels)
                elif labels is False:
                    labels = ticks.NullFormatter()
                elif dev.is_list_like(labels):
                    labels = ticks.FixedFormatter(labels)
                elif dev.is_dict_like(labels):
                    labels = ticks.ScalarFormatter(**labels)
                if set_formatter is not None:
                    set_formatter(labels)

            minor_labels = opts.get('minor_labels', False)
            if minor_labels is not False:
                if isinstance(minor_labels, str):
                    minor_labels = ticks.StrMethodFormatter(minor_labels)
                elif minor_labels is True:
                    minor_labels = ticks.ScalarFormatter()
                elif dev.is_list_like(minor_labels):
                    minor_labels = ticks.FixedFormatter(minor_labels)
                elif dev.is_dict_like(minor_labels):
                    minor_labels = ticks.ScalarFormatter(**minor_labels)
                if set_minor_formatter is not None:
                    set_minor_formatter(minor_labels)
            # set_ticks(**opts)
        elif dev.str_is(x, 'auto'):
            self._set_ticks(ticks.AutoLocator(),
                            **inherit_opts,
                            **opts
                            )
        elif dev.is_list_like(x):
            if len(x) == 2 and dev.is_dict_like(x[1]):
                self._set_ticks(x[0],
                            **inherit_opts,
                                **dict(opts, **x[1])
                                )
            elif len(x) == 2 and isinstance(x[0], ticks.Locator):
                self._set_ticks(x[0],
                            **inherit_opts,
                                **dict(opts, minor=x[1])
                                )
            elif len(x) == 2 and dev.is_list_like(x[0]):
                self._set_ticks(ticks.FixedLocator(x[0]),
                            **inherit_opts,
                                labels=x[1],
                                **opts)
            else:
                self._set_ticks(ticks.FixedLocator(x),
                            **inherit_opts,
                                **opts)
        elif dev.is_number(x):
            self._set_ticks(ticks.MultipleLocator(x),
                            **inherit_opts,
                            **opts)
        elif x is not None:
            set_ticks(x, **opts)
    def _set_xticks(self, x, **opts):
        return self._set_ticks(x,
                               set_ticks=self.axes.set_xticks,
                               set_locator=self.axes.xaxis.set_major_locator,
                               set_minor_locator=self.axes.xaxis.set_minor_locator,
                               set_formatter=self.axes.xaxis.set_major_formatter,
                               set_minor_formatter=self.axes.xaxis.set_minor_formatter,
                               **opts
                               )

    def _set_yticks(self, y, **opts):
        return self._set_ticks(y,
                               set_ticks=self.axes.set_yticks,
                               set_locator=self.axes.yaxis.set_major_locator,
                               set_minor_locator=self.axes.yaxis.set_minor_locator,
                               set_formatter=self.axes.yaxis.set_major_formatter,
                               set_minor_formatter=self.axes.yaxis.set_minor_formatter,
                               # set_minor_locator=self.axes.yaxis.set_minor_locator,
                               **opts
                               )

    @ticks.setter
    def ticks(self, ticks):
        if self._ticks is None:
            self._ticks = (self.axes.get_xticks(), self.axes.get_yticks())
        try:
            x, y = ticks
        except (ValueError, TypeError):
            if isinstance(ticks, bool):
                x, y = ticks = (ticks, ticks)
            else:
                x, y = ticks = (self._ticks[0], ticks)
        if isinstance(y, dict):
            opts = y
            try:
                x, y = x
            except (ValueError, TypeError):
                if isinstance(x, bool):
                    x, y = ticks = (x, x)
                else:
                    x, y = ticks = (self._ticks[0], x)
        else:
            opts = {}

        self._ticks = ticks
        self._set_xticks(x, **opts)
        self._set_yticks(y, **opts)

    @property
    def ticks_style(self):
        return self._ticks_style
    @ticks_style.setter
    def ticks_style(self, ticks_style):
        if self._ticks_style is None:
            self._ticks_style = (None,) * 2
        if isinstance(ticks_style, dict):
            ticks_style = (ticks_style, ticks_style)
        try:
            x, y = ticks_style
        except ValueError:
            x, y = ticks_style = (ticks_style, ticks_style)
        self._ticks_style = ticks_style
        if x is not None:
            if x is True:
                x = dict(bottom=True, labelbottom=True)
            elif x is False:
                x = dict(bottom=False, top=False, labelbottom=False, labeltop=False)
            self.axes.set_xtick_style(
                **x
            )
        if y is not None:
            if y is True:
                y = dict(left=True, labelleft=True)
            elif y is False:
                y = dict(left=False, right=False, labelleft=False, labelright=False)
            self.axes.set_ytick_style(
                **y
            )
    @property
    def frame_style(self):
        return self._frame_style
    @frame_style.setter
    def frame_style(self, f_style):
        if self._frame_style is None:
            self._frame_style = ((None, None), (None, None))
        if isinstance(f_style, dict):
            f_style = ((f_style, f_style), (f_style, f_style))

        try:
            x, y = f_style
        except ValueError:
            x, y = f_style = (f_style, f_style)
        if isinstance(y, dict):
            y = (y, y)
        if isinstance(x, dict):
            x = (x, x)
        if len(y) == 2:
            b, t = y
        else:
            b = t = y
        if len(x) == 2:
            l, r = x
        else:
            l = r = x

        self._frame_style = ((l, r), (b, t))
        self.axes.set_frame_style(
            self._frame_style
        )

    ticks_label_base_styles = {
        'size', 'color',
        'top', 'left', 'right', 'bottom'
    }
    ticks_label_style_remapping={'fontsize':'size', 'fontcolor':'color'}
    @classmethod
    def clean_tick_label_styles(cls, k):
        if k.startswith('label'):
            k = k[5:]
        if k in cls.ticks_label_base_styles:
            k = 'label' + k
        k = cls.ticks_label_style_remapping.get(k, k)
        return k

    @property
    def ticks_label_style(self):
        return self._ticks_label_style
    @ticks_label_style.setter
    def ticks_label_style(self, ticks_style):
        if self._ticks_label_style is None:
            self._ticks_label_style = (None,) * 2
        try:
            x, y = ticks_style
        except ValueError:
            x, y = ticks_style = (ticks_style, ticks_style)
        self._ticks_label_style = ticks_style

        if x is not None:
            self.axes.set_xtick_style(
                **{self.clean_tick_label_styles(k):v for k,v in x.items()}
            )
        if y is not None:
            self.axes.set_ytick_style(
                **{self.clean_tick_label_styles(k):v for k,v in y.items()}
            )

    @property
    def aspect_ratio(self):
        return self._aspect_ratio
    @aspect_ratio.setter
    def aspect_ratio(self, ar):
        if isinstance(ar, (float, int)):
            a, b = self.absolute_plot_range
            cur_ar = abs(b[1] - b[0]) / abs(a[1] - a[0])
            targ_ar = ar / cur_ar
            self.axes.set_aspect_ratio(targ_ar)
        elif isinstance(ar, str):
            self.axes.set_aspect_ratio(ar)
        else:
            self.axes.set_aspect_ratio(ar[0], **ar[1])
        self._aspect_ratio = ar

    def _compute_inset_imagesize(self):
        if self.managed or self.graphics.inset:
            bbox = self.axes.get_bbox()
            ((alx, aby), (arx, aty)) = bbox
            ((plx, prx), (pby, pty)) = self.padding
            return (arx - alx + prx + plx, aty - aby + pty + pby)
        else:
            return tuple(s * DPI_SCALING for s in self.figure.get_size_inches())
    # set size
    @property
    def image_size(self):
        # im_size = self._image_size
        # if isinstance(self._image_size, (int, float)):
        #     im_size =
        if isinstance(self._image_size, str) and self._image_size == 'auto':
            return self._compute_inset_imagesize()
        else:
            return self._image_size
    @image_size.setter
    def image_size(self, wh):
        if isinstance(wh, str) and wh == 'auto':
            self._image_size = wh
        else:
            if self._image_size is None:
                self._image_size = self._compute_inset_imagesize()
            try:
                w, h = wh
            except (TypeError, ValueError):
                ar = self.aspect_ratio
                if not isinstance(ar, (int, float)):
                    try:
                        ar = self._image_size[1] / self._image_size[0]
                    except TypeError:
                        ar = 1
                w, h = wh = (wh, ar * wh)
            self._image_size = (w, h)

            if (
                    (w is not None or h is not None)
                    and not self.managed
                    and not self.graphics.inset
            ):
                if w is None:
                    w = self._image_size[0]
                if h is None:
                    h = self._image_size[1]

                if w > DPI_SCALING: # refuse to have anything smaller than 1 inch?
                    wi = w / DPI_SCALING
                else:
                    wi = w
                    w = DPI_SCALING * w

                if h > DPI_SCALING:
                    hi = h / DPI_SCALING
                else:
                    hi = h
                    h = DPI_SCALING * h
                self.figure.set_size_inches(wi, hi)
    @property
    def axes_bbox(self):
        return self.axes.get_bbox()
        # return bbox
    @axes_bbox.setter
    def axes_bbox(self, bbox):
        if bbox is not None:
            self.axes.set_bbox(bbox)

    # set background color
    @property
    def background(self):
        if self._background is None:
            if self.graphics.inset:
                self._background = self.axes.get_facecolor()
                self.fe_background = self.axes.get_facecolor()
            else:
                self._background = self.figure.get_facecolor()
        return self._background
    @background.setter
    def background(self, bg):
        self._background = bg
        if not self.managed and not self.graphics.inset:
            self.figure.set_facecolor(bg)
        self.axes.set_facecolor(bg)

    # set show_frame
    @property
    def frame(self):
        return self._frame
    @frame.setter
    def frame(self, fr):
        self._frame = fr
        if fr is True or fr is False:
            self.axes.set_frame_visible(fr)
        else:
            lr, bt = fr
            if len(lr) == 2:
                l, r = lr
            else:
                l = lr; r = lr
            if len(bt) == 2:
                b, t = bt
            else:
                b = bt; t = bt
            self.axes.set_frame_visible(
                ((l, r), (b, t))
            )

    @property
    def scale(self):
        return self._scale
    @scale.setter
    def scale(self, scales):
        if self._scale is None:
            self._scale = (self.axes.get_xscale(), self.axes.get_yscale())
        try:
            x, y = scales
        except ValueError:
            x, y = scales = (self._scale[0], scales)

        self._scale = tuple(scales)

        if isinstance(x, Styled):
            self.axes.set_xscale(*x.val, **x.opts)
        elif Styled.could_be(x):
            x = Styled.construct(x)
            self.axes.set_xscale(*x.val, **x.opts)
        elif x is not None:
            self.axes.set_xscale(x)
        if isinstance(y, Styled):
            self.axes.set_yscale(*y.val, **y.opts)
        elif y is not None:
            self.axes.set_yscale(y)
        elif Styled.could_be(y):
            y = Styled.construct(y)
            self.axes.set_yscale(*y.val, **y.opts)

    @property
    def padding(self):
        if self.managed or self.graphics.inset:
            return self.axes.get_padding()
        else:
            return self._padding
    @padding.setter
    def padding(self, padding):
        try:
            w, h = padding
        except (ValueError, TypeError):
            w = h = padding
        try:
            wx, wy = w
        except (ValueError, TypeError):
            wx = wy = w
        try:
            hx, hy = h
        except (ValueError, TypeError):
            hx = hy = h

        W, H = self.image_size
        if wx < 1:
            wx = round(wx * W)
        if wy < 1:
            wy = round(wy * W)
        if hx < 1:
            hx = round(hx * H)
        if hy < 1:
            hy = round(hy * H)
        self._padding = ((wx, wy), (hx, hy))
        wx = wx / W; wy = wy / W
        hx = hx / H; hy = hy / H
        if not self.managed and not self.graphics.inset:
            self.figure.set_extents([
                [wx, 1-wy],
                [hx, 1-hy]
            ])
    @property
    def padding_left(self):
        return self._padding[0][0]
    @padding_left.setter
    def padding_left(self, p):
        wx, wy = self._padding[0]
        hx, hy = self._padding[1]
        self.padding = ((p, wy), (hx, hy))
    @property
    def padding_right(self):
        return self._padding[0][1]
    @padding_right.setter
    def padding_right(self, p):
        wx, wy = self._padding[0]
        hx, hy = self._padding[1]
        self.padding = ((wx, p), (hx, hy))
    @property
    def padding_top(self):
        return self._padding[1][1]
    @padding_top.setter
    def padding_top(self, p):
        wx, wy = self._padding[0]
        hx, hy = self._padding[1]
        self.padding = ((wx, wy), (hx, p))
    @property
    def padding_bottom(self):
        return self._padding[1][0]
    @padding_bottom.setter
    def padding_bottom(self, p):
        wx, wy = self._padding[0]
        hx, hy = self._padding[1]
        self.padding = ((wx, wy), (p, hy))

    @property
    def spacings(self):
        if self.managed or self.graphics.inset:
            return [0, 0]
        else:
            return self._spacings
    @spacings.setter
    def spacings(self, spacings):
        if not (self.managed or self.graphics.inset):
            try:
                w, h = spacings
            except ValueError:
                w = h = spacings

            """
            The width of the padding between subplots, as a fraction of the average Axes width.
            """
            if hasattr(self.axes, 'get_bboxes'):
                bboxes = self.axes.get_bboxes()
            else:
                bboxes = self.figure.get_bboxes()
            # bboxes = [a.get_bbox() for a in self.axes]
            # W = bbox[1][0] - bbox[0][0]
            # H = bbox[1][1] - bbox[0][1]
            W = sum(b[1][0] - b[0][0] for b in bboxes) / len(bboxes)
            H = sum(b[1][1] - b[0][1] for b in bboxes) / len(bboxes)

            # W, H = self.image_size
            if w < 1:
                wp = round(w * W)
            else:
                wp = w
            if h < 1:
                hp = round(h * H)
            else:
                hp = h
            self._spacings = (wp, hp)

            w = wp / W
            h = hp / H

            self.figure.set_figure_spacings([w, h])


    @property
    def colorbar(self):
        return self._colorbar
    @colorbar.setter
    def colorbar(self, c):
        self._colorbar = c
        # if self._cbar_obj is not None:
        #     self.graphics.remove(self._cbar_obj)
        if self._cbar_obj is None:
            if self._colorbar is True:
                self._cbar_obj = self.graphics.add_colorbar()
            elif isinstance(self._colorbar, dict):
                self._cbar_obj = self.graphics.add_colorbar(**self.colorbar)
        elif self._colorbar is None:
            pass
            #self.graphics.remove(self._cbar_obj)

class GraphicsPropertyManager3D(GraphicsPropertyManager):
    def __init__(self, graphics, figure, axes, managed=False):
        super().__init__(graphics, figure, axes, managed=managed)
        self._view_settings = None

    @property
    def axes_labels(self):
        return self._axes_labels
    @axes_labels.setter
    def axes_labels(self, labels):
        if self._axes_labels is None:
            self._axes_labels = (self.axes.get_xlabel(), self.axes.get_ylabel(), self.axes.get_zlabel())
        try:
            xlab, ylab, zlab = labels
        except ValueError:
            xlab, ylab, zlab = labels = (labels, self._axes_labels[1], self._axes_labels[2])

        self._axes_labels = tuple(labels)
        if xlab is None:
            self.axes.set_xlabel("")
        elif isinstance(xlab, Styled):
            self.axes.set_xlabel(*xlab.val, **xlab.opts)
        elif Styled.could_be(xlab):
            xlab = Styled.construct(xlab)
            self.axes.set_xlabel(*xlab.val, **xlab.opts)
        else:
            self.axes.set_xlabel(xlab)

        if ylab is None:
            self.axes.set_ylabel("")
        elif isinstance(ylab, Styled):
            self.axes.set_ylabel(*ylab.val, **ylab.opts)
        elif Styled.could_be(ylab):
            ylab = Styled.construct(ylab)
            self.axes.set_ylabel(*ylab.val, **ylab.opts)
        else:
            self.axes.set_ylabel(ylab)

        if zlab is None:
            self.axes.set_zlabel("")
        elif isinstance(zlab, Styled):
            self.axes.set_zlabel(*zlab.val, **zlab.opts)
        elif Styled.could_be(zlab):
            zlab = Styled.construct(zlab)
            self.axes.set_zlabel(*zlab.val, **zlab.opts)
        else:
            self.axes.set_zlabel(zlab)

    @property
    def plot_range(self):
        if self._plot_range is None:
            pr = (self.axes.get_xlim(), self.axes.get_ylim())
        else:
            pr = self._plot_range
        return pr
    @plot_range.setter
    def plot_range(self, ranges):
        if self._plot_range is None:
            self._plot_range = (self.axes.get_xlim(), self.axes.get_ylim(), self.axes.get_zlim())
        elif len(self._plot_range) == 2:
            self._plot_range = self._plot_range + (self.axes.get_zlim(),)

        try:
            x, y, z = ranges
        except ValueError:
            try:
                x, y = ranges
            except ValueError:
                raise ValueError("bad plot range spec {}".format(ranges))
            else:
                if isinstance(x, (int, float)):
                    x, y, z = ranges = (self._plot_range[0], self._plot_range[1], ranges)
                else:

                    z = self._plot_range[2]
        # else:
        #     if isinstance(x, int) or isinstance(x, float):
        #         x, y, z = ranges = (self._plot_range[0], self._plot_range[1], ranges)

        self._plot_range = tuple(ranges)

        if isinstance(x, Styled):  # name feels wrong here...
            self.axes.set_xlim(*x.val, **x.opts)
        elif x is not None:
            self.axes.set_xlim(x)
        if isinstance(y, Styled):
            self.axes.set_ylim(*y.val, **y.opts)
        elif y is not None:
            self.axes.set_ylim(y)
        if isinstance(z, Styled):
            self.axes.set_zlim(*z.val, **z.opts)
        elif z is not None:
            self.axes.set_zlim(z)

    @property
    def absolute_plot_range(self):
        a, b = self.plot_range
        if a is None:
            a = self.axes.get_xlim()
        if b is None:
            b = self.axes.get_ylim()
        return a, b
    def _set_zticks(self, z, **opts):
        return self._set_ticks(z,
                               set_ticks=self.axes.set_zticks,
                               set_locator=self.axes.zaxis.set_major_locator,
                               set_minor_locator=self.axes.zaxis.set_minor_locator,
                               set_formatter=self.axes.zaxis.set_major_formatter,
                               set_minor_formatter=self.axes.zaxis.set_minor_formatter,
                               **opts
                               )

    @property
    def ticks(self):
        return self._ticks
    @ticks.setter
    def ticks(self, ticks):
        if self._ticks is None:
            self._ticks = (self.axes.get_xticks(), self.axes.get_yticks(), self.axes.get_zticks())
        if ticks is not None:
            try:
                x, y, z = ticks
            except ValueError:
                x, y, z = ticks = (self._ticks[0], self._ticks[1], ticks)

            self._ticks = ticks

            self._set_xticks(x)
            self._set_yticks(y)
            self._set_zticks(z)

    @property
    def ticks_style(self):
        return self._ticks_style
    @ticks_style.setter
    def ticks_style(self, ticks_style):
        if self._ticks_style is None:
            self._ticks_style = (None,)*3
        try:
            x, y, z = ticks_style
        except ValueError:
            x, y, z = ticks_style = (self._ticks_style[0], self._ticks_style[1], ticks_style)
        self._ticks_style = ticks_style
        if x is not None:
            self.axes.set_xtick_style(
                **x
            )
        if y is not None:
            self.axes.set_ytick_style(
                **y
            )
        if z is not None:
            self.axes.set_ztick_style(
                **z
            )

    @property
    def view_settings(self):
        return self.axes.get_view_settings()
    @view_settings.setter
    def view_settings(self, value):
        self.axes.set_view_settings(**value)