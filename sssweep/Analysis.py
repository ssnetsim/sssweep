"""
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * - Redistributions of source code must retain the above copyright notice, this
 * list of conditions and the following disclaimer.
 *
 * - Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * - Neither the name of prim nor the names of its contributors may be used to
 * endorse or promote products derived from this software without specific prior
 * written permission.
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
"""
import ssplot

class Analysis(object):
  def __init__(self, name, filters, latency_mode,
               parse = True):

    self.name = name
    self.filters = filters

    assert latency_mode in ['packet-header', 'packet', 'message', 'transaction']
    self.latency_mode = latency_mode.split('-')[0]
    self.header_latency = latency_mode == 'packet-header'
    self.parse = parse
    self.plots={}

  def add_plot(self, plot_type, title_format = 'long-colon', **kwargs):
    """
    This adds a plot and its configuration to the analysis object

    Args:
    plot_type    : name of plot type
    title_format : title format and style
    kewargs all plot settings
    """
    d = ssplot.CommandLine.all_names()

    found = False
    valid = []
    for pt in d:
      valid.append(d[pt][0])
      if plot_type in d[pt]:
        plot_type = d[pt][0]
        plot_names = d[pt]
        found = True
        break

    # assert plot types
    assert found, 'plot type [{0}] not found, Valid: {1}'.format(
      plot_type, valid)

    assert plot_type not in self.plots.keys(), \
    'Error: plot type already exists!'
    self.plots[plot_type] = {}

    # title settings for sssweep
    if title_format is not None:
      if '-'  in title_format:
        title_f = title_format.split('-')[0]
        title_s = title_format.split('-')[1]
        assert title_s in ['colon', 'equal']
      else:
        title_f = title_format
        title_s = None
      assert title_f in ['long', 'short', 'off']

      self.plots[plot_type]['title_format'] = title_f
      self.plots[plot_type]['title_style'] = title_s

    # plot settings and names
    for key in kwargs:
      assert key is not 'title', 'Title is set by Sweeper'
      assert key is not 'units', 'Units are set by Sweeper'
    self.plots[plot_type]['settings'] = kwargs
    self.plots[plot_type]['names'] = plot_names
