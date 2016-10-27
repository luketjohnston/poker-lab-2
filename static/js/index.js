$( "#main-button" ).click(function() {
	$( "#main-button" ).hide();
	$( "#admin-input" ).fadeIn();
	$( "#admin-input" ).css("display", "flex");
});

$(document).click(function (e)
{
    var container = $( ".input" );

    container.each( function(index) {
		if($(container[index]).find( ".input__field" ).val().length !== 0) {
			$(container[index]).addClass( "input--filled" );
		} else {
			$(container[index]).removeClass( "input--filled" );
		}
	});
});

$( ".input" ).keyup(function (elem) 
{
	var inputs = $( ".input__field" );
	var filledInputs = $( ".input--filled" );
	if(inputs.length - 1 <= filledInputs.length) {
		$(" .next ").show();
	}
});

$( "#small-blind" ).keyup(function (e) 
{
	var value = parseInt($(e.currentTarget).val());
	if(isNaN(value)) {
		$( "#big-blind" ).val("");
	} else {
		$( "#big-blind" ).val(2*value);
	}
});

$( ".next" ).click(function (elem)
{
	$( "#admin-input" ).hide();
	$( "#session-input" ).css("display", "flex");
});

$( ".prev" ).click(function (elem)
{
	$( "#session-input" ).hide();
	$( "#admin-input" ).css("display", "flex");
});

$( ".number-input-field" ).keyup(function (e) {
	var value = parseInt($( "#max-buy-in" ).val());
	if(!isNaN(value)) {
		var inputs = $( ".number-input-field" );
		var valid_inputs = 0;
		inputs.each( function(index) {
			var cmp_val = parseInt($(inputs[index]).val());
			if(!isNaN(cmp_val) && cmp_val <= value){
				valid_inputs += 1;
			}
		});
		if(valid_inputs === 4) {
			$( "#max-buy-in" ).removeClass("danger-box")
			$( "#create-session" ).show()
		} else {
			$( "#max-buy-in" ).addClass("danger-box")
			$( "#create-session" ).hide()
		}
	}else{
		$( "#max-buy-in" ).addClass("danger-box")
		$( "#create-session" ).hide()
	}
});

$( "#create-session" ).click(function (e){
	window.location = "create-session/";
});


