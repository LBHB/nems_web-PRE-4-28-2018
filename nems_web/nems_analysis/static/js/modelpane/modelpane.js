$(document).ready(function(){

    function addLoad(){
        $('#loadingPopup').css('display', 'block');
    }
    function removeLoad(){
        $('#loadingPopup').css('display', 'none');
    }
    
    /*
    function resizeSVG(modRow){
        svg = $(this).find('.mpld3-figure');
        svg.attr('width','100%');
        svg.attr('height','100%');
        svg.attr('viewBox','0 0 1200 400');
        svg.attr('preserveAspectRatio','xMaxYMax');
    }

    $(".moduleRow").each(function(){
        resizeSVG($(this).parents(".row"));
    });
    */
    
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
                //resizeSVG(plotDiv.parents('.row'));
            },
            error: function(error){
                console.log(error);
            }
        });
        
    }
    
    $("#changeDataIdx").change(updateDataIdx);
    function updateDataIdx(){
        var plot_dataidx = $(this).val();
        addLoad();
        
        $.ajax({
            url: $SCRIPT_ROOT + '/update_data_idx',
            data: { plot_dataidx:plot_dataidx },
            type: 'GET',
            success: function(data){
                $(".plot-wrapper").each(function(i){
                    $(this).html(data.plots[i]);
                    //resizeSVG($(this).parents('.row'));
                });
                $("#stimIdxLabel").html("Stim Index 0 to " + data.stim_max);
                $("#changeStimIdx").val("0")
                removeLoad();
            },
            error: function(error){
                console.log(error);     
                removeLoad();
            }
        });
    }
                
    $("#changeStimIdx").change(updateStimIdx);
    function updateStimIdx(){
        var plot_stimidx = $(this).val();
        addLoad();
        
        $.ajax({
            url: $SCRIPT_ROOT + '/update_stim_idx',
            data: { plot_stimidx:plot_stimidx },
            type: 'GET',
            success: function(data){
                $(".plot-wrapper").each(function(i){
                    $(this).html(data.plots[i]);
                    //resizeSVG($(this).parents('.row'));
                });
                removeLoad();
            },
            error: function(error){
                console.log(error);
                removeLoad();
            }        
        })        
    }

    $(".submitModuleChanges").on('click', updateModule);
    function updateModule(){
        var modAffected = $(this).parents(".row").attr('id');
        var fields = [];
        var values = [];
        var types = [];
        var fieldValues = $(this).parents(".row")
        .find(".fieldValue").each(function(i){
            if ($(this).parents('.input-group').find('.check_box')
            .is(':checked')){
                fields.push($(this).attr('name'));
                values.push($(this).val());
                types.push($(this).attr('dtype'));
            }
            //fields_values[$(this).attr('name')] = $(this).val();
        });
        addLoad();
        
        $.ajax({
            url: $SCRIPT_ROOT + '/update_module',
            data: { fields:fields, values:values, types:types,
                   modAffected:modAffected },
            type: 'GET',
            success: function(data){
                var i = 0;
                $(".moduleRow").each(function(e){
                    var row = $(this);
                    if (parseInt(row.attr('name')) >= parseInt(data.modIdx)){
                        row.find('.plot-wrapper').html(data.plots[i]);
                        //resizeSVG(row);
                        $.each(data.fields[i], function(j){
                            var field = data.fields[i][j];
                            row.find("input[name='" + field + "']")
                            .val(data.values[i][j])
                            .attr('dtype', data.types[i][j])
                        });
                    i++;
                    }
                })
                removeLoad();
            },
            failure: function(error){
                console.log(error);
                removeLoad();
            }
        })

    }


    // Not used //
    /*
    $(".selectPreset").change(updatePresets);
    function updatePresets(){
        var modAffected = $(this).parents(".row").attr('id');
        var kSelected = $(this).val();
        var parentDiv = $(this).parents(".control-group");
        
        $.ajax({
            url: $SCRIPT_ROOT + '/get_kw_defaults',
            data: { modAffected:modAffected, kSelected:kSelected },
            type: 'GET',
            success: function(data){
                kwdict = eval(data);
                for (var key in kwdict){
                    console.log("kwdict key: " + kwdict[key]);
                    console.log("just the key: " + key);
                    if (key.length == 0){
                        continue;        
                    }
                    field = parentDiv.find(
                            ".input-finder:contains(" + key + ")"
                            ).children("input");
                    field.val(kwdict[key]);
                }
            },
            error: function(error){
                console.log(error);        
            }
        });
            
    }
    */
    
});