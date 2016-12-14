$( "#main-button" ).click(function() {
	$( "#main-button" ).hide();
	$( "#admin-input" ).fadeIn();
	$( "#admin-input" ).css("display", "flex");
});

// // Support TLS-specific URLs, when appropriate.
// if (window.location.protocol == "https:") {
//   var ws_scheme = "wss://";
// } else {
//   var ws_scheme = "ws://"
// };

// var inbox = new ReconnectingWebSocket(ws_scheme + location.host + "/receive");
// var outbox = new ReconnectingWebSocket(ws_scheme + location.host + "/submit");

// inbox.onmessage = function(message) {
//   var data = JSON.parse(message.data);
//   $("#chat-text").append("<div class='panel panel-default'><div class='panel-heading'>" + $('<span/>').text(data.handle).html() + "</div><div class='panel-body'>" + $('<span/>').text(data.text).html() + "</div></div>");
//   $("#chat-text").stop().animate({
//     scrollTop: $('#chat-text')[0].scrollHeight
//   }, 800);
// };

// $("#input-form").on("submit", function(event) {
//   event.preventDefault();
//   var handle = $("#input-handle")[0].value;
//   var text   = $("#input-text")[0].value;
//   outbox.send(JSON.stringify({ handle: handle, text: text }));
//   $("#input-text")[0].value = "";
// });

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


