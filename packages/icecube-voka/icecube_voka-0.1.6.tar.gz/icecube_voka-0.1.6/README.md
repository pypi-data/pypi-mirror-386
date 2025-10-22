<!--- Top of README Badges (automated) --->
[![PyPI](https://img.shields.io/pypi/v/icecube-voka)](https://pypi.org/project/icecube-voka/) [![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/icecube/voka?include_prereleases)](https://github.com/icecube/voka/) [![Versions](https://img.shields.io/pypi/pyversions/icecube-voka.svg)](https://pypi.org/project/icecube-voka) [![PyPI - License](https://img.shields.io/pypi/l/icecube-voka)](https://github.com/icecube/voka/blob/main/LICENSE) [![GitHub issues](https://img.shields.io/github/issues/icecube/voka)](https://github.com/icecube/voka/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) [![GitHub pull requests](https://img.shields.io/github/issues-pr/icecube/voka)](https://github.com/icecube/voka/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen)
<!--- End of README Badges (automated) --->
# voka
Histograms comparisons using statistical tests as input to an outlier detection algorithm.

## Problem Statement
Let's say you have a large number of histograms produced by a complex system (e.g. scientific simulation chain 
for a large-scale physics experiment) and you want to compare one large set of histograms to another to determine 
differences.  When the number of histograms becomes large (>100) it can be difficult for human observers to 
efficiently scan them for subtle differences buried in statistical flucuations.  The project is a tool that
can help detect those differences.

**This method can be viewed as emperically determining a p-value threshold from benchmark sets, valid for both 
discrete  and continuous distributions, and both Poissonian and non-Poissonian statistics.**

See the [wiki](https://github.com/icecube/voka/wiki) for more details.

# Dependencies

* numpy
* matplotlib
* scipy (optional)

```
   numpy (basic_example,classic_fit_example,standard_distribution_comparisons,stochastic_example,test.test_lof,test.test_metrics,test.test_voka,vanilla_gaussian,voka.lof)
    pylab (classic_fit_example,standard_distribution_comparisons,stochastic_example,vanilla_gaussian)
    scipy 
      \-optimize (classic_fit_example,standard_distribution_comparisons,stochastic_example,vanilla_gaussian)
      \-special (voka.metrics.llh)
      \-stats (standard_distribution_comparisons,stochastic_example,vanilla_gaussian)
    voka 
      \-compare (test.test_metrics)
      \-lof (test.test_lof)
      \-metrics 
      | \-ad (test.test_metrics)
      | \-bdm (test.test_metrics)
      | \-chisq (standard_distribution_comparisons,stochastic_example,test.test_metrics,vanilla_gaussian)
      | \-cvm (test.test_metrics)
      | \-ks (test.test_metrics)
      | \-llh (test.test_metrics)
      \-model (basic_example,test.test_voka)

```


# Test Coverage
Measured with [coverage](https://coverage.readthedocs.io/en/6.2/).

As of January 14th, 2022:
```
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
voka/__init__.py         0      0   100%
voka/compare.py         12      2    83%   37-38
voka/lof.py             26      0   100%
voka/metrics.py        115     17    85%   39-42, 60, 80, 89, 113, 141, 154, 162-163, 165-166, 168-169, 184
voka/model.py           36      6    83%   78-87
voka/two_sample.py      38     38     0%   2-90
--------------------------------------------------
TOTAL                  227     63    72%
```

## Running Tests
```sh
$ python3 -m unittest
$ coverage run --source=voka -m unittest
$ coverage report -m
```
