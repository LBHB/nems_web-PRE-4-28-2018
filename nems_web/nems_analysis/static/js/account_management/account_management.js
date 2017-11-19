$(document).ready(function(){


    //    old js/modal way commented out, using wtf forms in python    
    /*
    $("#logIn").on('click', function(){
        
        var user = $("#user").val();
        var pswd = $("#pswd").val();

        $.ajax({
            url: $SCRIPT_ROOT + '/log_in_test',
            data: { user:user, pswd:pswd },
            type: 'GET',
            success: function(data){
                if (data.success){
                    $('#logIn').css('display', 'none');
                    $('#logOut').css('display', 'block');
                    $('#userName').css('display', 'block');
                    $('#userName').html(data.user);
                    py_console_log('success');
                } else{
                    // log an error message returned from python?
                    py_console_log('error logging in')
                }
            },
            error: function(error){
                console.log(error);
            }
        });
    });
    */

    /*
    $("#logout").on('click', function(){
        $.ajax({
            url: $SCRIPT_ROOT + '/logout',
            type: 'GET',
            success: function(data){
                if (data.success){
                    $('#logOut').css('display', 'none');
                    $('#userName').css('display', 'none');
                    $('#userName').html('');
                    $('#logIn').css('display', 'block');
                    py_console_log('success');
                } else{
                    // log an error message returned from python?
                    py_console_log('error logging out')
                }
            },
            error: function(error){
                console.log(error);
            }
        });
    });
    */

    /*
    var user_avail = false;
    $("#reg_user").change(function(){
        var user = $("#reg_user").val();
        $.ajax({
            url: $SCRIPT_ROOT + '/check_username',
            data: { user:user },
            type: 'GET',
            success: function(data){
                if (data.available){
                    user_avail = true;
                } else{
                    user_avail = false;
                }
                check_register_okay();
            },
            error: function(error){
                console.log(error);
                check_register_okay();
            }
        });
    });
    */

    /*
    var pswd_match = false;
    $("#reg_pswd, #reg_pswdTwo").change(function(){
        var pswd = $("#reg_pswd").val();
        var pswdTwo = $("#reg_pswdTwo").val();
        if (pswd === pswdTwo){
            pswd_match = true;
        } else{
            pswd_match = false;
        }
        check_register_okay();
    });
    */

    /*
    function check_register_okay(){
        if (user_avail && pswd_match){
            $("#register").prop("disabled", false);
        } else{
            $("#register").prop("disabled", true);
        }
    }
    */

    /*
    $("#register").on('click', function(){
        var user = $("#reg_user").val();
        var pswd = $("#reg_pswd").val();
        var firstname = $("#reg_firstname").val();
        var lastname = $("#reg_lastname").val();
        //var email = $("#reg_email").val();

        if (!user_avail){
            // make separate message area for registration modal?
            // i.e. instead of using py_console, which might not be visible
            py_console_log('Username already exists');
            return false;
        }

        if (!pswd_match){
            py_console_log('Passwords must match');
            return false;
        }

        $.ajax({
            url: $SCRIPT_ROOT + '/register',
            data: { user:user, pswd:pswd, firstname:firstname,
                    lastname:lastname },
            type: 'GET',
            success: function(data){
                if (data.success){
                    py_console_log("Registration successful");
                } else{
                    py_console_log("Registration failed");
                }
            },
            error: function(error){
                console.log(error);
            }
        });
    });
    */
});