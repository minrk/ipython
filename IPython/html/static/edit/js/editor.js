// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'jquery',
    'base/js/utils',
    'codemirror/lib/codemirror',
    'codemirror/mode/meta',
    'codemirror/addon/comment/comment',
    'codemirror/addon/dialog/dialog',
    'codemirror/addon/edit/closebrackets',
    'codemirror/addon/edit/matchbrackets',
    'codemirror/addon/search/searchcursor',
    'codemirror/addon/search/search',
    'codemirror/keymap/emacs',
    'codemirror/keymap/sublime',
    'codemirror/keymap/vim',
    ],
function($,
    utils,
    CodeMirror
) {
    "use strict";
    
    var Editor = function(selector, options) {
        var that = this;
        this.selector = selector;
        this.contents = options.contents;
        this.events = options.events;
        this.base_url = options.base_url;
        this.file_path = options.file_path;
        this.config = options.config;
        this.codemirror = null;
        this.generation = -1;
        
        // It appears we have to set commands on the CodeMirror class, not the
        // instance. I'd like to be wrong, but since there should only be one CM
        // instance on the page, this is good enough for now.
        CodeMirror.commands.save = $.proxy(this.save, this);
        
        this.save_enabled = false;
        
        // wait for config to load, then load file
        this.config.loaded.then(function () {
            var cfg = that.config.data.Editor || {};
            var cmopts = $.extend({},
                Editor.default_codemirror_options,
                cfg.codemirror_options || {}
            );
            that.codemirror = new CodeMirror($(that.selector)[0], cmopts);
            that.load();
            that.events.trigger('config_changed.Editor', {config: that.config})
        });
    };
    
    // default CodeMirror options
    Editor.default_codemirror_options = {
        extraKeys: {
            "Tab" :  "indentMore",
        },
        indentUnit: 4,
        theme: "ipython",
        lineNumbers: true,
    };
    
    Editor.prototype.load = function() {
        var that = this;
        var cm = this.codemirror;
        this.contents.get(this.file_path, {type: 'file', format: 'text'})
            .then(function(model) {
                cm.setValue(model.content);
                
                // Find and load the highlighting mode
                var modeinfo = CodeMirror.findModeByMIME(model.mimetype);
                if (modeinfo) {
                    utils.requireCodeMirrorMode(modeinfo.mode, function() {
                        cm.setOption('mode', modeinfo.mode);
                    });
                }
                that.save_enabled = true;
                that.generation = cm.changeGeneration();
            },
            function(error) {
                cm.setValue("Error! " + error.message +
                                "\nSaving disabled.");
                that.save_enabled = false;
            }
        );
    };
    window.CodeMirror = CodeMirror;

    Editor.prototype.save = function() {
        if (!this.save_enabled) {
            console.log("Not saving, save disabled");
            return;
        }
        var model = {
            path: this.file_path,
            type: 'file',
            format: 'text',
            content: this.codemirror.getValue(),
        };
        var that = this;
        // record change generation for isClean
        this.generation = this.codemirror.changeGeneration();
        this.contents.save(this.file_path, model).then(function() {
            that.events.trigger("save_succeeded.TextEditor");
        });
    };
    
    Editor.prototype.update_codemirror_options = function (options) {
        /** update codemirror options locally and save changes in config */
        var that = this;
        var cmopts = {};
        for (var opt in options) {
            if (!options.hasOwnProperty(opt)) {
                continue
            }
            var value = options[opt];
            console.log(opt, value);
            this.codemirror.setOption(opt, value);
            cmopts[opt] = value;
        }
        
        return this.config.update({
            Editor: {
                codemirror_options: cmopts
            }
        }).then(
            that.events.trigger('config_changed.Editor', {config: that.config})
        );
    };

    return {Editor: Editor};
});
