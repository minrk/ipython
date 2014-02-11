//----------------------------------------------------------------------------
//  Copyright (C) 2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Tour of IPython Notebok UI (with Bootstrap Tour)
//============================================================================

var step_duration = 5000;
var tour_steps = [
  { 
    element: $("#ipython_notebook").parent(),
    title: "Let's take it from the top",
    placement: 'bottom',
    content: "This is the Header.",
    backdrop: true,
  }, {
    element: "#ipython_notebook",
    title: "Header",
    placement: 'bottom',
    content: "Clicking here takes you back to the Dashboard."
  }, {
    element: "#notebook_name",
    title: "Filename",
    placement: 'bottom',
    content: "You can click here to change the filename for this notebook."
  }, 
          {
    element: "#checkpoint_status",
    title: "Checkpoint status",
    placement: 'bottom',
    content: "Information about the last time this notebook was saved."
  }, {
    element: "#menus",
    placement: 'bottom',
    title: "Notebook Menubar",
    content: "The actions that you can perform with this notebook, its cells, and its kernel"
  }, {
    element: "#menus",
    placement: 'bottom',
    title: "Notebook Menubar",
    content: "The actions that you can perform with this notebook, its cells, and its kernel"
  }, {
    element: "#notification_kernel",
    placement: 'bottom',
    onShow: function(tour) {  IPython.notification_area.widget_dict.kernel.set_message("sample notification"); },
    onHide: function(tour) {  IPython.notification_area.widget_dict.kernel.set_message("sample notification", 100); },
    title: "Notification area",
    content: "Message in response to user action (Kernel busy, Interrupt, etc)"
  }, {
    element: "#modal_indicator",
    title: "Mode indicator",
    placement: 'bottom',
    content: "IPython has two modes: Edit Mode and Command Mode. This indicator tells you which mode you are in."
  }, {
    element: "#modal_indicator",
    title: "Mode indicator",
    placement: 'bottom',
    content: "Right now you are in Command mode, and many keyboard shortcuts are available."
  }, {
    element: "#modal_indicator",
    title: "Edit Mode",
    placement: 'bottom',
    onShow: function(tour) { IPython.notebook.edit_mode(); },
    content: "And now we've switched to Edit Mode, regular typing will go into the currently active cell."
  }, {
    element: $('.selected'),
    title: "Edit Mode",
    placement: 'bottom',
    onHide: function(tour) { IPython.notebook.command_mode(); },
    content: "Notice that the border around the currently active cell changed color."
  }, {
    element: "#kernel_indicator",
    title: "Kernel indicator",
    placement: 'bottom',
    content: "This is the Kernel indicator. It looks like this when the Kernel is idle.",
  }, {
    element: "#kernel_indicator",
    title: "Kernel Indicator",
    placement: 'bottom',
    onShow: function(tour) { $([IPython.events]).trigger('status_busy.Kernel'); },
    onHide: function(tour) { $([IPython.events]).trigger('status_idle.Kernel');},
    content: "The Kernel indicator looks like this when the Kernel is busy.",
  }
];
var tour = new Tour({
    //orphan: true,
    storage: false, // start tour from beginning every time
    //element: $("#ipython_notebook"),
    debug: true,
    reflex: true, // click on element to continue tour
    //backdrop: true, // show dark behind popover
    animation: false,
    duration: step_duration,
    onStart: function() { console.log('tour started'); },
    steps: tour_steps,
});
// Initialize the tour
tour.init();

// Start the tour
tour.start();
