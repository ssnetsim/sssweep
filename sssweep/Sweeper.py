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

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import os
import copy
import ssplot
import taskrun
from .web_viewer_gen import *

class Sweeper(object):

  def __init__(self, supersim_path, settings_path, sslatency_path, out_dir,
               parse_scalar=None, parse_filters=[], latency_units=None,
               latency_ymin=None, latency_ymax=None,
               rate_ymin=None, rate_ymax=None,
               plot_style=None, plot_size=None,
               titles='short', title_style='colon',
               latency_mode='packet',
               sim=True, parse=True,
               qplot=True, lplot=True, rplot=True, cplot=True,
               web_viewer=True,
               get_resources=None,
               readme=None):
    """
    Constructs a Sweeper object

    Args:
      supersim_path  : path to supersim bin
      settings_path  : path to settings file
      sslatency_path : path to sslatency bin
      out_dir        : location of output files directory
      parse_scalar   : latency scalar for parsing
      latency_units  : unit of latency for plots
      latency_ymin   : ymin for latency plots
      latency_ymax   : ymax for latency plots
      rate_ymin      : ymin for rate plots
      rate_ymax      : ymax for rate plots
      plot_style     : styling of plots (colormap, line styles)
      plot_size      : size of plot e.g. 16x10
      titles         : plot titles format (short, long, off)
      title_style    : style of plot titles (colon : or equal = )
      latency_mode   : 'packet-header', 'packet', 'message', 'transaction'
      sim, parse     : bools to enable/disable sim and parsing
      qplot          : enable/disable quad plots
      lplot          : enable/disable load vs. latency plots
      rplot          : enable/disable load vs. latency plots
      cplot          : enable/disable comparison plots
      web_viewer     : bool to enable/disable web viewer generation
      get_resources  : pointer to set resource function for tasks
      readme         : text for readme file
    """
    # paths
    self._supersim_path = os.path.abspath(os.path.expanduser(supersim_path))
    self._out_dir = os.path.abspath(os.path.expanduser(out_dir))
    self._settings_path = os.path.abspath(os.path.expanduser(settings_path))
    self._sslatency_path = os.path.abspath(os.path.expanduser(sslatency_path))

    # plot settings
    self._parse_scalar = parse_scalar
    self._parse_filters = parse_filters
    self._latency_units = latency_units
    self._latency_ymin = latency_ymin
    self._latency_ymax = latency_ymax
    self._rate_ymin = rate_ymin
    self._rate_ymax = rate_ymax
    if plot_style is not None:
      assert plot_style in ['rainbow', 'rainbow-dots', 'black', 'inferno', 'inferno-dots', 'inferno-markers']
    self._plot_style = plot_style
    self._plot_size = plot_size # 16x10
    assert titles in ['long', 'short', 'off']
    self._titles = titles
    assert title_style in ['colon', 'equal']
    self._title_style = title_style
    assert latency_mode in ['packet-header', 'packet', 'message', 'transaction']
    self._latency_mode = latency_mode.split('-')[0]  # this ignores '-header'
    self._header_latency = latency_mode == 'packet-header'

    # task activation
    self._sim = sim
    self._parse = parse
    self._qplot = qplot
    self._lplot = lplot
    self._rplot = rplot
    self._cplot = cplot
    self._web_viewer = web_viewer
    self._get_resources = get_resources

    # load sweep values
    self._start = None
    self._stop = None
    self._step = None

    self._variables = []
    self._created = False
    self._load_variable = None
    self._load_name = None

    # variables for javascript
    self._id_cmp = "Cmp"
    self._id_lat_dist = "LatDist"
    self._comp_var_count = 0

    # store tasks
    self._sim_tasks = {}
    self._parse_tasks = {}

    # ensure the settings file exists
    if not os.path.isfile(self._settings_path):
      self._error('{0} does not exist'.format(self._settings_path))

    # ensure the supersim bin exists
    if not os.path.isfile(self._supersim_path):
      self._error('{0} does not exist'.format(self._supersim_path))

    # ensure the sslatency bin exists
    if not os.path.isfile(self._sslatency_path):
      self._error('{0} does not exist'.format(self._sslatency_path))

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
    #readme
    self._readme = readme
    if self._readme is not None:
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

    # web_viewer
    web_viewer_f = os.path.join(self._out_dir, self._viewer_folder)
    if not os.path.isdir(web_viewer_f):
      try:
        os.mkdir(web_viewer_f)
      except:
        self._error('couldn\'t create {0}'.format(web_viewer_f))

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
    loads = ['{0:.02f}'.format(x_values/100)
             for x_values in range(start, stop+1, step)]
    assert len(loads) > 0
    lconfig = {'name': name, 'short_name': short_name, 'values': list(loads),
               'command': set_command, 'compare' : False, 'values_dic': None}
    # add the variables
    self._load_variable = lconfig
    self._load_name = name
    self._start = start
    self._stop = stop
    self._step = step

  def add_variable(self, name, short_name, values, set_command, compare=True):
    """
    This adds a sweep variable to the config variable

    Args:
      name          : name of sweep variable
      short_name     : acronym of sweep variable for filename
      values        : values of variable to sweep through
      set_command    : pointer to command function
      compare       : should this variable be compared in cplot
    """
    # verify unique values
    assert len(values) == len(set(values)), 'Duplicate value detected'

    # check more than 1 value was given for variable
    assert len(values) > 0

    # build the variable
    configall = {'name': name, 'short_name': short_name, 'values': list(values),
                 'command': set_command, 'compare': compare}
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
      if widths[dim] is not 1:
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

  def _make_id(self, config, extra=None):
    """
    This creates id for task

    Args:
      config   : input config to iterate
      extra    : extra values to append at the end (list or string)
    """
    values = [y_var['value'] for y_var in config]
    if extra:
      if isinstance(extra, str):
        values.append(extra)
      elif isinstance(extra, list):
        values.extend(extra)
      else:
        assert False
    return '_'.join([str(x_values) for x_values in values])

  def _make_title(self, config, plot_type, cvar=None, lat_dist=None):
    """
    This creates titles for plots
    # qplot
     Latency (TrafficPattern: UR, RoutingAlgorithm: AD, Load: 0.56)
     Lat (TP: UR, RA: AD, LD: 0.56)
     Lat (TP=UR RA=AD LD=0.56)

    # rplots
     Accepted Rate (TrafficPattern: UR, RoutingAlgorithm: AD)
     Rate (TP: UR, RA: AD)

    # lplots
     Load vs. Latency (TrafficPattern: UR, RoutingAlgorithm: AD)
     LvL (TP: UR, RA: AD)

    # cplots
     RoutingAlgorithm Comparison (TrafficPattern: UR [Mean])
     RA Cmp (TP: UR [Mean])
    """

    if self._title_style is 'colon':
      separ = ': '
      delim = ', '
    else:
      separ = '='
      delim = ' '

    #tuples
    name_values = []
    for y_values in config:
      if self._titles == 'long':
        name_values.append((y_values['name'], str(y_values['value'])))
      elif self._titles == 'short':
        name_values.append((y_values['short_name'], str(y_values['value'])))

    #format
    title = ''
    # name values
    for idx, x_values in enumerate(name_values):
      tmp = separ.join(x_values)
      if idx != len(name_values)-1:
        title += tmp + delim
      else:
        title += tmp
    # qplot
    if plot_type == 'qplot':
      if self._titles == 'long':
        title = '"Latency ({0})"'.format(title)
      elif self._titles == 'short':
        title = '"Lat ({0})"'.format(title)
    #lplot
    if plot_type == 'lplot':
      if self._titles == 'long':
        title = '"Load vs. Latency ({0})"'.format(title)
      elif self._titles == 'short':
        title = '"LvL ({0})"'.format(title)
    #rplot
    if plot_type == 'rplot':
      if self._titles == 'long':
        title = '"Delivered Rate ({0})"'.format(title)
      elif self._titles == 'short':
        title = '"Rate ({0})"'.format(title)
    #cplot
    if plot_type == 'cplot':
      if self._titles == 'long':
        title = '"{0} Comparison ({1} [{2}])"'.format(
          cvar['name'], title, lat_dist)
      elif self._titles == 'short':
        title = '"{0} Cmp ({1} [{2}])"'.format(
          cvar['short_name'], title, lat_dist)
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
    assert cmd is not None, 'You must return a command modifier'
    if isinstance(cmd, str):
      cmd = [cmd]
    clean = ' ' + ' '.join([str(x_values) for x_values in [y for y in cmd]])
    return clean

  def _get_files(self, id_task):
    """
    This creates file names for a given id_task

    Args:
      id_task   : id_task to generate files for
    """
    dir_var = self._out_dir
    return {
      'messages_mpf'  : os.path.join(
        dir_var, self._data_folder, 'messages_{0}.mpf.gz'.format(id_task)),
      'rates_csv'     : os.path.join(
        dir_var, self._data_folder, 'rates_{0}.csv.gz'.format(id_task)),
      'channels_csv'  : os.path.join(
        dir_var, self._data_folder, 'channels_{0}.csv.gz'.format(id_task)),
      'latency_csv'   : os.path.join(
        dir_var, self._data_folder, 'latency_{0}.csv.gz'.format(id_task)),
      'aggregate_csv' : os.path.join(
        dir_var, self._data_folder, 'aggregate_{0}.csv.gz'.format(id_task)),
      'usage_log'     : os.path.join(
        dir_var, self._logs_folder, 'usage_{0}.log'.format(id_task)),
      'simout_log'    : os.path.join(
        dir_var, self._logs_folder, 'simout_{0}.log'.format(id_task)),
      'qplot_png'     : os.path.join(
        dir_var, self._plots_folder, 'qplot_{0}.png'.format(id_task)),
      'rplot_png'     : os.path.join(
        dir_var, self._plots_folder, 'rplot_{0}.png'.format(id_task)),
      'lplot_png'     : os.path.join(
        dir_var, self._plots_folder, 'lplot_{0}.png'.format(id_task)),
      'cplot_png'     : os.path.join(
        dir_var, self._plots_folder, 'cplot_{0}.png'.format(id_task)),
      'html'          : os.path.join(
        dir_var, self._viewer_folder, 'index.html'),
      'javascript'    : os.path.join(
        dir_var, self._viewer_folder, 'dynamic_plot.js'),
      'css'           : os.path.join(
        dir_var, self._viewer_folder, 'style.css'),
      'javascript_in' : 'dynamic_plot.js',
      'css_in'        : 'style.css'
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

    # generate tasks
    if self._sim:
      print("Creating simulation tasks")
      self._create_sim_tasks(tm_var)
    if self._parse:
      print("Creating parsing tasks")
      self._create_parse_tasks(tm_var)
    if self._qplot:
      print("Creating qplot tasks")
      self._create_qplot_tasks(tm_var)
    if self._lplot:
      print("Creating lplot tasks")
      self._create_lplot_tasks(tm_var)
    if self._rplot:
      print("Creating rplot tasks")
      self._create_rplot_tasks(tm_var)
    if self._cplot:
      print("Creating cplot tasks")
      self._create_cplot_tasks(tm_var)
    if self._web_viewer:
      print("Creating viewer")
      self._create_web_viewer_task()

  def _create_sim_tasks(self, tm_var):
    # create config
    for sim_config in self._dim_iter():
      # make id & name
      id_task = self._make_id(sim_config)
      files = self._get_files(id_task)
      sim_name = 'sim_{0}'.format(id_task)
      # sim command
      sim_cmd = ('/usr/bin/time -v -o {0} {1} {2} '
                 'workload.message_log.file=string={3} '
                 'workload.applications[0].rate_log.file=string={4} '
                 'network.channel_log.file=string={5}'
                ).format(
                  files['usage_log'],
                  self._supersim_path,
                  self._settings_path,
                  files['messages_mpf'],
                  files['rates_csv'],
                  files['channels_csv'])
      #loop through each variable commands to add
      for var in sim_config:
        tmp_cmd = var['command'](var['value'], sim_config)
        cmd = self._cmd_clean(tmp_cmd)
        sim_cmd += cmd
      # sim task
      sim_task = taskrun.ProcessTask(tm_var, sim_name, sim_cmd)
      sim_task.stdout_file = files['simout_log']
      sim_task.stderr_file = files['simout_log']
      if self._get_resources is not None:
        sim_task.resources = self._get_resources('sim', sim_config)
      sim_task.priority = 0
      sim_task.add_condition(taskrun.FileModificationCondition(
        [], [files['messages_mpf'], files['rates_csv'], files['channels_csv']]))
      self._sim_tasks[id_task] = sim_task

  def _create_parse_tasks(self, tm_var):
    # loop through all variables
    for parse_config in self._dim_iter():
      # make id and name
      id_task = self._make_id(parse_config)
      files = self._get_files(id_task)
      parse_name = 'parse_{0}'.format(id_task)
      # parse cmd
      parse_cmd = '{0} -{1} {2} -a {3} {4}'.format(
        self._sslatency_path,
        self._latency_mode[:1].lower(),
        files['latency_csv'],
        files['aggregate_csv'],
        files['messages_mpf'])
      if self._header_latency:
        parse_cmd += ' --headerlatency'

      if self._parse_scalar is not None:
        parse_cmd += ' -s {0}'.format(self._parse_scalar)

      # parse filters
      for filter in self._parse_filters:
        parse_cmd += ' -f {0}'.format(filter)

      # parse task
      parse_task = taskrun.ProcessTask(tm_var, parse_name, parse_cmd)
      if self._get_resources is not None:
        parse_task.resources = self._get_resources('parse', parse_config)
      parse_task.priority = 1
      parse_task.add_dependency(self._sim_tasks[id_task])
      parse_task.add_condition(taskrun.FileModificationCondition(
        [files['messages_mpf']],
        [files['latency_csv'], files['aggregate_csv']]))
      self._parse_tasks[id_task] = parse_task

  def _create_qplot_tasks(self, tm_var):
    # loop through all variables
    for qplot_config in self._dim_iter():
      id_task = self._make_id(qplot_config)
      files = self._get_files(id_task)
      qplot_name = 'qplot_{0}'.format(id_task)

      qplot_cmd = 'sslqp {0} {1} '.format(
        files['latency_csv'],
        files['qplot_png'])

      # plot settings
      if self._titles != 'off':
        qplot_title = self._make_title(qplot_config, 'qplot')
        qplot_cmd += (' --title {0} '.format(qplot_title))
      if self._latency_units is not None:
        qplot_cmd += (' --units {0} '.format(self._latency_units))
      if self._plot_size is not None:
        qplot_cmd += (' --size {0} '.format(self._plot_size))

      # create tasks
      qplot_task = taskrun.ProcessTask(tm_var, qplot_name, qplot_cmd)
      if self._get_resources is not None:
        qplot_task.resources = self._get_resources('qplot', qplot_config)
      qplot_task.priority = 1
      qplot_task.add_dependency(self._parse_tasks[id_task])
      qplot_task.add_condition(taskrun.FileModificationCondition(
        [files['latency_csv']],
        [files['qplot_png']]))

  def _create_rplot_tasks(self, tm_var):
    # config with no load
    for rplot_config in self._dim_iter(dont=self._load_name):
      id_task1 = self._make_id(rplot_config)
      rplot_name = 'rplot_{0}'.format(id_task1)
      files1 = self._get_files(id_task1)

      # rplot cmd
      rplot_cmd = ('sslrp {0} {1} {2} {3}'
                   .format(files1['rplot_png'],
                           self._start, self._stop + 1, self._step))

      # add to rplot_cmd the load files- sweep load
      for loads in self._dim_iter(do_vars=self._load_name):
        id_task2 = self._make_id(rplot_config, extra=self._make_id(loads))
        files2 = self._get_files(id_task2)
        rplot_cmd += ' {0}'.format(files2['rates_csv'])

      if self._titles != 'off':
        rplot_title = self._make_title(rplot_config, 'rplot')
        rplot_cmd += (' --title {0} '.format(rplot_title))

      # check plot settings
      if self._rate_ymin is not None:
        rplot_cmd += (' --ymin {0}'.format(self._rate_ymin))
      if self._rate_ymax is not None:
        rplot_cmd += (' --ymax {0}'.format(self._rate_ymax))
      if self._plot_size is not None:
        rplot_cmd += (' --size {0} '.format(self._plot_size))
      if self._plot_style is not None:
        rplot_cmd += (' --style {0} '.format(self._plot_style))

      # create task
      rplot_task = taskrun.ProcessTask(tm_var, rplot_name, rplot_cmd)
      if self._get_resources is not None:
        rplot_task.resources = self._get_resources('rplot', rplot_config)
      rplot_task.priority = 1
      # add dependencies
      for loads in  self._dim_iter(do_vars=self._load_name):
        id_task3 = self._make_id(rplot_config, extra=self._make_id(loads))
        rplot_task.add_dependency(self._parse_tasks[id_task3])

      rplot_fmc = taskrun.FileModificationCondition([], [files1['rplot_png']])

      # add input files to task
      for loads in self._dim_iter(do_vars=self._load_name):
        id_task4 = self._make_id(rplot_config, extra=self._make_id(loads))
        files3 = self._get_files(id_task4)
        rplot_fmc.add_input(files3['rates_csv'])
      rplot_task.add_condition(rplot_fmc)

  def _create_lplot_tasks(self, tm_var):
    # config with no load
    for lplot_config in self._dim_iter(dont=self._load_name):
      id_task1 = self._make_id(lplot_config)
      lplot_name = 'lplot_{0}'.format(id_task1)
      files1 = self._get_files(id_task1)
      # lplot cmd
      lplot_cmd = ('ssllp --row {0} {1} {2} {3} {4} '
                   .format(self._latency_mode.title(), files1['lplot_png'],
                           self._start, self._stop + 1, self._step))

      if self._titles != 'off':
        lplot_title = self._make_title(lplot_config, 'lplot')
        lplot_cmd += (' --title {0} '.format(lplot_title))

      # check plot settings
      if self._latency_units is not None:
        lplot_cmd += (' --units {0}'.format(self._latency_units))
      if self._latency_ymin is not None:
        lplot_cmd += (' --ymin {0}'.format(self._latency_ymin))
      if self._latency_ymax is not None:
        lplot_cmd += (' --ymax {0}'.format(self._latency_ymax))
      if self._plot_size is not None:
        lplot_cmd += (' --size {0} '.format(self._plot_size))
      if self._plot_style is not None:
        lplot_cmd += (' --style {0} '.format(self._plot_style))

      # add to lplot_cmd the load files- sweep load
      for loads in  self._dim_iter(do_vars=self._load_name):
        id_task2 = self._make_id(lplot_config, extra=self._make_id(loads))
        files2 = self._get_files(id_task2)
        lplot_cmd += ' {0}'.format(files2['aggregate_csv'])

      # create task
      lplot_task = taskrun.ProcessTask(tm_var, lplot_name, lplot_cmd)
      if self._get_resources is not None:
        lplot_task.resources = self._get_resources('lplot', lplot_config)
      lplot_task.priority = 1
      # add dependencies
      for loads in  self._dim_iter(do_vars=self._load_name):
        id_task3 = self._make_id(lplot_config, extra=self._make_id(loads))
        lplot_task.add_dependency(self._parse_tasks[id_task3])

      lplot_fmc = taskrun.FileModificationCondition([], [files1['lplot_png']])

      # add input files to task
      for loads in self._dim_iter(do_vars=self._load_name):
        id_task4 = self._make_id(lplot_config, extra=self._make_id(loads))
        files3 = self._get_files(id_task4)
        lplot_fmc.add_input(files3['aggregate_csv'])
      lplot_task.add_condition(lplot_fmc)

  def _create_cplot_tasks(self, tm_var):
    # loop over all vars that should compared and have more than 1 value
    for cvar in self._variables:
      if (cvar['name'] is not self._load_name and cvar['compare']
          and len(cvar['values']) > 1):
        # count number of compare variables
        self._comp_var_count += 1
        # iterate all configurations for this variable (no l, no cvar)
        for cplot_config in self._dim_iter(dont=[self._load_name,
                                                 cvar['name']]):
          # iterate all latency distributions (9)
          for field in ssplot.LoadLatencyStats.FIELDS:
            field2 = field.replace('%','')
            # make id, plot title, png file
            id_task = self._make_id(cplot_config, extra=field2)
            cplot_name = 'cplot_{0}_{1}'.format(cvar['short_name'], id_task)
            files = self._get_files(('{0}_{1}'.format(cvar['short_name'],
                                                      id_task)))

            # cmd
            cplot_cmd = ('sslcp --row {0} --field {1} {2} {3} {4} {5} '
                         .format(self._latency_mode.title(),
                                 field, files['cplot_png'],
                                 self._start, self._stop + 1, self._step))
            # title
            if self._titles != 'off':
              cplot_title = self._make_title(cplot_config, 'cplot', cvar=cvar,
                                           lat_dist=field)
              cplot_cmd += (' --title {0} '.format(cplot_title))

            # add plot settings if they exist
            if self._latency_units is not None:
              cplot_cmd += (' --units {0}'.format(self._latency_units))
            if self._latency_ymin is not None:
              cplot_cmd += (' --ymin {0}'.format(self._latency_ymin))
            if self._latency_ymax is not None:
              cplot_cmd += (' --ymax {0}'.format(self._latency_ymax))
            if self._plot_size is not None:
              cplot_cmd += (' --size {0} '.format(self._plot_size))
            if self._plot_style is not None:
              cplot_cmd += (' --style {0} '.format(self._plot_style))

            # loop through comp variable and loads to add agg files to cmd
            for var_load_config in self._dim_iter(do_vars=[cvar['name'],
                                                           self._load_name]):
              # create ordered config with cvar and load
              sim_config = self._create_config(cplot_config, var_load_config)
              id_task2 = self._make_id(sim_config)
              files2 = self._get_files(id_task2)
              cplot_cmd += ' {0}'.format(files2['aggregate_csv'])
            # loop through comp variable to create legend
            for var_config in self._dim_iter(do_vars=cvar['name']):
              for var in var_config:
                cplot_cmd += ' --label "{0}"'.format(var['value'])

            # create task
            cplot_task = taskrun.ProcessTask(tm_var, cplot_name, cplot_cmd)
            if self._get_resources is not None:
              cplot_task.resources = self._get_resources('cplot', cplot_config)
            cplot_task.priority = 1
            # add dependencies (loop through load and cvar)
            for var_load_config in self._dim_iter(do_vars=[cvar['name'],
                                                           self._load_name]):
              # create ordered config with cvar and load
              sim_config = self._create_config(cplot_config, var_load_config)
              id_task3 = self._make_id(sim_config)
              cplot_task.add_dependency(self._parse_tasks[id_task3])
            cplot_fmc = taskrun.FileModificationCondition(
              [], [files['cplot_png']])
            for var_load_config in self._dim_iter(do_vars=[cvar['name'],
                                                           self._load_name]):
              # create ordered config with cvar and load
              sim_config = self._create_config(cplot_config, var_load_config)
              id_task4 = self._make_id(sim_config)
              files3 = self._get_files(id_task4)
              cplot_fmc.add_input(files3['aggregate_csv'])
            cplot_task.add_condition(cplot_fmc)

  def _create_web_viewer_task(self):
    files = self._get_files('')

    # css
    css = get_css()
    with open(files['css'], 'w') as fd_css:
      print(css, file=fd_css)

    # html
    html_top = get_html_top(self, files)
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
    create_name = get_create_name()
    compose_name = get_compose_name(self)

    js_all = load_params + get_params + show_div + cplot_divs + create_name + \
    get_log + compose_name + add_params
    with open(files['javascript'], 'w') as fd_js:
      print(js_all, file=fd_js)
