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

# css
def get_css():
  css = """\
html, body, .viewport {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
}

html *
{
    font-family: Metric, Arial, Helvetica, sans-serif !important;
    font-size: 14px;
}
p {
  word-break: break-all;
}
img {
    image-rendering: -moz-crisp-edges;         /* Firefox */
    image-rendering:   -o-crisp-edges;         /* Opera */
    image-rendering: -webkit-optimize-contrast;/* Webkit */
    image-rendering: crisp-edges;
    -ms-interpolation-mode: nearest-neighbor;  /* IE (non-standard property) */
}

.wrapper {
    display: -webkit-box;
    display: -moz-box;
    display: -ms-flexbox;
    display: -webkit-flex;
    display: flex;

    -webkit-flex-flow: row wrap;
    flex-flow: row wrap;
    text-align: center;

    height: 100%;
    margin: 0;
    padding: 0;

}
/* We tell all items to be 100% width */
.wrapper > * {
    padding: 10px;
    flex: 1 100%;
}

h2 {font-size: 20px !important; text-align:center;}

.logo img {height:45px;}


.main {text-align: center;}

.aside-1 {
  border-right: medium solid #614767;/* #C6C9CA;*/
  background: #fff; /*#eee*/
  /*background: #425563; color: #fff;*/
}

.plotImg {
    height: auto;
    width: auto;
    max-height: 100%;
    max-width: 100%;
}

/* Large format (side to side) */
@media all and (min-width: 1000px) {
    .aside-1 { text-align:left;
               -webkit-flex: 1 5%;
               flex: 1 5%;
               -webkit-order:1;
               order:1;}
    .main    { order: 2; flex:12;}

}

/* small format - nav top plot bottom */
@media (max-width: 1000px) {
    .wrapper { height: auto;}
    .logo img {height:40px;}
    .aside-1 {border: none; border-bottom: thin solid #C6C9CA;}
    .plotImg {height: auto; width:auto;}
    br {
        content: ' '
    }
    br:after {
        content: ' '
    }
}"""
  return css

# html
def get_html_top(self, files):
  html_top = ("""\
<!DOCTYPE html>
<html>
<head>
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
  <link rel="icon" type="image/png" href="https://www.hotplugs.co.uk/shop/media/ecom/cat/hpebox.png">
  <link rel="stylesheet" href="{0}">
  <script src="{1}"></script>
  <title>SuperSim Sweep</title>
</head>
<body>
<div class="wrapper">
  <!-- ==================================================================- -->
  <aside class="aside aside-1">
         <!-- --------------------------------- -->
         <div class="logo">
           <a href="."><img src="https://www.labs.hpe.com/img/home/labs-logo.png"
                           alt="HPE Labs logo"/></a>
           <h2>SuperSim Plot Viewer</h2>
         </div>
         <!-- --------------------------------- -->
         <div id="mode" style="padding-bottom:5px">
           Plot:<br>
           <select id="mode_sel" name="mode_select" onchange="showDiv(this)">
             <option disabled selected value> -- select an option -- </option>
""".format(files['css_in'], files['javascript_in']))
  d = ssplot.CommandLine.all_names()

  for plot_type, filter_name in sorted(self._plots.keys(), key=lambda x: x[1]):
    for pt in d:
      if plot_type in d[pt]:
        plot_name = d[pt][1]
        break
    if plot_type != "load-latency-compare" :
      html_top += ("""\
             <option value="{0}">[{1}] {2}</option>
      """.format(plot_name, filter_name, plot_type))
    elif self._comp_var_count != 0:
      html_top += ("""\
      <option value="{0}">[{1}] {2}</option>
      """.format(plot_name, filter_name, plot_type))
  html_top_end = """
           </select>
         </div>
         <hr>
<!-- --------------------------------- -->
  <div id="options">
"""
  return html_top + html_top_end

def get_html_bottom(self):
  html_bottom = """\
<!-- --------------------------------- -->
    <div id="settings" style="display:none">
      <p>Filename:</p>
      <p id="plot_name"></p>
    <hr>
    <p id ="sim_log" style="display:none">
      <a id="sim_log_a" href="" target="_blank">simulation log</a>
    </p>
    </div>
    <input id="cachingOff" type="checkbox" name="cachingoff" onclick="cashingfunc()"/> Bypass cache [Debug Mode] <br>
"""
  if self._readme is not None:
    html_bottom += """\
    <p> <a href="../README.txt" target="_blank">README</a> </p>
"""

  html_bottom2 = """\
  </div>
</aside>
<!-- ==================================================================- -->
<article class="main">
  <img class="plotImg" id="plot" src="" onError="noImgFile()" />
</article>
<!-- ==================================================================- -->
</div>
</body>
</html>"""
  return html_bottom + html_bottom2


def get_html_dyn(self, load_latency_stats):
  html_dyn = ""
  vars_selector = ""
  cmp_selector = ""

  # end of selector
  select_end = ("""</select><br></p>
</div>
""")
  # Comp Selector
  cmp_option = ""
  cmp_sel_top = ("""\
<div style ='display:none;' id="{0}">
<p>Compare Variable:<br>
<select id="{0}_sel" onchange="CplotDivs(this)">
""".format(self._id_cmp))
  # select an option
  disable_select = ("""\
<option disabled selected value> -- select an option -- </option>
""")

  # latency distribution selector
  ld_option = ""
  ld_top = ("""\
<div style ='display:none;' id="{0}">
<p>Latency Distribution:<br>
<select id="{0}_sel" onchange="createName()">
  <option disabled selected value> -- select an option -- </option>
""".format(self._id_lat_dist))

  # dynamic generation of selects for html
  for var in self._variables:
    # only one option - pre select it
    if len(var['values']) == 1:
      # start of selector
      select_start = ("""<div style ='display:none;' id="{1}">
<p>{0}:
<select id="{1}_sel" onchange="createName()">
""".format(var['name'], var['short_name'])) # no "select an option"

      # options - iterate through values
      select_option = ""
      for val in var['values']:
        select_option += ("""\
<option value="{0}" selected="true" disabled="disabled">{0}</option>
""".format(val))

    # more than 1 value - multiple options
    elif len(var['values']) > 1:
      # start of selector with select an option
      select_start = ("""<div style ='display:none;' id="{1}">
<p>{0}:<br>
<select id="{1}_sel" onchange="createName()">
  <option disabled selected value> -- select an option -- </option>
""".format(var['name'],
           var['short_name']))

      # options - iterate through values
      select_option = ""
      for val in var['values']:
        select_option += ("""  <option value="{0}">{0}</option>
""".format(val))

    selector = select_start + select_option + select_end
    vars_selector += selector

  # Compare Variables
  for var in self._variables:
    if var['compare'] and len(var['values']) > 1:
      cmp_option += ("""  <option value="{1}">{0} ({1})</option>
""".format(var['name'], var['short_name']))
  if self._comp_var_count == 0: # no compare variable
    cmp_option = ""
  else: # multiple comp variables
    cmp_option = disable_select + cmp_option

  # loop through latency distributions
  for field in load_latency_stats:
    field = field.replace('%','')
    ld_option += ("""  <option value="{0}">{0}</option>
""".format(field))

  ld_selector = ld_top + ld_option + select_end
  cmp_selector = cmp_sel_top + cmp_option + select_end

  # all dynamic selectors
  html_dyn = cmp_selector + vars_selector + ld_selector
  return html_dyn

# javascript
def load_URL_params(self):
  dyn = ""
  top ="""\
document.onreadystatechange=function(){
  var mode = getURLParameter('mode_sel');
  if (mode) {
    mode_obj = document.getElementById('mode_sel');
    document.getElementById('mode_sel').value = mode;   //  assign URL param to select field
  }
"""
  # loop through variables to assign parameters
  for var in self._variables:
    dyn += ("""
  var {0}_val = getURLParameter('{0}_sel');
  if ({0}_val) {{
    document.getElementById('{0}_sel').value = {0}_val;   //  assign URL param to select field
  }}
""").format(var['short_name'])

  lat_cmp = ("""\
  var {0}_val = getURLParameter('{0}_sel');
  if ({0}_val) {{
    document.getElementById('LatDist_sel').value = {0}_val;   //  assign URL param to select field
  }}

  var {1}_val = getURLParameter('{1}_sel');
  if ({1}_val) {{
    document.getElementById('{1}_sel').value = {1}_val;   //  assign URL param to select field
  }}
""").format(self._id_lat_dist, self._id_cmp)

  bottom = ("""\
if (mode == "loadlatcomp") {{
    document.getElementById('{0}').style.display = "block";
    if ({0}_val) {{
      c = document.getElementById('{0}_sel');
      CplotDivs(c);
    }}
  }} else {{
    showDiv(mode_obj);
  }}
}}
""").format(self._id_cmp)

  return top + dyn + lat_cmp + bottom

def get_URL_params():
  get_url =  """function getURLParameter(name) {
  return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search) || [null, ''])[1].replace(/\+/g, '%20')) || null;
}
"""
  return get_url

def get_show_div(self):
  top = """function showDiv(elem){
    document.getElementById("sim_log").style.display = "none";
"""
  load_var_top = """\
  if(elem.value == "latpdf"
|| elem.value == "latcdf"
|| elem.value == "latperc"
|| elem.value == "timelatscat"
|| elem.value == "timepermin"
|| elem.value == "timeavehops"
|| elem.value == "timelat" ) {{
    // no comp no loaddist
    document.getElementById('{0}').style.display = "none";
    document.getElementById('{1}').style.display = "none";
    document.getElementById("sim_log").style.display = "block";
""".format(self._id_cmp, self._id_lat_dist)

  var_only_top = """\
  }} else if (elem.value == "loadlat"
|| elem.value == "loadpermin"
|| elem.value == "loadavehops"
|| elem.value == "loadrateper"
|| elem.value == "loadrate" ) {{
    // no load no comp no loaddist
    document.getElementById('{0}').style.display = "none";
    document.getElementById('{1}').style.display = "none";
""".format(self._id_cmp, self._id_lat_dist)
# add no load

  cplot_top = """\
  }} else if (elem.value == "loadlatcomp") {{
    // only cmp selector
    document.getElementById('{0}').style.display = "block";
    document.getElementById('{0}').getElementsByTagName('option')[0].selected =
      "selected";
    document.getElementById('{1}').style.display = "none";
""".format(self._id_cmp, self._id_lat_dist)

  bottom = """\
  }
createName();
}
"""
  #--------------------------------------------#
  id_one = ""
  cplot_dyn = ""
  load_var_dyn = ""
  var_only_dyn = ""
  for var in self._variables:
    # many options
    if len(var['values']) > 1:
      load_var_dyn += """\
    document.getElementById('{0}').style.display = "block";
""".format(var['short_name'])
      var_only_dyn += """\
    document.getElementById('{0}').style.display = "block";
""".format(var['short_name'])

      cplot_dyn += """\
    document.getElementById('{0}').style.display = "none";
""".format(var['short_name'])

      # var_only has no load selector
      if var['name'] == self._load_name:
        var_only_dyn += """\
    document.getElementById('{0}').style.display = "none";
""".format(var['short_name'])
      else:
        var_only_dyn += """\
    document.getElementById('{0}').style.display = "block";
""".format(var['short_name'])

    # only one option do not display and color blue to add to filename
    elif len(var['values']) == 1:
      id_one += """\
   document.getElementById('{0}').style.color = "blue";
""".format(var['short_name'])

      load_var_dyn += """\
    document.getElementById('{0}').style.display = "none";
""".format(var['short_name'])
      var_only_dyn += """\
    document.getElementById('{0}').style.display = "none";
""".format(var['short_name'])

      cplot_dyn += """\
    document.getElementById('{0}').style.display = "none";
""".format(var['short_name'])

      # var_only has no load selector (if not needed)
      if var['name'] == self._load_name:
        var_only_dyn += """\
    document.getElementById('{0}').style.display = "none";
""".format(var['short_name'])
      else:
        var_only_dyn += """\
    document.getElementById('{0}').style.display = "none";
""".format(var['short_name'])

  return top + id_one + load_var_top + load_var_dyn + var_only_top + \
    var_only_dyn + cplot_top + cplot_dyn + bottom

def get_cplot_divs(self):
  top = """\
function CplotDivs(elem) {{
  document.getElementById('{0}').style.display = "block";
""".format(self._id_lat_dist)

  bottom = """\
  //deactive cvar
  document.getElementById(elem.value).style.display = "none";
  createName();
}
"""
  dyn = ""
  for var in self._variables:
    # no load selector
    if var['name'] == self._load_name:
      dyn += """\
  document.getElementById('{0}').style.display = "none"
""".format(var['short_name'])
    else:
      if len(var['values']) > 1:
        dyn += """\
  document.getElementById('{0}').style.display = "block";
""".format(var['short_name'])
      elif len(var['values']) == 1:
        dyn += """\
  document.getElementById('{0}').style.display = "none";
""".format(var['short_name'])
  return top + dyn + bottom


def get_create_name():
  create_name = """\
function noImgFile() {
  document.getElementById("plot_name").style.color = "red";
  document.getElementById("plot").style.display='none';
  document.getElementById("sim_log_a").style.color = "red";
}

function createName() {
  document.getElementById("settings").style.display = "block";
  document.getElementById("plot").style.display="block";
  document.getElementById("plot_name").innerHTML = composeName();
  document.getElementById("plot_name").style.color = "black";

  if ($('#cachingOff').is(':checked')) {
    document.getElementById('plot').src = '../plots/' + composeName() + '?time='+ new Date().getTime();
  } else {
    document.getElementById('plot').src = '../plots/' + composeName();
  }

  if (document.getElementById("mode_sel").value == "latpdf"
|| document.getElementById("mode_sel").value == "latcdf"
|| document.getElementById("mode_sel").value == "latperc"
|| document.getElementById("mode_sel").value == "timelatscat"
|| document.getElementById("mode_sel").value == "timepermin"
|| document.getElementById("mode_sel").value == "timeavehops"
|| document.getElementById("mode_sel").value == "timelat"
) {
    document.getElementById("sim_log_a").style.color = "blue";
    document.getElementById("sim_log_a").href = '../logs/' + getSimLog();
  }
  addURLparams();
}
"""
  return create_name


def get_sim_log(self):
  top = """\
function getSimLog() {
"""
  bottom = """\
  var y = "";
  for (var i = 0; i < vars_div_id.length; i++) {
    curr_elem = document.getElementById(vars_div_id[i]);
    if (curr_elem.style.display == "block") {
      y += '_'
      y += document.getElementById(vars_sel_id[i]).value;
    } else if(curr_elem.style.color == "blue") {
      y += '_'
      y += document.getElementById(vars_sel_id[i]).value;
    }
  }
  return 'simout' + y + '.log'
}
"""
  # format variables for js
  var_div_id = [] # list of div ids
  var_sel_id = [] # list of selectors ids
  # div ids
  var_div_id.append(self._id_cmp)
  for var in self._variables:
    var_div_id.append(var['short_name'])
  var_div_id.append(self._id_lat_dist)
  # slector ids
  for v_id in var_div_id:
    sid = v_id + '_sel'
    var_sel_id.append(sid)

  dyn = """\
  var vars_div_id = {0};
  var vars_sel_id = {1};
""".format(var_div_id, var_sel_id)
  return top + dyn + bottom


def get_compose_name(self):
  top = """\
function composeName() {
  plot_select = document.getElementById("mode_sel")
  var m = plot_select.value;
  var f = plot_select.options[plot_select.selectedIndex].text;
  f = f.split('[')[1].split(']')[0];

"""
  bottom = """\
  // get displayed div values
  var y = "";
  var cmp_var = ""
  for (var i = 0; i < vars_div_id.length; i++) {{
    curr_elem = document.getElementById(vars_div_id[i]);
    if (curr_elem.style.display == "block") {{
       if (vars_div_id[i] != "{0}") {{
         y += '_'
         y += document.getElementById(vars_sel_id[i]).value;
       }} else {{
        cmp_var = '_' + document.getElementById(vars_sel_id[i]).value;
       }}
    }} else if(curr_elem.style.color == "blue") {{
      if (vars_div_id[i] != 'l') {{
        y += '_'
        y += document.getElementById(vars_sel_id[i]).value;
      }} else if (m == "latpdf"
                 || m == "latcdf"
                 || m == "latperc"
                 || m == "timelatscat"
                 || m == "timepermin"
                 || m == "timeavehops"
                 || m == "timelat"
                 ) {{
        y += '_'
        y += document.getElementById(vars_sel_id[i]).value;
      }}
    }}
  }}
  return m + cmp_var + '_' + f + y + '.png'
}}
""".format(self._id_cmp)
  # format variables for js
  var_div_id = [] # list of div ids
  var_sel_id = [] # list of selectors ids
  # div ids
  var_div_id.append(self._id_cmp)
  for var in self._variables:
    var_div_id.append(var['short_name'])
  var_div_id.append(self._id_lat_dist)
  # slector ids
  for v_id in var_div_id:
    sid = v_id + '_sel'
    var_sel_id.append(sid)

  dyn = """\
  var vars_div_id = {0};
  var vars_sel_id = {1};
""".format(var_div_id, var_sel_id)
  return top + dyn + bottom


def add_URL_params(self):
  top = """\
function addURLparams() {
  var params = "";
  var m = document.getElementById("mode_sel").value;
  params += "mode_sel=" + m;
"""
  bottom = """\
  // get displayed div values
  val = '';
  for (var i = 0; i < vars_div_id.length; i++) {
    curr_elem = document.getElementById(vars_div_id[i]);
    if (curr_elem.style.display == "block") {
      val = document.getElementById(vars_sel_id[i]).value;
      params += "&" + vars_sel_id[i] + '=' + val;
    } else if(curr_elem.style.color == "blue") {
      val = document.getElementById(vars_sel_id[i]).value;
      params += "&" + vars_sel_id[i] + '=' + val;
    }
  }

  history.pushState(null, '', 'index.html?'+params);
}
"""
  # format variables for js
  var_div_id = [] # list of div ids
  var_sel_id = [] # list of selectors ids
  # div ids
  var_div_id.append(self._id_cmp)
  for var in self._variables:
    var_div_id.append(var['short_name'])
  var_div_id.append(self._id_lat_dist)
  # slector ids
  for v_id in var_div_id:
    sid = v_id + '_sel'
    var_sel_id.append(sid)

  dyn = """\
  var vars_div_id = {0};
  var vars_sel_id = {1};
""".format(var_div_id, var_sel_id)
  return top + dyn + bottom
