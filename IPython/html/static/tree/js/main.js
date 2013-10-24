//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// On document ready
//============================================================================

if (typeof console == "undefined") { var console = {}; console.log = function () { }; }

$.ajaxSetup({ cache: false, dataType: 'json' });

function fromDtoDate(dateStr) {
    return new Date(parseFloat(/Date\(([^)]+)\)/.exec(dateStr)[1]));
}
function toTwitterTime(a) {
    var b = new Date();
    var c = typeof a == "date" ? a : new Date(a);
    var d = b - c;
    var e = 1000, minute = e * 60, hour = minute * 60, day = hour * 24, week = day * 7;
    if (isNaN(d) || d < 0) { return "" }
    if (d < e * 7) { return "right now" }
    if (d < minute) { return Math.floor(d / e) + " secs ago" }
    if (d < minute * 2) { return "about 1 min ago" }
    if (d < hour) { return Math.floor(d / minute) + " mins ago" }
    if (d < hour * 2) { return "about 1 hour ago" }
    if (d < day) { return Math.floor(d / hour) + " hours ago" }
    if (d > day && d < day * 2) { return "yesterday" }
    if (d < day * 365) { return Math.floor(d / day) + " days ago" } else { return "over a year ago" }
}
function enc(html) {
    if (typeof html != "string") return html;
    return html.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function dirPath(path) {
    if (typeof path != "string") return path;
    var strPos = path.lastIndexOf('/', path.length - 1);
    if (strPos == -1) return path;
    return path.substr(0, strPos);
}
function _mkAjax(url, data, callback, type, method) {
    if ($.isFunction(data)) {
        callback = data, data = {};
    }
    return $.ajax({ type: method, url: url, data: data, success: callback, contentType: type });
}
$.extend({
    put: function (url, data, callback, type) {
        return _mkAjax(url, data, callback, type, 'PUT');
    },
    del: function (url, data, callback, type) {
        return _mkAjax(url, data, callback, type, 'DELETE');
    }
});

var href = "/api/contents", lastHref = "";

var mkdir = function () {
    var dir = $("#dirname");
    if (!dir.val()) {
        alert("Enter the name of the folder first");
        dir.focus();
        return;
    }
    $.post(href + "/" + dir.val(), null, function () { dir.val(''); refresh(); });
};
$(".mkdir .btn").click(mkdir);
$(".mkdir INPUT").keypress(function (e) { if (e.which == '13') mkdir(); });
$(".upload .btn").click(function () {
    var file = $("#fileupload").val();
    if (!file) {
        alert("Select a file to upload first");
        return;
    }
    try {
        $.ajaxFileUpload({
            url: href,
            secureuri: false,
            fileElementId: 'fileupload',
            success: refresh
        });
    }
    catch (e) {
        alert("Not supported in this browser");
    }
});
$(".btn").mousedown(function () { $(this).toggleClass("mousedown"); });
$(".btn").mouseup(function () { $(this).toggleClass("mousedown"); });

var refresh = function (callback, skipPushState) {
    if (!skipPushState && window.history.pushState)
        window.history.pushState(href, href.replace('/', ' / '), '#!' + href);

    var dirs = href.replace(/\/$/, "").split('/');
    var sb = '<div id="breadcrumb">';
    var sbDirs = "";
    for (var i = 0; i < dirs.length; i++) {
        var dir = dirs[i];
        if (!dir) continue;
        sb += (i == dirs.length - 1)
        ? '<strong>' + dir + '</strong>'
        : '<a href="#!' + sbDirs + dir + '">' + dir + '</a><b>/</b>';
        sbDirs += dir + "/";
    }
    $("#breadcrumb").html(sb + "</div>");

    var jqLs = $("#ls");
    $.getJSON(href, function (r) {
        var navBack = lastHref.length > href.length && lastHref.substr(0, href.length) == href,
        nextCls = navBack ? "results-0" : "results-2",
        hasResults = $("#ls TABLE").length == 1,
        cls = !hasResults ? "results-1" : nextCls;
        var sb = "<div class='" + cls + "'><table><thead><tr><th>name</th><th>age</th><th>size</th></thead><tbody>";

        var file = r.File;
        if (file) {
            if (!file.IsTextFile) {
                location.href = href + "?ForDownload=true";
                setTimeout(function () { window.history.back() }, 1000);
                return;
            }

            var jqFile = $("#fileview");
            var sb = "<h3><a class='btn edit' href='#!savechanges'><span>save changes</span></a></dd>"
               + "<span class='ib txt'></span><dl><dd>" + enc(file.FileSizeBytes) + " bytes</dd><dd>"
               + toTwitterTime(fromDtoDate(file.ModifiedDate)) + "</dd>"
               + '<dd><a class="btn download" href="' + href + '?ForDownload=true"><span>download file</span></a></dd>'
               + "</dl></h3>"
               + "<textarea>" + enc(file.Contents) + "</textarea>";
            jqFile.html(sb).show();

            var height = $("#footer").position().top - $("#ls").position().top;
            $("#fileview TEXTAREA").height(height - 65);

            $("#fileadmin").hide();
            $("#ls").html("").hide();
            return;
        }

        $("#fileview").html("").hide();
        var dirList = r.Directory;
        if (dirList) {
            if (dirs.length > 1) {
                var upHref = href.substr(0, href.lastIndexOf('/', href.length - 2));
                sb += "<tr><td><a class='up-dir' href='#!" + upHref + "'>..<a></td><td></td><td></td></tr>";
            }
            $.each(dirList.Folders, function (i, dir) {
                sb += "<tr><td><a class='dir' href='#!" + href + "/" + dir.Name + "'>" + dir.Name + "/<a></td><td>"
                + toTwitterTime(fromDtoDate(dir.ModifiedDate)) + "</td><td>"
                + dir.FileCount + " files</td>";
            });
            $.each(dirList.Files, function (i, file) {
                sb += "<tr><td><a class='file' href='#!" + href + "/" + file.Name + "'><b class='del' href='#!deletefile'></b>" + file.Name + "</a></td><td>"
                + toTwitterTime(fromDtoDate(file.ModifiedDate)) + "</td><td>"
                + file.FileSizeBytes + " bytes</td>";
            });
        }

        sb += "</tbody></table></div>";

        $("#fileadmin").show();
        $("#ls").show().append(sb);

        var jq1 = $(".results-1"), jq2 = $("." + nextCls), el1 = jq1[0], el2 = jq2[0];
        if (el1 && el2) {
            jqLs.css({ "min-height": Math.max(jq1.height(), jq2.height()) + "px" });

            jq1.addClass(navBack ? "slide-right" : "slide-left");
            jq2.addClass(navBack ? "slide-right" : "slide-left");

            setTimeout(function () {
                jqLs.children().first().remove();
                jqLs.children().first()[0].className = "results-1";
            }, 450);
        }
        else {
            $("#ls").css({ "min-height": jq1.height() + "px" });
        }
    });
}

window.onpopstate = function (e) {
    e = e || event;
    if (!e.state) return;
    href = e.state;
    refresh(null, true);
};

var clickHandlers = {
    files: function (el, e, href) {
        if (e.ctrlKey || e.shiftKey) {
            window.open('#!' + href);
            return;
        }
        refresh();
    },
    savechanges: function () {
        $.put(lastHref, { TextContents: $("#fileview textarea").val() }, refresh, 'application/x-www-form-urlencoded');
        href = dirPath(lastHref), location.hash = "#!" + href;
    },
    deletefile: function (el) {
        var fileHref = $(el.parentNode).attr('href').substr(2);
        $.del(fileHref, refresh);
        href = dirPath(fileHref), location.hash = "#!" + href;
    },
    revertfiles: function () {
        if (!confirm("Are you sure you want to revert the filesystem back to its original state?")) return;
        href = "files", location.hash = "#!files";
        $.post("revertfiles", null, refresh);
        return;
    },
    closechoice: function () {
        document.body.className = "";
        href = "files", location.hash = "#!files";
        refresh();
    }
}

$(document).click(function (e) {
    var attrHref, el = e.target;
    do { attrHref = el.getAttribute("href"); } while (!attrHref && (el = el.parentElement));
    if (!attrHref) return;

    if (attrHref.substr(0, 2) === "#!") {
        lastHref = href, href = attrHref.substr(2);
        var cmd = href.split('/')[0];

        var clickHandler = clickHandlers[cmd];
        if (clickHandler) {
            if (e.preventDefault) e.preventDefault();
            clickHandler(el, e, href);
        }
    }
});

var hash = location.hash.indexOf('#!') === 0 && location.hash.substr(2);
if (hash) href = hash;
refresh();


$(document).ready(function () {

    IPython.page = new IPython.Page();

    $('#new_notebook').button().click(function (e) {
        IPython.notebook_list.new_notebook($('body').data('baseProjectUrl'))
    });

    IPython.notebook_list = new IPython.NotebookList('#notebook_list');
    IPython.cluster_list = new IPython.ClusterList('#cluster_list');
    IPython.login_widget = new IPython.LoginWidget('#login_widget');

    var interval_id=0;
    // auto refresh every xx secondes, no need to be fast,
    //  update is done at least when page get focus
    var time_refresh = 60; // in sec

    var enable_autorefresh = function(){
        //refresh immediately , then start interval
        if($('.upload_button').length == 0)
        {
            IPython.notebook_list.load_sessions();
            IPython.cluster_list.load_list();
        }
        if (!interval_id){
            interval_id = setInterval(function(){
                    if($('.upload_button').length == 0)
                    {
                        IPython.notebook_list.load_sessions();
                        IPython.cluster_list.load_list();
                    }
                }, time_refresh*1000);
            }
    }

    var disable_autorefresh = function(){
        clearInterval(interval_id);
        interval_id = 0;
    }

    // stop autorefresh when page lose focus
    $(window).blur(function() {
        disable_autorefresh();
    })

    //re-enable when page get focus back
    $(window).focus(function() {
        enable_autorefresh();
    });

    // finally start it, it will refresh immediately
    enable_autorefresh();

    IPython.page.show();
    
    // bound the upload method to the on change of the file select list
    $("#alternate_upload").change(function (event){
        IPython.notebook_list.handelFilesUpload(event,'form');
    });
    
    // set hash on tab click
    $("#tabs").find("a").click(function() {
        window.location.hash = $(this).attr("href");
    })
    
    // load tab if url hash
    if (window.location.hash) {
        $("#tabs").find("a[href=" + window.location.hash + "]").click();
    }


});

