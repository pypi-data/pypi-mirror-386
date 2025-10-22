"""Rendering histograms."""

import pylab  # type: ignore[import]

def draw(sample, title=None, color = "green", ylim = None, log = False, yerr = None):
    r"""Make a matplotlib figure of a sample.
    Arguments:
        title : Plot title.
        color : matplotlib color string
            Color of the histogram area.
        ylim : None or (float, float)
            Axis limits (ymin, ymax). If None, use 0.1 margin around data.
        log : bool
            Draw the y-axis in a logarithmic scale.
        yerr : None, float, or array/list of floats
            Error bars around the histogram.

    r"""

    if not ylim:
        if log:
            positive_y_values = [v for v in sample if v > 0]
            ymin = 0.9 * min(positive_y_values) if positive_y_values else 0.1
        else:
            ymin = 0.9 * min(sample)
        ymax = 1.1 * max(sample)
    else:
        ymin, ymax = ylim

    pylab.ylim(ymin, ymax)
    pylab.title(title)

    left_edges = list(range(len(sample)))

    pylab.bar(left_edges,
              sample,
              linewidth = 0,
              align = "edge",
              color = color,
              log = log,
              yerr = yerr)

def draw_comparisons(test_sample,
                     benchmark_samples,
                     title=None,
                     colors = {'test': 'blue',  'benchmarks': 'green'},
                     log = False):
    r"""Make a matplotlib figure of comparing test_histogram to benchmark_histogram.
        Arguments:
            draw_ratio : bool
                Draw a ratio test_histogram/benchmark_histogram in a third subplot,
                with error bars. Always linear y-scale. The histograms have to use
                the same binning!
            color : matplotlib color string
                Color of the histogram areas.
            log : bool
                Draw the y-axis in a logarithmic scale.

    r"""

    # Need to figure out how many subplots to make.
    # Also need to scale the title

    subplot_start = {2 : 211,
                     3 : 311,
                     4 : 221,
                     5 : 321,
                     6 : 321,
                     7 : 331,
                     8 : 331,
                     9 : 331,
    } # matplotlib chokes on 431 and 431

    n_plots = min(1 + len(benchmark_samples), 9)

    fig_idx = subplot_start[n_plots]
    ax = pylab.subplot(fig_idx)
    ax.set_title(title)
    draw(test_sample, color = colors['test'], log = log)

    samples = benchmark_samples[:8] \
        if len(benchmark_samples) > 8 \
           else benchmark_samples

    for sample in samples:
        fig_idx += 1
        pylab.subplot(fig_idx)
        draw(sample, color = colors['benchmarks'], log = log)

def draw_ratios(test_sample,
                benchmark_samples,
                title=None,
                colors = {'test': 'blue',  'benchmarks': 'green'},
                log = False):

    # Need to figure out how many subplots to make.
    # Also need to scale the title

    subplot_start = {2 : 211,
                     3 : 311,
                     4 : 221,
                     5 : 321,
                     6 : 321,
                     7 : 331,
                     8 : 331,
                     9 : 331,
    } # matplotlib chokes on 431 and 431

    n_plots = min(len(benchmark_samples), 9)

    samples = benchmark_samples[:8] \
        if len(benchmark_samples) > 8 \
           else benchmark_samples

    fig_idx = subplot_start[n_plots]
    for sample in samples:
        pylab.subplot(fig_idx)
        fig_idx += 1

        ratio = [t/s if s else 0. for t,s in zip(test_sample, sample)]

        draw(ratio, color = colors['benchmarks'], log = log)

def draw_ratio(test_sample,
               benchmark_sample,
               colors = {'test': 'blue',  'benchmarks': 'green'},
               log = False):
    r"""Make a matplotlib figure of comparing test_histogram to benchmark_histogram.
        Arguments:
            draw_ratio : bool
                Draw a ratio test_histogram/benchmark_histogram in a third subplot,
                with error bars. Always linear y-scale. The histograms have to use
                the same binning!
            color : matplotlib color string
                Color of the histogram areas.
            log : bool
                Draw the y-axis in a logarithmic scale.

    r"""

    # Need to figure out how many subplots to make.
    # Also need to scale the title

    ax = pylab.subplot(221)
    draw(test_sample, color = colors['test'], log = log)

    pylab.subplot(222)
    draw(benchmark_sample, color = colors['benchmarks'], log = log)

    ratio_sample = [t/b if b else 0.
                    for t,b in zip(test_sample, benchmark_sample)]
    pylab.subplot(223)
    draw(ratio_sample)
