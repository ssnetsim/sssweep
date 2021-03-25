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
import os
import stat
import copy
import numpy
import ssplot
import taskrun

#from .Analysis import Analysis
from .web_viewer_gen import *

class Sweeper(object):
  def __init__(
      self, supersim_path, settings_path, ssparse_path, transient_path,
      create_task_func, out_dir, compress=True, check_paths=True,
      latency_scalar=None, latency_units=None, load_units=None, sim=True,
      viewer='prod', viewer_style='ss', readme=None, wanted_plots=[]):
    """
    Constructs a Sweeper object

    Args:
      supersim_path    : path to supersim bin
      settings_path    : path to settings file
      ssparse_path     : path to ssparse bin
      transient_path   : path to transient script
      create_task_func : task creation function
      out_dir          : location of output files directory
      compress         : bool to enable/disable compression of data files
      check_paths      : check paths existence

      latency_scalar   : latency scalar during parsing
      latency_units    : unit of latency for plots
      sim              : bool to enable/disable sim
      viewer           : web viewer (dev/prod/off)
      viewer_style     : style name of viewer
      readme           : text for readme file
      wanted_plots     : name of compare plot to get cmd
    """
    # mandatory
    self._supersim_path = os.path.abspath(os.path.expanduser(supersim_path))
    self._settings_path = os.path.abspath(os.path.expanduser(settings_path))
    self._ssparse_path = os.path.abspath(os.path.expanduser(ssparse_path))
    self._transient_path = os.path.abspath(os.path.expanduser(transient_path))
    self._create_task_func = create_task_func
    self._out_dir = os.path.abspath(os.path.expanduser(out_dir))
    self._compress = compress

    # settings
    self._latency_scalar = latency_scalar
    self._latency_units = latency_units
    self._load_units = load_units
    self._sim = sim
    self._viewer = viewer.lower()
    self._readme = readme

    # load sweep values
    self._start = None
    self._stop = None
    self._step = None

    self._variables = []
    self._parsings = {}
    self._plots = {}
    self._all_cmds = []
    self._all_cmds_file = 'all_cmds.txt'
    self._wanted_plots = wanted_plots
    self._plot_cmds = []
    self._plot_cmds_file = 'plot_cmds.sh'
    self._created = False
    self._load_variable = None
    self._load_name = None

    # variables for javascript
    self._id_cmp = "Cmp"
    self._id_lat_dist = "LatDist"
    self._comp_var_count = 0

    # store tasks
    self._sim_tasks = {}
    self._ssparse_tasks = {}
    self._tparse_tasks = {}

    if check_paths:
      # ensure the settings file exists
      if not os.path.isfile(self._settings_path):
        self._error('{0} does not exist'.format(self._settings_path))

      # ensure the supersim bin exists
      if not os.path.isfile(self._supersim_path):
        self._error('{0} does not exist'.format(self._supersim_path))

      # ensure the ssparse bin exists
      if not os.path.isfile(self._ssparse_path):
        self._error('{0} does not exist'.format(self._ssparse_path))

      # ensure the transient script exists
      if not os.path.isfile(self._transient_path):
        self._error('{0} does not exist'.format(self._transient_path))

    # ensure outdir exists, if not make it
    if not os.path.isdir(self._out_dir):
      try:
        os.mkdir(self._out_dir)
      except:
        self._error('couldn\'t create {0}'.format(self._out_dir))

    # create subfolders and readme file
    self._data_folder = 'data'
    self._logs_folder = 'logs'
    self._plots_folder = 'plots'
    self._viewer_folder = 'viewer'

    # viewer output files with static names
    self._html_name = 'index.html'
    self._javascript_name = 'dynamic_plot.js'
    self._css_name = 'style.css'
    self._favicon_name = 'favicon.ico'
    self._mainlogo_name = 'logo.png'

    # plot viewer style
    self._favicon_res = '{}-favicon.ico'.format(viewer_style)
    self._mainlogo_res = '{}-logo.png'.format(viewer_style)
    self._colors_res = '{}-color.clr'.format(viewer_style)

    # readme
    if self._readme != None:
      readme_f = os.path.join(self._out_dir, 'README.txt')
      with open(readme_f, 'w') as fd_readme:
        print(readme, file=fd_readme)

    # data
    data_f = os.path.join(self._out_dir, self._data_folder)
    if not os.path.isdir(data_f):
      try:
        os.mkdir(data_f)
      except:
        self._error('couldn\'t create {0}'.format(data_f))

    # logs
    logs_f = os.path.join(self._out_dir, self._logs_folder)
    if not os.path.isdir(logs_f):
      try:
        os.mkdir(logs_f)
      except:
        self._error('couldn\'t create {0}'.format(logs_f))

    # plots
    plots_f = os.path.join(self._out_dir, self._plots_folder)
    if not os.path.isdir(plots_f):
      try:
        os.mkdir(plots_f)
      except:
        self._error('couldn\'t create {0}'.format(plots_f))

    # viewer
    viewer_f = os.path.join(self._out_dir, self._viewer_folder)
    if not os.path.isdir(viewer_f):
      try:
        os.mkdir(viewer_f)
      except:
        self._error('couldn\'t create {0}'.format(viewer_f))

  def add_loads(self, name, short_name, start, stop, step, set_command):
    """
    This creates and adds the load sweep variable to _load_variable

    Args:
      name              : name of sweep variable
      shortname         : acronym of sweep variable for filename
      start, stop, step : load sweep start stop and step
      set_command       : pointer to command function
    """
    # build the variable
    assert start <= stop, 'start must be <= stop'
    assert step > 0, 'step must be > 0.0'
    loads = list(numpy.arange(start, stop, step))
    assert len(loads) > 0
    lconfig = {'name': name, 'short_name': short_name, 'values': list(loads),
               'command': set_command, 'compare' : False}
    # add the variables
    self._load_variable = lconfig
    self._load_name = name
    self._start = start
    self._stop = stop
    self._step = step

  def add_plot(self, plot_type, filter_name, filters = [],
               title_format='short-equal', latency_mode='packet',
               transient_args=None, **plot_settings):
    """
    This adds a plot and corresponding parsing.
    """
    # title format
    if '-'  in title_format:
      title_f = title_format.split('-')[0]
      title_s = title_format.split('-')[1]
      assert title_s in ['colon', 'equal']
    else:
      title_f = title_format
      title_s = None
    assert title_f in ['long', 'short', 'off']

    # latency mode
    assert latency_mode in ['packet-header', 'packet', 'message', 'transaction']
    lat_mode = latency_mode.split('-')[0]
    header_latency = latency_mode == 'packet-header'

    # set plot_type to valid format
    d = ssplot.CommandLine.all_names()
    found = False
    valid = []
    for pt in d:
      valid.append(d[pt][0])
      if plot_type in d[pt]:
        plot_type = d[pt][0]
        short_ptype = d[pt][1]
        plot_names = d[pt]
        found = True
        break
    assert found, 'plot type [{0}] not found, valid names: {1}'.format(
      plot_type, valid)

    # define parsing type
    if plot_type in ['load-rate']:
      parse_type = None
      assert transient_args is None
      assert len(filters) == 0, 'No filters supported in load-rate plots'
    elif plot_type in ['time-percent-minimal', 'time-average-hops',
                       'time-latency']:
      parse_type = 'transient'
    else:
      parse_type = 'ssparse'
      assert transient_args is None

    # assert checks
    if len(self._parsings) > 0: # not empty
      # check unique pair filter_name-filters per parsing type
      if filter_name not in self._parsings.keys(): # unique filter_name
        for key in self._parsings:
          if parse_type == self._parsings[key]['parse_type']: # same parsing
            if (set(filters)) != (self._parsings[key]['filters']): # unique filters
              # ADD parsing
              self._parsings[filter_name] = {}
              self._parsings[filter_name]['parse_type'] = parse_type
              self._parsings[filter_name]['filters'] = set(filters)
              self._parsings[filter_name]['transient'] = transient_args
              self._parsings[filter_name]['header_latency'] = header_latency
              self._parsings[filter_name]['latency_mode'] = lat_mode
              break
            else: # NOT unique filters for unique filter name
              print('NOT UNIQUE FILTERS')
              assert False, 'Set of filters for {0} already exist with a '\
                'different filter name!'.format(parse_type)
          else: # not same parsing - allowed filters
            self._parsings[filter_name] = {}
            self._parsings[filter_name]['parse_type'] = parse_type
            self._parsings[filter_name]['filters'] = set(filters)
            self._parsings[filter_name]['transient'] = transient_args
            self._parsings[filter_name]['header_latency'] = header_latency
            self._parsings[filter_name]['latency_mode'] = lat_mode
            break
      else: # filter name already exists
        # same filters
        assert set(filters) == self._parsings[filter_name]['filters'], \
                '[{}] must have the same filters'.format(filter_name)

        assert transient_args == self._parsings[filter_name]['transient'] or \
                header_latency == self._parsings[filter_name]['header_latency'] or \
                lat_mode == self._parsings[filter_name]['latency_mode'], \
                'Check [transient_args] and/or [latency_mode] ' \
                'are the same in [{0}]'.format(filter_name)

    else: # empty just add
      # ADD
      self._parsings[filter_name] = {}
      self._parsings[filter_name]['parse_type'] = parse_type
      self._parsings[filter_name]['filters'] = set(filters)
      self._parsings[filter_name]['transient'] = transient_args
      self._parsings[filter_name]['header_latency'] = header_latency
      self._parsings[filter_name]['latency_mode'] = lat_mode

    # plot does not exist for filter
    assert (plot_type, filter_name) not in self._plots.keys(), \
      'plot_type [{0}] already exists for parsing [{1}] with filter '\
      '[{2}]'.format(plot_type, parse_type, filter_name)

    # add plot
    self._plots[(plot_type, filter_name)]={}
    self._plots[(plot_type, filter_name)]['parsing'] = parse_type
    self._plots[(plot_type, filter_name)]['plot_type'] = plot_type
    self._plots[(plot_type, filter_name)]['short_plot_type'] = short_ptype
    self._plots[(plot_type, filter_name)]['settings'] = plot_settings
    self._plots[(plot_type, filter_name)]['title_format'] = title_f
    self._plots[(plot_type, filter_name)]['title_style'] = title_s

  def add_variable(self, name, short_name, values, set_command, compare=True):
    """
    This adds a sweep variable to the config variable

    Args:
      name          : name of sweep variable
      short_name    : acronym of sweep variable for filename
      values        : values of variable to sweep through
      set_command   : pointer to command function
      compare       : should this variable be compared in cplot
    """
    # verify unique values
    assert len(values) == len(set(values)), 'Duplicate value detected'

    # check at least 1 value was given for variable
    assert len(values) > 0

    # short names do not support spaces
    assert ' ' not in short_name, 'Spaces not supported in short_name'

    # build the variable
    configall = {
      'name': name,
      'short_name': short_name,
      'values': list(values),
      'command': set_command,
      'compare': compare
    }
    assert len(configall) > 0

    # add the variable
    self._variables.append(configall)

  def _dim_iter(self, do_vars=None, dont=None):
    """
    This function creates the config files with the permutations of the sweep
    variables

    Args:
      do_vars           : variables to iterate through
      dont         : variables to remove from iteration
    """
    tmp_vars = []
    # All variables
    if do_vars is None:
      tmp_vars = copy.deepcopy(self._variables) #Adds all
    else:
      for var in copy.deepcopy(self._variables):
        if var['name'] in do_vars: # add only dos
          tmp_vars.append(var)

    # remove variables
    vars_all = []
    for var in tmp_vars:
      if dont is None or var['name'] not in dont:
        vars_all.append(var) # add only variables not in dont

    # reverse the order
    vars_all = list(reversed(vars_all))

    # find value lengths
    widths = []
    for var in vars_all:
      widths.append(len(var['values']))

    # find top non-single value variable
    top_non_one = None
    for dim in reversed(range(len(widths))):
      if widths[dim] != 1:
        top_non_one = dim
        break

    # generate all indices
    cur = [0] * len(widths)
    more = True
    while more:
      # yield the configuration
      config = []
      for dim in reversed(range(len(cur))):
        variable = vars_all[dim]
        config.append({
          'name': variable['name'],
          'short_name': variable['short_name'],
          'value': variable['values'][cur[dim]],
          'command': variable['command'],
          'compare': variable['compare']
        })
      yield config

      # detect only one config
      if top_non_one is None:
        more = False
        break

      # advance the generator
      for dim in range(len(widths)):
        if cur[dim] == widths[dim] - 1:
          if dim == top_non_one:
            more = False
            break
          else:
            cur[dim] = 0

        else:
          cur[dim] += 1
          break

  def _error(self, msg, code=-1):
    if msg:
      print('ERROR: {0}'.format(msg))
    exit(code)

  def _make_id(self, config, f_name=None, extra=None):
    """
    This creates id for task

    Args:
      config   : input config to iterate
      extra    : extra values to append at the end (list or string)
    """
    values = [y_var['value'] for y_var in config]
    if f_name != None:
      values.insert(0, f_name)
    if extra:
      if isinstance(extra, str):
        values.append(extra)
      elif isinstance(extra, list):
        values.extend(extra)
      else:
        assert False
    return '_'.join([str(x_values) for x_values in values])

  def _make_title(self, config, plot_info, lat=None):
    # plot name
    if plot_info['title_format'] == 'long':
      plot_name = plot_info['plot_type'].replace("-", " ")
    elif plot_info['title_format'] == 'short':
      plot_name = plot_info['short_plot_type']
    else:
      assert(false)
    assert len(plot_name) > 0

    # configs
    name_values = []
    if len(config) > 0:
      for y_values in config:
        if plot_info['title_format'] == 'long':
          name_values.append((y_values['name'], str(y_values['value'])))
        elif plot_info['title_format'] == 'short':
          name_values.append((y_values['short_name'], str(y_values['value'])))
        else:
          assert False, 'Invalid title format'

    # format title
    if plot_info['title_style'] == 'colon':
      separ = ': '
      delim = ', '
    else:
      separ = '='
      delim = ' '

    # config vars
    v = ''
    for idx, x_values in enumerate(name_values):
      tmp = separ.join(x_values)
      if idx != len(name_values)-1:
        v += tmp + delim
      else:
        v += tmp

    title = '{0}'.format(plot_name)
    if len(v) > 0 :
      # if config vars
      title += ' ({0}'.format(v)

    if plot_info['plot_type'] == 'load-latency-compare':
      # add latency distribution
      title += ' [{0}]'.format(lat)

    if len(v) > 0 :
      title += ')'

    # add quotes around title
    title = '"{}"'.format(title)

    assert len(title) > 0
    return title

  def _create_config(self, *args):
    """
    This creates ordered config from multiple sub-configs

    Args:
      *   : configs to combine
    """
    # vars to return
    combined = []
    for var in copy.deepcopy(self._variables):
      for config in args:
        found = False
        for var2 in config:
          if var2['name'] == var['name']:
            found = True
            combined.append(copy.deepcopy(var2))
            break
        if found:
          break
    return combined

  def _cmd_clean(self, cmd):
    """
    This adds leading space to input commands

    Args:
      cmd   : cmd to clean (str or array)
    """
    assert cmd != None, 'You must return a command modifier'
    if isinstance(cmd, str):
      cmd = [cmd]
    clean = ' ' + ' '.join([str(x_values) for x_values in [y for y in cmd]])
    return clean

  def _get_sim_files(self, id_task):
    """
    This creates sim file names for a given id_task
    """
    dir_var = self._out_dir
    compress = '.gz' if self._compress else ''
    return {
      # generated by sim
      'info_csv': os.path.join(
        dir_var, self._data_folder, 'info_{0}.csv{1}'.format(
          id_task, compress)),
      'messages_mpf' : os.path.join(
        dir_var, self._data_folder, 'messages_{0}.mpf{1}'.format(
          id_task, compress)),
      'rates_csv' : os.path.join(
        dir_var, self._data_folder, 'rates_{0}.csv{1}'.format(
          id_task, compress)),
      'channels_csv' : os.path.join(
        dir_var, self._data_folder, 'channels_{0}.csv{1}'.format(
          id_task, compress)),
      'simout_log' : os.path.join(
        dir_var, self._logs_folder, 'simout_{0}.log'.format(id_task)),
    }
  def _get_ssparse_files(self, id_task):
    """
    This creates ssparse file names for a given id_task
    """
    dir_var = self._out_dir
    compress = '.gz' if self._compress else ''
    return {
      # generated by ssparse
      'samples_csv' : os.path.join(
        dir_var, self._data_folder, 'samples_{0}.csv{1}'.format(
          id_task, compress)),
      'latency_csv' : os.path.join(
        dir_var, self._data_folder, 'latency_{0}.csv{1}'.format(
          id_task, compress)),
      'hops_csv' : os.path.join(
        dir_var, self._data_folder, 'hops_{0}.csv{1}'.format(
          id_task, compress))
    }

  def _get_tparse_files(self, id_task):
    """
    This creates tparse file names for a given id_task
    """
    dir_var = self._out_dir
    compress = '.gz' if self._compress else ''
    return {
      # generated by transient parse
      'trans_csv' : os.path.join(
        dir_var, self._data_folder, 'trans_{0}.csv{1}'.format(
          id_task, compress))
    }

  def _get_plot_files(self, id_task):
    """
    This creates plots file names for a given id_task
    """
    dir_var = self._out_dir
    compress = '.gz' if self._compress else ''
    return {
      # plots
      'loadpermin_png' : os.path.join(
        dir_var, self._plots_folder, 'loadpermin_{0}.png'.format(id_task)),
      'loadlatcomp_png' : os.path.join(
        dir_var, self._plots_folder, 'loadlatcomp_{0}.png'.format(id_task)),
      'loadlat_png' : os.path.join(
        dir_var, self._plots_folder, 'loadlat_{0}.png'.format(id_task)),
      'loadrateper_png' : os.path.join(
        dir_var, self._plots_folder, 'loadrateper_{0}.png'.format(id_task)),
      'latpdf_png' : os.path.join(
        dir_var, self._plots_folder, 'latpdf_{0}.png'.format(id_task)),
      'latperc_png' : os.path.join(
        dir_var, self._plots_folder, 'latperc_{0}.png'.format(id_task)),
      'latcdf_png' : os.path.join(
        dir_var, self._plots_folder, 'latcdf_{0}.png'.format(id_task)),
      'loadavehops_png' : os.path.join(
        dir_var, self._plots_folder, 'loadavehops_{0}.png'.format(id_task)),
      'timelatscat_png': os.path.join(
        dir_var, self._plots_folder, 'timelatscat_{0}.png'.format(id_task)),
      'loadrate_png' : os.path.join(
        dir_var, self._plots_folder, 'loadrate_{0}.png'.format(id_task)),
      'timepermin_png' : os.path.join(
        dir_var, self._plots_folder, 'timepermin_{0}.png'.format(id_task)),
      'timeavehops_png' : os.path.join(
        dir_var, self._plots_folder, 'timeavehops_{0}.png'.format(id_task)),
      'timelat_png' : os.path.join(
        dir_var, self._plots_folder, 'timelat_{0}.png'.format(id_task))
    }

  def _get_viewer_files(self):
    """
    This creates file names for the web viewer
    """
    return {
      'html' : os.path.join(
        self._out_dir, self._viewer_folder, self._html_name),
      'javascript' : os.path.join(
        self._out_dir, self._viewer_folder, self._javascript_name),
      'css' : os.path.join(
        self._out_dir, self._viewer_folder, self._css_name),
      'favicon' : os.path.join(
        self._out_dir, self._viewer_folder, self._favicon_name),
      'mainlogo' : os.path.join(
        self._out_dir, self._viewer_folder, self._mainlogo_name)
    }

  def create_tasks(self, tm_var):
    """
    This creates all the tasks
    """
    # task created only once
    assert not self._created, "Task already created! Fail!"
    self._created = True
    # add load to _variables
    self._variables.append(self._load_variable)
    # check for unique names
    x_values = []
    y_values = []
    for n_var in self._variables:
      x_values.append(n_var['name'])
      y_values.append(n_var['short_name'])
    assert len(x_values) == len(set(x_values)), "Not unique names!"
    assert len(y_values) == len(set(y_values)), "Not unique short names!"

    # sim
    if self._sim:
      print("Creating simulation tasks")
      self._create_sim_tasks(tm_var)
    # parsings
    if len(self._parsings) > 0:
      print("Creating parsing tasks")
    for f_name in self._parsings:
      # ssparse
      if self._parsings[f_name]['parse_type'] == 'ssparse':
        self._create_ssparse_tasks(tm_var, f_name)
      # transient
      elif self._parsings[f_name]['parse_type'] == 'transient':
        self._create_tparse_tasks(tm_var, f_name)
      # none
      elif self._parsings[f_name]['parse_type'] == None:
        pass
      else:
        assert False
    # plots
    if len(self._plots) > 0:
      print("Creating plotting tasks")
    for plot_type, filter_name in self._plots:
      # none
      if plot_type == 'load-rate':
        self._create_loadrate_tasks(tm_var, filter_name)
      # ssparse
      if plot_type == 'load-percent-minimal':
        self._create_loadpermin_tasks(tm_var, filter_name)
      if plot_type == 'load-latency':
        self._create_loadlat_tasks(tm_var, filter_name)
      if plot_type == 'load-average-hops':
        self._create_loadavehops_tasks(tm_var, filter_name)
      if plot_type == 'load-rate-percent':
        self._create_loadrateper_tasks(tm_var, filter_name)
      if plot_type == 'load-latency-compare':
        self._create_loadlatcomp_tasks(tm_var, filter_name)
      if plot_type == 'latency-pdf':
        self._create_latpdf_tasks(tm_var, filter_name)
      if plot_type == 'latency-percentile':
        self._create_latperc_tasks(tm_var, filter_name)
      if plot_type == 'latency-cdf':
        self._create_latcdf_tasks(tm_var, filter_name)
      if plot_type == 'time-latency-scatter':
        self._create_timelatscat_tasks(tm_var, filter_name)
      # tran
      if plot_type == 'time-percent-minimal':
        self._create_timepermin_tasks(tm_var, filter_name)
      if plot_type == 'time-average-hops':
        self._create_timeavehops_tasks(tm_var, filter_name)
      if plot_type == 'time-latency':
        self._create_timelat_tasks(tm_var, filter_name)

    # viewer
    if  self._viewer != 'off':
      print("Creating viewer")
      self._create_viewer_task()

    # all cmds
    if len(self._all_cmds) != 0:
      cmd_f = os.path.join(self._out_dir, self._all_cmds_file)
      with open(cmd_f, 'w') as fd_cmd:
        fd_cmd.write('\n'.join(str(line) for line in self._all_cmds))

    if len(self._plot_cmds) != 0:
      cmd_f2 = os.path.join(self._out_dir, self._plot_cmds_file)
      with open(cmd_f2, 'w') as fd_cmd2:
        fd_cmd2.write('#!/bin/bash\n')
        fd_cmd2.write('\n'.join(str(line) for line in self._plot_cmds))

      st = os.stat(cmd_f2)
      os.chmod(cmd_f2, st.st_mode | stat.S_IEXEC)

  # ===================================================================
  def _create_sim_tasks(self, tm_var):
    # create config
    for sim_config in self._dim_iter():
      # make id & name
      id_task = self._make_id(sim_config)
      files = self._get_sim_files(id_task)
      sim_name = 'sim_{0}'.format(id_task)
      # sim command
      sim_cmd = (
        '{0} {1} '
        '/simulator/info_log/file=string={2} '
        '/workload/message_log/file=string={3} '
        '/workload/applications/0/rate_log/file=string={4} '
        '/network/channel_log/file=string={5}'
      ).format(
        self._supersim_path,
        self._settings_path,
        files['info_csv'],
        files['messages_mpf'],
        files['rates_csv'],
        files['channels_csv'])
      #loop through each variable commands to add
      for var in sim_config:
        tmp_cmd = var['command'](var['value'], sim_config)
        cmd = self._cmd_clean(tmp_cmd)
        sim_cmd += cmd
      self._all_cmds.append(sim_cmd)
      # sim task
      sim_task = self._create_task_func(
        tm_var, sim_name, sim_cmd, files['simout_log'], 'sim', sim_config)
      sim_task.priority = 0
      sim_task.add_condition(taskrun.FileModificationCondition(
        [], [files['info_csv'], files['messages_mpf'], files['rates_csv'],
             files['channels_csv']]))
      self._sim_tasks[id_task] = sim_task

  # ssparse
  def _create_ssparse_tasks(self, tm_var, f_name):
    # loop through all variables
    for ssparse_config in self._dim_iter():
      # make id and name
      id_ssparse = self._make_id(ssparse_config, f_name=f_name)
      id_sim = self._make_id(ssparse_config)
      ssparse_files = self._get_ssparse_files(id_ssparse)
      sim_files = self._get_sim_files(id_sim)
      ssparse_name = 'parse_{0}'.format(id_ssparse)

      latency_mode = self._parsings[f_name]['latency_mode']
      header_latency = self._parsings[f_name]['header_latency']
      filters =  self._parsings[f_name]['filters']

      # parse cmd
      ssparse_cmd = '{0} -{1} {2} -l {3} -c {4} {5}'.format(
        self._ssparse_path,
        latency_mode[:1].lower(),
        ssparse_files['samples_csv'],
        ssparse_files['latency_csv'],
        ssparse_files['hops_csv'],
        sim_files['messages_mpf'])

      if header_latency:
        ssparse_cmd += ' --headerlatency'
      if self._latency_scalar != None:
        ssparse_cmd += ' -s {0}'.format(self._latency_scalar)
      # parse filters
      if filters != None:
        for filter in filters:
          ssparse_cmd += ' -f {0}'.format(filter)

      self._all_cmds.append(ssparse_cmd)
      # parse task
      ssparse_task = self._create_task_func(
        tm_var, ssparse_name, ssparse_cmd, None, 'parse', ssparse_config)
      ssparse_task.priority = 1
      ssparse_task.add_dependency(self._sim_tasks[id_sim])
      ssparse_task.add_condition(taskrun.FileModificationCondition(
        [sim_files['messages_mpf']],
        [ssparse_files['samples_csv'], ssparse_files['latency_csv'],
         ssparse_files['hops_csv']]))
      self._ssparse_tasks[id_ssparse] = ssparse_task

  # transient parse
  def _create_tparse_tasks(self, tm_var, f_name):
    # loop through all variables
    for tparse_config in self._dim_iter():
      # make id and name
      id_tparse = self._make_id(tparse_config, f_name=f_name)
      id_sim = self._make_id(tparse_config)
      tparse_files = self._get_tparse_files(id_tparse)
      sim_files = self._get_sim_files(id_sim)
      tparse_name = 'tparse_{0}'.format(id_tparse)

      # tparse cmd
      tparse_cmd = '{0} {1} {2} {3}'.format(
        self._transient_path,
        self._ssparse_path,
        sim_files['messages_mpf'],
        tparse_files['trans_csv'])

      filters =  self._parsings[f_name]['filters']
      extra_args = self._parsings[f_name]['transient']
      if self._latency_scalar != None:
        tparse_cmd += ' -s {0}'.format(self._latency_scalar)
      if extra_args != None:
        tparse_cmd += ' {0} '.format(extra_args)
      if filters != None:
        for filter in filters:
          tparse_cmd += ' -f {0}'.format(filter)

      self._all_cmds.append(tparse_cmd)
      # tparse task
      tparse_task = self._create_task_func(
        tm_var, tparse_name, tparse_cmd, None, 'tparse', tparse_config)
      tparse_task.priority = 1
      tparse_task.add_dependency(self._sim_tasks[id_sim])
      tparse_task.add_condition(taskrun.FileModificationCondition(
        [sim_files['messages_mpf']],[tparse_files['trans_csv']]))
      self._tparse_tasks[id_tparse] = tparse_task
  # ===================================================================
  # load-percent-minimal
  def _create_loadpermin_tasks(self, tm_var, f_name):
    # config with no load
    for loadpermin_config in self._dim_iter(dont=self._load_name):
      id_task1 = self._make_id(loadpermin_config, f_name = f_name)
      loadpermin_name = 'loadpermin_{0}'.format(id_task1)
      files1 = self._get_plot_files(id_task1)
      # loadpermin cmd
      loadpermin_cmd = ('ssplot load-percent-minimal {0} {1} {2} {3} '
                   .format(files1['loadpermin_png'],
                           self._start, self._stop, self._step))
      # plot settings
      plot_info = self._plots[('load-percent-minimal', f_name)]
      if plot_info['title_format'] != 'off':
        loadpermin_title = self._make_title(loadpermin_config, plot_info)
        loadpermin_cmd += (' --title {0} '.format(loadpermin_title))
      for key in plot_info['settings']:
        loadpermin_cmd += (' --{0} "{1}"'.format(
          key, plot_info['settings'][key]))
      # add to loadpermin_cmd the stats files
      for loads in  self._dim_iter(do_vars=self._load_name):
        id_ssparse = self._make_id(loadpermin_config, f_name = f_name,
                                   extra=self._make_id(loads))
        files_ssparse = self._get_ssparse_files(id_ssparse)
        loadpermin_cmd += ' {0}'.format(files_ssparse['hops_csv'])

      self._all_cmds.append(loadpermin_cmd)
      # create task
      loadpermin_task = self._create_task_func(
        tm_var, loadpermin_name, loadpermin_cmd, None,
        'loadpermin', loadpermin_config)
      loadpermin_task.priority = 1
      # add dependencies
      for loads in  self._dim_iter(do_vars=self._load_name):
        id_task3 = self._make_id(loadpermin_config, extra=self._make_id(loads),
                                 f_name = f_name)
        loadpermin_task.add_dependency(self._ssparse_tasks[id_task3])
      loadpermin_fmc = taskrun.FileModificationCondition(
        [], [files1['loadpermin_png']])
      # add input files to task
      for loads in self._dim_iter(do_vars=self._load_name):
        id_task4 = self._make_id(loadpermin_config, extra=self._make_id(loads),
                                 f_name = f_name)
        files3 = self._get_ssparse_files(id_task4)
        loadpermin_fmc.add_input(files3['hops_csv'])
      loadpermin_task.add_condition(loadpermin_fmc)

  # load-latency
  def _create_loadlat_tasks(self, tm_var, f_name):
    # config with no load
    for loadlat_config in self._dim_iter(dont=self._load_name):
      id_task1 = self._make_id(loadlat_config, f_name=f_name)
      loadlat_name = 'loadlat_{0}'.format(id_task1)
      files1 = self._get_plot_files(id_task1)
      # loadlat cmd
      loadlat_cmd = ('ssplot load-latency --row {0} {1} {2} {3} {4} '
                   .format(self._parsings[f_name]['latency_mode'].title(),
                           files1['loadlat_png'],
                           self._start, self._stop, self._step))
      # plot settings
      plot_info = self._plots[('load-latency', f_name)]
      if self._latency_units != None:
        loadlat_cmd += (' --latency_units {0}'.format(self._latency_units))
      if self._load_units != None:
        loadlat_cmd += (' --load_units {0}'.format(self._load_units))
      if plot_info['title_format'] != 'off':
        loadlat_title = self._make_title(loadlat_config, plot_info)
        loadlat_cmd += (' --title {0} '.format(loadlat_title))
      for key in plot_info['settings']:
        loadlat_cmd += (' --{0} "{1}"'.format(
          key,plot_info['settings'][key]))
      # add stats files
      for loads in  self._dim_iter(do_vars=self._load_name):
        id_task2 = self._make_id(loadlat_config, extra=self._make_id(loads),
                                 f_name=f_name)
        files2 = self._get_ssparse_files(id_task2)
        loadlat_cmd += ' {0}'.format(files2['latency_csv'])
      self._all_cmds.append(loadlat_cmd)
      # create task
      loadlat_task = self._create_task_func(
        tm_var, loadlat_name, loadlat_cmd, None, 'loadlat', loadlat_config)
      loadlat_task.priority = 1
      # add dependencies
      for loads in  self._dim_iter(do_vars=self._load_name):
        id_task3 = self._make_id(loadlat_config, extra=self._make_id(loads),
                                 f_name=f_name)
        loadlat_task.add_dependency(self._ssparse_tasks[id_task3])
      loadlat_fmc = taskrun.FileModificationCondition([],
                                                      [files1['loadlat_png']])
      # add input files to task
      for loads in self._dim_iter(do_vars=self._load_name):
        id_task4 = self._make_id(loadlat_config, extra=self._make_id(loads),
                                 f_name=f_name)
        files3 = self._get_ssparse_files(id_task4)
        loadlat_fmc.add_input(files3['latency_csv'])
      loadlat_task.add_condition(loadlat_fmc)

  # load-rate-percent
  def _create_loadrateper_tasks(self, tm_var, f_name):
    # config with no load
    for loadrateper_config in self._dim_iter(dont=self._load_name):
      id_task1 = self._make_id(loadrateper_config, f_name=f_name)
      id_sim = self._make_id(loadrateper_config)
      loadrateper_name = 'loadrateper_{0}'.format(id_task1)
      plot_files1 = self._get_plot_files(id_task1)
      sim_files1 = self._get_sim_files(id_sim)
      # loadrateper cmd
      loadrateper_cmd = ('ssplot load-rate-percent {0} {1} {2} {3}'
                   .format(plot_files1['loadrateper_png'],
                           self._start, self._stop, self._step))
      # add rate and hops files
      rates_files = ''
      hops_files = ''
      for loads in self._dim_iter(do_vars=self._load_name):
        id_task2 = self._make_id(loadrateper_config, extra=self._make_id(loads),
                                 f_name=f_name)
        ssparse_files2 = self._get_ssparse_files(id_task2)
        id_sim2 = self._make_id(loadrateper_config, extra=self._make_id(loads))
        sim_files2 = self._get_sim_files(id_sim2)
        rates_files += ' {0}'.format(sim_files2['rates_csv'])
        hops_files += ' {0}'.format(ssparse_files2['hops_csv'])
      loadrateper_cmd += ' --rate_stats {0}'.format(rates_files)
      loadrateper_cmd += ' --hops_stats {0}'.format(hops_files)
      # plot settings
      plot_info = self._plots[('load-rate-percent', f_name)]
      if plot_info['title_format'] != 'off':
        loadrateper_title = self._make_title(loadrateper_config, plot_info)
        loadrateper_cmd += (' --title {0} '.format(loadrateper_title))
      for key in plot_info['settings']:
        loadrateper_cmd += (' --{0} "{1}"'.format(
          key, plot_info['settings'][key]))
      self._all_cmds.append(loadrateper_cmd)
      # create task
      loadrateper_task = self._create_task_func(
        tm_var, loadrateper_name, loadrateper_cmd, None,
        'loadrateper', loadrateper_config)
      loadrateper_task.priority = 1
      # add dependencies
      for loads in  self._dim_iter(do_vars=self._load_name):
        id_task3 = self._make_id(loadrateper_config, extra=self._make_id(loads),
                                 f_name=f_name)
        loadrateper_task.add_dependency(self._ssparse_tasks[id_task3])

      loadrateper_fmc = taskrun.FileModificationCondition(
        [], [plot_files1['loadrateper_png']])
      # add input files to task
      for loads in self._dim_iter(do_vars=self._load_name):
        id_task4 = self._make_id(loadrateper_config, extra=self._make_id(loads),
                                 f_name=f_name)
        ssparse_files3 = self._get_ssparse_files(id_task4)
        id_sim4 = self._make_id(loadrateper_config, extra=self._make_id(loads))
        sim_files3 = self._get_sim_files(id_sim4)
        loadrateper_fmc.add_input(sim_files3['rates_csv'])
        loadrateper_fmc.add_input(ssparse_files3['hops_csv'])
      loadrateper_task.add_condition(loadrateper_fmc)

  # latency-pdf
  def _create_latpdf_tasks(self, tm_var, f_name):
    # loop through all variables
    for latpdf_config in self._dim_iter():
      id_task = self._make_id(latpdf_config, f_name=f_name)
      ssparse_files = self._get_ssparse_files(id_task)
      plot_files = self._get_plot_files(id_task)
      latpdf_name = 'latpdf_{0}'.format(id_task)
      latpdf_cmd = 'ssplot latency-pdf {0} {1} '.format(
        ssparse_files['samples_csv'],
        plot_files['latpdf_png'])

      # plot settings
      plot_info = self._plots[('latency-pdf',f_name)]
      if self._latency_units != None:
        latpdf_cmd += (' --latency_units {0}'.format(self._latency_units))
      if plot_info['title_format'] != 'off':
        latpdf_title = self._make_title(latpdf_config, plot_info)
        latpdf_cmd += (' --title {0} '.format(latpdf_title))
      for key in plot_info['settings']:
        latpdf_cmd += (' --{0} "{1}"'.format(
          key,plot_info['settings'][key]))

      self._all_cmds.append(latpdf_cmd)
      # create tasks
      latpdf_task = self._create_task_func(
        tm_var, latpdf_name, latpdf_cmd, None, 'latpdf', latpdf_config)
      latpdf_task.priority = 1
      latpdf_task.add_dependency(self._ssparse_tasks[id_task])
      latpdf_task.add_condition(taskrun.FileModificationCondition(
        [ssparse_files['samples_csv']],
        [plot_files['latpdf_png']]))

  # latency-percentile
  def _create_latperc_tasks(self, tm_var, f_name):
    # loop through all variables
    for latperc_config in self._dim_iter():
      id_task = self._make_id(latperc_config, f_name=f_name)
      ssparse_files = self._get_ssparse_files(id_task)
      plot_files = self._get_plot_files(id_task)
      latperc_name = 'latperc_{0}'.format(id_task)
      latperc_cmd = 'ssplot latency-percentile {0} {1} '.format(
        ssparse_files['samples_csv'],
        plot_files['latperc_png'])
      # plot settings
      plot_info = self._plots[('latency-percentile', f_name)]
      if self._latency_units != None:
        latperc_cmd += (' --latency_units {0}'.format(self._latency_units))
      if plot_info['title_format'] != 'off':
        latperc_title = self._make_title(latperc_config, plot_info)
        latperc_cmd += (' --title {0} '.format(latperc_title))
      for key in plot_info['settings']:
        latperc_cmd += (' --{0} "{1}"'.format(
          key,plot_info['settings'][key]))
      self._all_cmds.append(latperc_cmd)
      # create tasks
      latperc_task = self._create_task_func(
        tm_var, latperc_name, latperc_cmd, None, 'latperc', latperc_config)
      latperc_task.priority = 1
      latperc_task.add_dependency(self._ssparse_tasks[id_task])
      latperc_task.add_condition(taskrun.FileModificationCondition(
        [ssparse_files['samples_csv']],
        [plot_files['latperc_png']]))

  # latency-cdf
  def _create_latcdf_tasks(self, tm_var, f_name):
    # loop through all variables
    for latcdf_config in self._dim_iter():
      id_task = self._make_id(latcdf_config, f_name=f_name)
      ssparse_files = self._get_ssparse_files(id_task)
      plot_files = self._get_plot_files(id_task)
      latcdf_name = 'latcdf_{0}'.format(id_task)
      latcdf_cmd = 'ssplot latency-cdf {0} {1} '.format(
        ssparse_files['samples_csv'],
        plot_files['latcdf_png'])

      # plot settings
      plot_info = self._plots[('latency-cdf', f_name)]
      if self._latency_units != None:
        latcdf_cmd += (' --latency_units {0}'.format(self._latency_units))
      if plot_info['title_format'] != 'off':
        latcdf_title = self._make_title(latcdf_config, plot_info)
        latcdf_cmd += (' --title {0} '.format(latcdf_title))
      for key in plot_info['settings']:
        latcdf_cmd += (' --{0} "{1}"'.format(
          key,plot_info['settings'][key]))
      self._all_cmds.append(latcdf_cmd)
      # create tasks
      latcdf_task = self._create_task_func(
        tm_var, latcdf_name, latcdf_cmd, None, 'latcdf', latcdf_config)
      latcdf_task.priority = 1
      latcdf_task.add_dependency(self._ssparse_tasks[id_task])
      latcdf_task.add_condition(taskrun.FileModificationCondition(
        [ssparse_files['samples_csv']],
        [plot_files['latcdf_png']]))

  # load-average-hops
  def _create_loadavehops_tasks(self, tm_var, f_name):
    # config with no load
    for loadavehops_config in self._dim_iter(dont=self._load_name):
      id_task1 = self._make_id(loadavehops_config, f_name=f_name)
      loadavehops_name = 'loadavehops_{0}'.format(id_task1)
      files1 = self._get_plot_files(id_task1)
      # loadavehops cmd
      loadavehops_cmd = ('ssplot load-average-hops {0} {1} {2} {3} '
                   .format(files1['loadavehops_png'],
                           self._start, self._stop, self._step))
      # plot settings
      plot_info = self._plots[('load-average-hops', f_name)]
      if plot_info['title_format'] != 'off':
        loadavehops_title = self._make_title(loadavehops_config, plot_info)
        loadavehops_cmd += (' --title {0} '.format(loadavehops_title))
      for key in plot_info['settings']:
        loadavehops_cmd += (' --{0} "{1}"'.format(
          key, plot_info['settings'][key]))
      # add the stats files
      for loads in  self._dim_iter(do_vars=self._load_name):
        id_task2 = self._make_id(loadavehops_config, extra=self._make_id(loads),
                                 f_name=f_name)
        files2 = self._get_ssparse_files(id_task2)
        loadavehops_cmd += ' {0}'.format(files2['hops_csv'])
      self._all_cmds.append(loadavehops_cmd)
      # create task
      loadavehops_task = self._create_task_func(
        tm_var, loadavehops_name, loadavehops_cmd, None,
        'loadavehops', loadavehops_config)
      loadavehops_task.priority = 1
      # add dependencies
      for loads in  self._dim_iter(do_vars=self._load_name):
        id_task3 = self._make_id(loadavehops_config, extra=self._make_id(loads),
                                 f_name=f_name)
        loadavehops_task.add_dependency(self._ssparse_tasks[id_task3])
      loadavehops_fmc = taskrun.FileModificationCondition(
        [], [files1['loadavehops_png']])
      # add input files to task
      for loads in self._dim_iter(do_vars=self._load_name):
        id_task4 = self._make_id(loadavehops_config, extra=self._make_id(loads),
                                 f_name=f_name)
        files3 = self._get_ssparse_files(id_task4)
        loadavehops_fmc.add_input(files3['hops_csv'])
      loadavehops_task.add_condition(loadavehops_fmc)

  # time-latency-scatter
  def _create_timelatscat_tasks(self, tm_var, f_name):
    # loop through all variables
    for timelatscat_config in self._dim_iter():
      id_task = self._make_id(timelatscat_config, f_name=f_name)
      ssparse_files = self._get_ssparse_files(id_task)
      plot_files = self._get_plot_files(id_task)
      timelatscat_name = 'timelatscat_{0}'.format(id_task)
      timelatscat_cmd = 'ssplot time-latency-scatter {0} {1} '.format(
        ssparse_files['samples_csv'],
        plot_files['timelatscat_png'])

      # plot settings
      plot_info = self._plots[('time-latency-scatter', f_name)]
      if self._latency_units != None:
        timelatscat_cmd += (' --latency_units {0}'.format(self._latency_units))
      if plot_info['title_format'] != 'off':
        timelatscat_title = self._make_title(timelatscat_config, plot_info)
        timelatscat_cmd += (' --title {0} '.format(timelatscat_title))
      for key in plot_info['settings']:
        timelatscat_cmd += (' --{0} "{1}"'.format(
          key, plot_info['settings'][key]))
      self._all_cmds.append(timelatscat_cmd)
      # create tasks
      timelatscat_task = self._create_task_func(
        tm_var, timelatscat_name, timelatscat_cmd, None,
        'timelatscat', timelatscat_config)
      timelatscat_task.priority = 1
      timelatscat_task.add_dependency(self._ssparse_tasks[id_task])
      timelatscat_task.add_condition(taskrun.FileModificationCondition(
        [ssparse_files['samples_csv']],
        [plot_files['timelatscat_png']]))

  # time-percent-minimal
  def _create_timepermin_tasks(self, tm_var, f_name):
    # loop through all variables
    for timepermin_config in self._dim_iter():
      id_task = self._make_id(timepermin_config, f_name=f_name)
      plot_files = self._get_plot_files(id_task)
      tparse_files = self._get_tparse_files(id_task)
      timepermin_name = 'timepermin_{0}'.format(id_task)
      timepermin_cmd = 'ssplot time-percent-minimal {0} {1} '.format(
        tparse_files['trans_csv'],
        plot_files['timepermin_png'])

      # plot settings
      plot_info = self._plots[('time-percent-minimal', f_name)]
      if plot_info['title_format'] != 'off':
        timepermin_title = self._make_title(timepermin_config, plot_info)
        timepermin_cmd += (' --title {0} '.format(timepermin_title))
      for key in plot_info['settings']:
        timepermin_cmd += (' --{0} "{1}"'.format(
          key, plot_info['settings'][key]))
      self._all_cmds.append(timepermin_cmd)
      # create tasks
      timepermin_task = self._create_task_func(
        tm_var, timepermin_name, timepermin_cmd, None,
        'timepermin', timepermin_config)
      timepermin_task.priority = 1
      timepermin_task.add_dependency(self._tparse_tasks[id_task])
      timepermin_task.add_condition(taskrun.FileModificationCondition(
        [tparse_files['trans_csv']],
        [plot_files['timepermin_png']]))

  # time-average-hops
  def _create_timeavehops_tasks(self, tm_var, f_name):
    # loop through all variables
    for timeavehops_config in self._dim_iter():
      id_task = self._make_id(timeavehops_config, f_name=f_name)
      plot_files = self._get_plot_files(id_task)
      tparse_files = self._get_tparse_files(id_task)
      timeavehops_name = 'timeavehops_{0}'.format(id_task)
      timeavehops_cmd = 'ssplot time-average-hops {0} {1} '.format(
        tparse_files['trans_csv'],
        plot_files['timeavehops_png'])

      # plot settings
      plot_info = self._plots[('time-average-hops', f_name)]
      if plot_info['title_format'] != 'off':
        timeavehops_title = self._make_title(timeavehops_config, plot_info)
        timeavehops_cmd += (' --title {0} '.format(timeavehops_title))
      for key in plot_info['settings']:
        timeavehops_cmd += (' --{0} "{1}"'.format(
          key, plot_info['settings'][key]))
      self._all_cmds.append(timeavehops_cmd)
      # create tasks
      timeavehops_task = self._create_task_func(
        tm_var, timeavehops_name, timeavehops_cmd, None,
        'timeavehops', timeavehops_config)
      timeavehops_task.priority = 1
      timeavehops_task.add_dependency(self._tparse_tasks[id_task])
      timeavehops_task.add_condition(taskrun.FileModificationCondition(
        [tparse_files['trans_csv']],
        [plot_files['timeavehops_png']]))

  # time-latency
  def _create_timelat_tasks(self, tm_var, f_name):
    # loop through all variables
    for timelat_config in self._dim_iter():
      id_task = self._make_id(timelat_config, f_name=f_name)
      plot_files = self._get_plot_files(id_task)
      tparse_files = self._get_tparse_files(id_task)
      timelat_name = 'timelat_{0}'.format(id_task)
      timelat_cmd = 'ssplot time-latency {0} {1} '.format(
        tparse_files['trans_csv'],
        plot_files['timelat_png'])

      # plot settings
      plot_info = self._plots[('time-latency', f_name)]
      if self._latency_units != None:
        timelat_cmd += (' --latency_units {0}'.format(self._latency_units))
      if plot_info['title_format'] != 'off':
        timelat_title = self._make_title(timelat_config, plot_info)
        timelat_cmd += (' --title {0} '.format(timelat_title))
      for key in plot_info['settings']:
        timelat_cmd += (' --{0} "{1}"'.format(
          key, plot_info['settings'][key]))
      self._all_cmds.append(timelat_cmd)
      # create tasks
      timelat_task = self._create_task_func(
        tm_var, timelat_name, timelat_cmd, None,
        'timelat', timelat_config)
      timelat_task.priority = 1
      timelat_task.add_dependency(self._tparse_tasks[id_task])
      timelat_task.add_condition(taskrun.FileModificationCondition(
        [tparse_files['trans_csv']],
        [plot_files['timelat_png']]))

  # load-rate
  def _create_loadrate_tasks(self, tm_var, f_name):
    # config with no load
    for loadrate_config in self._dim_iter(dont=self._load_name):
      id_task1 = self._make_id(loadrate_config, f_name=f_name)
      id_sim = self._make_id(loadrate_config)
      loadrate_name = 'loadrate_{0}'.format(id_task1)
      plot_files1 = self._get_plot_files(id_task1)
      sim_files1 = self._get_sim_files(id_sim)
      # loadrate cmd
      loadrate_cmd = ('ssplot load-rate {0} {1} {2} {3}'
                   .format(plot_files1['loadrate_png'],
                           self._start, self._stop, self._step))
      # add stats
      for loads in self._dim_iter(do_vars=self._load_name):
        id_task2 = self._make_id(loadrate_config, extra=self._make_id(loads))
        sim_files2 = self._get_sim_files(id_task2)
        loadrate_cmd += ' {0}'.format(sim_files2['rates_csv'])
      # plot settings
      plot_info = self._plots[('load-rate', f_name)]
      if plot_info['title_format'] != 'off':
        loadrate_title = self._make_title(loadrate_config, plot_info)
        loadrate_cmd += (' --title {0} '.format(loadrate_title))
      for key in plot_info['settings']:
        loadrate_cmd += (' --{0} "{1}"'.format(
          key,plot_info['settings'][key]))
      self._all_cmds.append(loadrate_cmd)
      # create task
      loadrate_task = self._create_task_func(
        tm_var, loadrate_name, loadrate_cmd, None, 'loadrate', loadrate_config)
      loadrate_task.priority = 1
      # add dependencies
      for loads in  self._dim_iter(do_vars=self._load_name):
        id_task3 = self._make_id(loadrate_config, extra=self._make_id(loads))
        loadrate_task.add_dependency(self._sim_tasks[id_task3])
      loadrate_fmc = taskrun.FileModificationCondition(
        [], [plot_files1['loadrate_png']])
      # add input files to task
      for loads in self._dim_iter(do_vars=self._load_name):
        id_task4 = self._make_id(loadrate_config, extra=self._make_id(loads))
        sim_files3 = self._get_sim_files(id_task4)
        loadrate_fmc.add_input(sim_files3['rates_csv'])
      loadrate_task.add_condition(loadrate_fmc)

  # load-latency-compare
  def _create_loadlatcomp_tasks(self, tm_var, f_name):
    # loop over all vars that should compared and have more than 1 value
    for cvar in self._variables:
      if (cvar['name'] != self._load_name and cvar['compare']
          and len(cvar['values']) > 1):
        # count number of compare variables
        self._comp_var_count += 1
        # iterate all configurations for this variable (no l, no cvar)
        for loadlatcomp_config in self._dim_iter(dont=[self._load_name,
                                                 cvar['name']]):
          # iterate all latency distributions (9)
          for field in ssplot.LoadLatencyStats.FIELDS:
            field2 = field.replace('%','')
            # make id, plot title, png file
            id_task = self._make_id(loadlatcomp_config, extra=field2,
                                    f_name=f_name)
            loadlatcomp_name = 'loadlatcomp_{0}_{1}'.format(cvar['short_name'],
                                                            id_task)
            plot_files = self._get_plot_files(
              ('{0}_{1}'.format(cvar['short_name'], id_task)))
            # cmd
            loadlatcomp_cmd = ('ssplot load-latency-compare --row {0} ' \
                         '--field {1} {2} {3} {4} {5} '
                         .format(self._parsings[f_name]['latency_mode'].title(),
                                 field, plot_files['loadlatcomp_png'],
                                 self._start, self._stop, self._step))
            # plot settings
            plot_info = self._plots[('load-latency-compare',f_name)]
            if self._latency_units != None:
              loadlatcomp_cmd += (' --latency_units {0}'.format(
                self._latency_units))
            if self._load_units != None:
              loadlatcomp_cmd += (' --load_units {0}'.format(self._load_units))
            if plot_info['title_format'] != 'off':
              loadlatcomp_title = self._make_title(loadlatcomp_config,
                                                   plot_info, lat=field)
              loadlatcomp_cmd += (' --title {0} '.format(loadlatcomp_title))
            loadlatcomp_cmd += (' --legend_title "{0}" '.format(
              cvar['name']))
            for key in plot_info['settings']:
              loadlatcomp_cmd += (' --{0} "{1}"'.format(
                key, plot_info['settings'][key]))

            # loop through comp variable and loads to add agg files to cmd
            for var_load_config in self._dim_iter(do_vars=[cvar['name'],
                                                           self._load_name]):
              # create ordered config with cvar and load
              sim_config = self._create_config(loadlatcomp_config,
                                               var_load_config)
              id_task2 = self._make_id(sim_config, f_name=f_name)
              ssparse_files2 = self._get_ssparse_files(id_task2)
              loadlatcomp_cmd += ' {0}'.format(ssparse_files2['latency_csv'])
            # loop through comp variable to create legend
            for var_config in self._dim_iter(do_vars=cvar['name']):
              for var in var_config:
                loadlatcomp_cmd += ' --data_label "{0}"'.format(var['value'])
            for w in self._wanted_plots:
              if (w in plot_files['loadlatcomp_png']):
                self._plot_cmds.append(loadlatcomp_cmd)
                print("added", w)

            self._all_cmds.append(loadlatcomp_cmd)
            # create task
            loadlatcomp_task = self._create_task_func(
              tm_var, loadlatcomp_name, loadlatcomp_cmd, None,
              'loadlatcomp', loadlatcomp_config)
            loadlatcomp_task.priority = 1
            # add dependencies (loop through load and cvar)
            for var_load_config in self._dim_iter(do_vars=[cvar['name'],
                                                           self._load_name]):
              # create ordered config with cvar and load
              sim_config = self._create_config(loadlatcomp_config,
                                               var_load_config)
              id_task3 = self._make_id(sim_config, f_name=f_name)
              loadlatcomp_task.add_dependency(self._ssparse_tasks[id_task3])
            loadlatcomp_fmc = taskrun.FileModificationCondition(
              [], [plot_files['loadlatcomp_png']])
            for var_load_config in self._dim_iter(do_vars=[cvar['name'],
                                                           self._load_name]):
              # create ordered config with cvar and load
              sim_config = self._create_config(loadlatcomp_config,
                                               var_load_config)
              id_task4 = self._make_id(sim_config, f_name=f_name)
              ssparse_files3 = self._get_ssparse_files(id_task4)
              loadlatcomp_fmc.add_input(ssparse_files3['latency_csv'])
            loadlatcomp_task.add_condition(loadlatcomp_fmc)

  def _create_viewer_task(self):
    files = self._get_viewer_files()

    # resource files
    for resource, output in [(self._favicon_res, files['favicon']),
                             (self._mainlogo_res, files['mainlogo'])]:
      copy_resource(resource, output)

    # css
    colors = read_resource(self._colors_res).strip()
    self._background_color = colors.split(',')[0]
    self._text_color = colors.split(',')[1]
    css = get_css(self)
    with open(files['css'], 'w') as fd_css:
      print(css, file=fd_css)

    # html
    html_top = get_html_top(self)
    html_bottom = get_html_bottom(self)
    html_dyn = get_html_dyn(self, ssplot.LoadLatencyStats.FIELDS)

    html_all = html_top + html_dyn + html_bottom
    with open(files['html'], 'w') as fd_html:
      print(html_all, file=fd_html)

    # javascript
    get_params = get_URL_params()
    load_params = load_URL_params(self)
    add_params = add_URL_params(self)
    get_log = get_sim_log(self)

    show_div = get_show_div(self)
    cplot_divs = get_cplot_divs(self)
    create_name = get_create_name(self)
    compose_name = get_compose_name(self)

    js_all = load_params + get_params + show_div + cplot_divs + \
    create_name + get_log + compose_name + add_params
    with open(files['javascript'], 'w') as fd_js:
      print(js_all, file=fd_js)
