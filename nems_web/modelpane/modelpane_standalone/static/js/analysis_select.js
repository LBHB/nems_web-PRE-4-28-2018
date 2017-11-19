$(document).ready(function(){
        
    // TODO: Split this up into multile .js files? getting a bit crowded in here,
    // could group by functionality at this point.    

    //socketio -- not working?
    namespace = '/py_console'
    var socket = io.connect(
            location.protocol + '//'
            + document.domain + ':' 
            + location.port + namespace,
            {'timeout':0}
            );
            
    socket.on('connect', function() {
       console.log('socket connected');
    });
    
    socket.on('console_update', function(msg){
        //console.log('received console_update from server');
        $('#py_console').prepend("<p class='py_con_msg'>" + msg.data + "</p>");
    });
    
    // use this in place of console.log to send to py_console
    function py_console_log(message){
      $('#py_console').prepend("<p class='py_con_msg'>" + message + "</p>");        
    }

    //initializes bootstrap popover elements
    $('[data-toggle="popover"]').popover({
        trigger: 'click',
    });
    
    function initTable(table){
        // Called any time results is updated -- set table options here
        table.DataTable({
            paging: false,
            search: {
                "caseInsensitive": true,
            },
            //responsive: true,
            // TODO: add select option to replace custom one
            // (can add ctrl/shift click etc)
        });
    }
    
    var analysisCheck = document.getElementById("analysisSelector").value;
    if ((analysisCheck !== "") && (analysisCheck !== undefined) && (analysisCheck !== null)){
        updateBatchModel();
        updateAnalysisDetails();
    }
    
    
    $("#selectAllCells").on('click', selectCellsCheck);
    
    function selectCellsCheck(){
        var cellOptions = document.getElementsByName("cellOption[]");
        for (var i=0;i<cellOptions.length;i++){
            if (document.getElementById("selectAllCells").checked){
                cellOptions[i].setAttribute("selected",true);
            } else{
                cellOptions[i].removeAttribute("selected");
            }
        }
        updateResults();                           
    }
    
    $("#selectAllModels").on('click', selectModelsCheck);
    
    function selectModelsCheck(){
        var modelOptions = document.getElementsByName("modelOption[]");
        for (var i=0;i<modelOptions.length;i++){
            if (document.getElementById("selectAllModels").checked){
                modelOptions[i].setAttribute("selected",true);
            } else{
                modelOptions[i].removeAttribute("selected");
            }
        }
        updateResults();
    }
    
    
    $("#analysisSelector").change(updateBatchModel);

    function updateBatchModel(){
        // if analysis selection changes, get the value selected
        var aSelected = $("#analysisSelector").val();
        // pass the value to '/update_batch' in nemsweb.py
        // get back associated batchnum and change batch selector to match
        $.ajax({
            url: $SCRIPT_ROOT + '/update_batch',
            data: { aSelected:aSelected }, 
            type: 'GET',
            success: function(data) {
                $("#batchSelector").val(data.batch).change();
            },
            error: function(error) {
                console.log(error);
            }
        });
        // also pass analysis value to 'update_models' in nemsweb.py
        $.ajax({
            url: $SCRIPT_ROOT + '/update_models',
            data: { aSelected:aSelected }, 
            type: 'GET',
            success: function(data) {
                var models = $("#modelSelector");
                models.empty();
                             
                $.each(data.modellist, function(modelname) {
                    models.append($("<option></option>")
                        .attr("value", data.modellist[modelname])
                        .attr("name","modelOption[]")
                        .text(data.modellist[modelname]));
                });
                    
                selectModelsCheck();
            },
            error: function(error) {
                console.log(error);
            }     
        });
    };

    $("#batchSelector").change(updateCells);

    function updateCells(){
        // TODO: update cell list when batch changes
        //       should cascade from change to analysis selection
        // if batch selection changes, get the value of the new selection
        var bSelected = $("#batchSelector").val();
        var aSelected = $("#analysisSelector").val();

        $.ajax({
            url: $SCRIPT_ROOT + '/update_cells',
            data: { bSelected:bSelected, aSelected:aSelected },
            type: 'GET',
            success: function(data) {
                cells = $("#cellSelector");
                cells.empty();
                
                $.each(data.celllist, function(cell) {
                    cells.append($("<option></option>")
                        .attr("value", data.celllist[cell])
                        .attr("name","cellOption[]")
                        .text(data.celllist[cell]));                    
                });
                    
                selectCellsCheck();
            },
            error: function(error) {
                console.log(error);
            }    
        });
    };
     
    // initialize display option variables
    var colSelected = [];
    var ordSelected;
    var sortSelected;
    
    // update function for each variable
    function updatecols(){
        var checks = document.getElementsByName('result-option[]');
        colSelected.length = 0; //empty out the options, then push the new ones
        for (var i=0; i < checks.length; i++) {
            if (checks[i].checked) {
                colSelected.push(checks[i].value);
            }
        }
    }
    
    function updateOrder(){
        var order = document.getElementsByName('order-option[]');
        for (var i=0; i < order.length; i++) {
            if (order[i].checked) {
                ordSelected = order[i].value;
                return false;
            }
        }
    }
    
    function updateSort(){
        var sort = document.getElementsByName('sort-option[]');
        for (var i=0; i < sort.length; i++) {
            if (sort[i].checked) {
                sortSelected = sort[i].value;
                return false;
            }
        }
    }
            
    // update at start of page, and again if changes are made
    updatecols();
    ordSelected = updateOrder();
    sortSelected = updateSort();

    $("#batchSelector,#modelSelector,#cellSelector,.result-option,#rowLimit,.order-option,.sort-option")
    .change(updateResults);
            
    function updateResults(){
        
        updatecols();
        updateOrder();
        updateSort();
        
        var bSelected = $("#batchSelector").val();
        var cSelected = $("#cellSelector").val();
        var mSelected = $("#modelSelector").val();
        var rowLimit = $("#rowLimit").val();
                         
        $.ajax({
            url: $SCRIPT_ROOT + '/update_results',
            data: { bSelected:bSelected, cSelected:cSelected, 
                   mSelected:mSelected, colSelected:colSelected,
                   rowLimit:rowLimit, ordSelected:ordSelected,
                   sortSelected:sortSelected },
            type: 'GET',
            success: function(data) {
                //grabs whole div - replace inner html with new table?
                results = $("#tableWrapper");
                results.html(data.resultstable)
                initTable(results.children("table"));
            },
            error: function(error) {
                console.log(error);
            }
        });
    }

    $("#batchSelector,#modelSelector,#cellSelector,#measureSelector,#analysisSelector")
    .change(function(){
        var empty = false;
        $(".plot-form").each(function() {
            if (!($(this).val()) || ($(this).val().length == 0)) {
                    empty = true;
                }
        });
        
        if (empty){
            $(".plotsub").attr('disabled','disabled');
            //$("#form-warning").html("<p>Selection required for each option before submission</p>")
        } else {
            $(".plotsub").removeAttr('disabled');
            //$("#form-warning").html("")
        }   
    });

    ////////////////////////////////////////////////////////////////////////
    //         Analysis details, tags/status, edit/delete/new             //
    ////////////////////////////////////////////////////////////////////////

    $("#analysisSelector").change(updateAnalysisDetails);
            
    function updateAnalysisDetails(){
        var aSelected = $("#analysisSelector").val();
        
        $.ajax({
            url: $SCRIPT_ROOT + '/update_analysis_details',
            data: { aSelected:aSelected },
            type: 'GET',
            success: function(data) {
                $("#analysisDetails").attr("data-content",data.details)
                $("#analysisDetails").attr("title",aSelected)
            },
            error: function(error) {
                console.log(error);
            }
        });
    }
    
    var tagSelected;
    var statSelected;
    
    function updateTag(){
        var tags = document.getElementsByName('tagOption[]');
        for (var i=0; i < tags.length; i++) {
            if (tags[i].checked) {
                tagSelected = tags[i].value;
                return false;
            }
        }
    }
    
    function updateStatus(){
        var status = document.getElementsByName('statusOption[]');
        for (var i=0; i < status.length; i++) {
            if (status[i].checked) {
                statSelected = status[i].value;
                return false;
            }
        }
    }
    
    updateTag();
    updateStatus();
    updateAnalysis();
    $(".tagOption, .statusOption").change(updateAnalysis);
    
    function updateAnalysis(){
        updateTag();
        updateStatus();

        $.ajax({
           url: $SCRIPT_ROOT + '/update_analysis',
           data: { tagSelected:tagSelected, statSelected:statSelected },
           type: 'GET',
           success: function(data){
                analyses = $("#analysisSelector");
                analyses.empty();
                
                $.each(data.analysislist, function(analysis) {
                    analyses.append($("<option></option>")
                        .attr("value", data.analysislist[analysis])
                        .text(data.analysislist[analysis]));
                });
                    
                $("#analysisSelector").val($("#analysisSelector option:first").val()).change();
           },
           error: function(error){
                console.log(error);
           }
        });
    }
            
    function updateTagOptions(){
        $.ajax({
           url: $SCRIPT_ROOT + '/update_tag_options',
           type: 'GET',
           success: function(data){
               tags = $("#tagFilters")
               tags.empty();
               tags.append(
                        "<ul class='list-unstyled col-sm-6'>"
                        + "<li>"
                        + "<input class='statusOption' name='statusOption[]' type="
                        + "'radio' value='__any' checked>"
                        + "<span class='lbl'> Any </span>"
                        + "</li>"
                        )
               
               $.each(data.taglist, function(tag){
                   if (tag%12 == 0){
                       tags.append(
                                "</ul><ul class='list-unstyled col-sm-6'>"
                                )        
                   }
                   
                   tags.append(
                           "<li>"
                            + "<input class='tagOption'"
                            + "name='tagOption[]' type='radio' value="
                            + data.taglist[tag] + "'" + ">"
                            + "<span class='lbl'>" + data.taglist[tag] + "</span>"
                            + "</li>"
                            )
               });
               tags.append("</ul>");    
            
           },
           error: function(error){
               console.log(error);
           }        
        });
    }
    
    function updateStatusOptions(){
        $.ajax({
           url: $SCRIPT_ROOT + '/update_status_options',
           type: 'GET',
           success: function(data){
               statuses = $("#statusFilters")
               statuses.empty();
               statuses.append(
                        "<li>"
                        + "<input class='statusOption' name='statusOption[]' type="
                        + "'radio' value='__any' checked>"
                        + "<span class='lbl'> Any </span>"
                        + "</li>"
                        )
               
               $.each(data.statuslist, function(status){
                   if (status == 0){
                       var checked = 'checked'
                   } else{
                       var checked = '' 
                   }
                   statuses.append(
                            "<li>"
                            + "<input class='tagOption'"
                            + "name='tagOption[]' type='radio' value="
                            + data.statuslist[status] + "'" + ">"
                            + "<span class='lbl'>" + data.statuslist[status]
                            + "</span>"
                            + "</li>"
                            )
               });
           },
           error: function(error){
               console.log(error);
           }        
        });
    }
    
    $("#newAnalysis").on('click',newAnalysis);
    
    function newAnalysis(){
        $("[name='editName']").val('');
        $("[name='editStatus']").val('');
        $("[name='editTags']").val('');
        $("[name='editQuestion']").html('');
        $("[name='editAnswer']").html('');
        $("[name='editTree']").val('');
    }
    
    $("#editAnalysis").on('click',editAnalysis);
    
    function editAnalysis(){
        // get current analysis selection
        // ajax call to get back name, tags, question, etc
        // fill in content of editor modal with response
        
        var aSelected = $("#analysisSelector").val();
        
        $.ajax({
            url: $SCRIPT_ROOT + '/get_current_analysis',
            data: { aSelected:aSelected },
            type: 'GET',
            success: function(data){
                $("[name='editName']").val(data.name);
                $("[name='editStatus']").val(data.status);
                $("[name='editTags']").val(data.tags);
                $("[name='editQuestion']").html(data.question);
                $("[name='editAnswer']").html(data.answer);
                $("[name='editTree']").val(data.tree);
            },
            error: function(error){
                console.log(error);        
            }                
        });
    }
    
    $("#submitEditForm").on('click',verifySubmit);
    
    
    // TODO: change this to run nested ajax call instead of .submit()
    // so that entire page doesn't have to refresh afterward. should only have
    // to call updateAnalysis() to refresh the list for analysis selector.
    
    function verifySubmit(){
        var nameEntered = $("[name='editName']").val();
        
        $.ajax({
           url: $SCRIPT_ROOT + '/check_analysis_exists',
           data: { nameEntered:nameEntered },
           type: 'GET',
           success: function(data){
                if (data.exists){
                    alert("WARNING: An analysis by the same name already exists.\n" +
                          "Submitting this form without changing the name will\n" +
                          "overwrite the existing analysis entry!");
                }
                
                if(confirm("ATTENTION: This will save the entered information to the\n" +
                            "database, potentially overwriting previous settings.\n" +
                            "Are you sure you want to continue?")){
                    //$("#analysisEditor").submit();
                    submitAnalysis();
                                  
                } else{
                    return false;
                }
            },
           error: function(error){
                   
            }
        });
    }
                
    function submitAnalysis(){
        var name = $("[name='editName']").val();
        var status = $("[name='editStatus']").val();
        var tags = $("[name='editTags']").val();
        var question = $("[name='editQuestion']").val();
        var answer = $("[name='editAnswer']").val();
        var tree = $("[name='editTree']").val();
        
        $.ajax({
           url: $SCRIPT_ROOT + '/edit_analysis',
           data: { name:name, status:status, tags:tags,
                  question:question, answer:answer, tree:tree },
           type: 'GET',
           success: function(data){
               $("#analysisEditorModal").modal('hide')
               py_console_log(data.success);
               updateAnalysis();
               //updateTagOptions();
               //updateStatusOptions();
               $("#analysisSelector").val(name);
           },
           error: function(error){
               console.log(error)
           }
        });
    }

    $("#deleteAnalysis").on('click',deleteAnalysis);
    
    function deleteAnalysis(){
            
        var aSelected = $("#analysisSelector").val();
        reply = confirm("WARNING: This will delete the database entry for the selected " +
                "analysis. \n\n!!   THIS CANNOT BE UNDONE   !!\n\n" +
                "Are you sure you wish to delete this analysis:\n" +
                aSelected);
        
        if (reply){
            $.ajax({
                url: $SCRIPT_ROOT + '/delete_analysis',
                data: { aSelected:aSelected },
                
                // TODO: should use POST here? but was causing issues
                
                type: 'GET',
                success: function(data){
                    if (data.success){
                        py_console_log(aSelected + " successfully deleted.");
                        updateAnalysis();
                        //updateTagOptions();
                        //updateStatusOptions();
                    } else{
                        py_console_log("Something went wrong - unable to delete:\n" + aSelected);
                        return false;
                    }
                },
                error: function(error){
                    console.log(error);
                }
            });
        } else{
            return false;        
        }
    }
    
    
    
    ///////////////////////////////////////////////////////////////////////
    //     table selection, preview, strf, inspect                       //
    ///////////////////////////////////////////////////////////////////////
    
    
    
    $(document).on('click','.dataframe tr',function(){
        if ($(this).hasClass('selectedRow')){
            $(this).removeClass('selectedRow');
        } else{
            $(this).addClass('selectedRow');
        }
    });

    $(document).on('click','#preview',function(e){
        var cSelected = [];
        var mSelected = [];
        var bSelected = $("#batchSelector").val();
        
        $(".dataframe tr.selectedRow").each(function(){
            cSelected.push($(this).children().eq(0).html());
        });
        $(".dataframe tr.selectedRow").each(function(){
            mSelected.push($(this).children().eq(1).html());
        });

        // only proceed if selections have been made
        if ((cSelected.length == 0) || (mSelected.length == 0)){
            py_console_log('Must select at least one result from table')
            return false;
        }
        
        $.ajax({
            url: $SCRIPT_ROOT + '/get_preview',
            data: { cSelected:cSelected, mSelected:mSelected,
                   bSelected:bSelected },
            type: 'GET',
            success: function(data){
                // TODO: get this to open multiple windows. currently just
                // opens the first one then stops.
                //for (var i=0;i<data.filepaths.length;i++){
                //    window.open('preview' + data.filepaths[i],
                //                'width=520','height=910');
                //}
                $("#displayWrapper").empty();
                $("#displayWrapper").html(
                        '<img id="preview_image" src="data:image/png;base64,'
                        + data.image + '" />'
                        );
            },
            error: function(error){
                console.log(error);        
            }
        });
    });
                
    $("#clearSelected").on('click',function(){
        $(".dataframe tr.selectedRow").each(function(){
            $(this).removeClass('selectedRow');
        });
    });
                
    $("#strf").on('click',function(){
        py_console_log("STRF Function not yet implemented");
        //return strf plots ala narf_analysis
        //low priority
    });
                
                
                
                
    //////////////////////////////////////////////////////////////////////            
    //               Model fitting, inspect                             //
    //////////////////////////////////////////////////////////////////////
    
    
    
    function addLoad(){
        $('#loadingPopup').css('display', 'block');
    }
    function removeLoad(){
        $('#loadingPopup').css('display', 'none');
    }
    
    
    $("#fitSingle").on('click',function(){   
        var bSelected = $("#batchSelector").val();
        var cSelected = $("#cellSelector").val();
        var mSelected = $("#modelSelector").val();
        
        if ((bSelected === null) || (bSelected === undefined) || 
                (bSelected.length == 0)){
            py_console_log('Must select a batch')
            return false;
        }
        if ((cSelected.length > 1) || (mSelected.length > 1) || (cSelected.length
            == 0) || (mSelected.length == 0)){
            py_console_log('Must select one model and one cell')
            return false;
        }
        
        if (!(confirm(
                "Preparing to fit selection -- this may take several minutes."
              + "Web interface will be disabled until fit is complete."
              + "\n\nSelect OK to continue."))){
            return false;
        }
        // TODO: insert confirmation box here, with warning about waiting for
        //          fit job to finish
        
        addLoad();
                
        py_console_log("Sending fit request to server. Success or failure will be"
                    + "reported here when job is finished.")
        
        $.ajax({
            url: $SCRIPT_ROOT + '/fit_single_model',
            data: { bSelected:bSelected, cSelected:cSelected,
                       mSelected:mSelected },
            // TODO: should use POST maybe in this case?
            type: 'GET',
            timeout: 0,
            success: function(data){
                py_console_log("Fit finished.\n"
                      + "r_test: " + data.r_est + "\n"
                      + "r_val: " + data.r_val + "\n"
                      + "Click 'inspect' to browse model");
                
                updateResults();
                removeLoad();
                //open preview in new window like the preview button?
                //then would only have to pass file path
                //window.open('preview/' + data.preview,'width=520','height=910')
            },
            error: function(error){
                console.log("Fit failed");
                console.log(error);
                removeLoad();
            },
        });
    });
        
                
    $("#enqueue").on('click',function(){  
        var bSelected = $("#batchSelector").val();
        var cSelected = $("#cellSelector").val();
        var mSelected = $("#modelSelector").val();
        var queuelimit = $("#queuelimit").val();
                          
        if ((bSelected === null) || (bSelected === undefined) || 
                (bSelected.length == 0)){
            py_console_log('Must select a batch')
            return false;
        }
        if ((cSelected.length == 0) || (mSelected.length == 0)){
            py_console_log('Must select at least one model and at least one cell')
            return false;
        }
        
        if (queuelimit > 50){
            py_console_log("WARNING: Setting a queue limit higher than 50"
                           + "will likely result in a very long wait time."
                           + "Trying a smaller limit first is recommended.")
        }
        
        if (!(confirm("Continuing will queue a model fit for all combinations\n"
                      + "of selected models and cells. Until the background\n"
                      + "model queuer is implemented, all fits will run immediately.\n\n"
                      + "This may take a very long time. Are you sure you wish to continue?"))){
            return false;
        }
            
        addLoad();
        py_console_log("Sending fit request for each combination - please wait...");
                      
        $.ajax({
            url: $SCRIPT_ROOT + '/enqueue_models',
            data: { bSelected:bSelected, cSelected:cSelected,
                   mSelected:mSelected, queuelimit:queuelimit },
            // TODO: should POST be used in this case?
            type: 'GET',
            success: function(data){
                py_console_log(data.data);
                removeLoad();
            },
            error: function(error){
                console.log(error)   
                removeLoad();
            }
        });
        //communicates with daemon to queue model fitting for each selection on cluster,
        //using similar process as above but for multiple models and no
        //dialogue displayed afterward
        
        //open separate window/tab for additional specifications like priority?
    });
        
    $("#inspect").on('click',function(){
        //pull from results table
        var cSelected = [];
        var mSelected = [];
        var bSelected = $("#batchSelector").val();
        
        $(".dataframe tr.selectedRow").each(function(){
            cSelected.push($(this).children().eq(0).html());
            if (cSelected.length > 0){
                return false;
            }
        });
        $(".dataframe tr.selectedRow").each(function(){
            mSelected.push($(this).children().eq(1).html());
            if (mSelected.length > 0){
                return false;
            }
        });
 
        if ((cSelected.length === 0) || (mSelected.length === 0)){
            py_console_log("Must choose one cell and one model from the table.");
            return false;
        }
        
        var form = document.getElementById("modelpane");
        var batch = document.getElementById("p_batch");
        var cellid = document.getElementById("p_cellid");
        var modelname = document.getElementById("p_modelname");
        
        batch.value = bSelected;
        cellid.value = cSelected;
        modelname.value = mSelected;
        
        form.submit();
    });
        
    
    ////////////////////////////////////////////////////////////////////
    //////////////////////  PLOTS //////////////////////////////////////
    ////////////////////////////////////////////////////////////////////
        
    
    // from modelpane for reference
    $(".plotSelect").change(updatePlot);
    
    function updatePlot(){
        var plotDiv = $(this).parents(".row").find(".plot-wrapper");
        var modAffected = $(this).parents(".row").attr('id');
        var plotType = $(this).val();
        
        $.ajax({
            url: $SCRIPT_ROOT + '/update_modelpane_plot',
            data: { modAffected:modAffected, plotType:plotType },
            type: 'GET',
            success: function(data){
                plotDiv.html(data.html);
            },
            error: function(error){
                console.log(error);
            }
        });
        
    }
        
    $("#submitPlot").on('click', getNewPlot);
    
    function getNewPlot(){
        var plotDiv = $("#displayWrapper");
        
        var plotType = $("#plotTypeSelector").val();
        var bSelected = $("#batchSelector").val();
        var cSelected = $("#cellSelector").val();
        var mSelected = $("#modelSelector").val();
        var measure = $("#measureSelector").val();
        var onlyFair = $("#onlyFair").val();
        var includeOutliers = $("#includeOutliers").val();
        //TODO: add this
        //var useSNRorISO = $()
        
        addLoad();
        $.ajax({
            url: $SCRIPT_ROOT + '/generate_plot_html',
            data: { plotType:plotType, bSelected:bSelected, cSelected:cSelected,
                    mSelected:mSelected, measure:measure, onlyFair:onlyFair,
                    includeOutliers:includeOutliers },
            type: 'GET',
            success: function(data){
                plotDiv.empty();
                plotDiv.html(data.script + data.div);
                removeLoad();
            },
            error: function(error){
                console.log(error)
                removeLoad();
            }
        })
    }
});
        
