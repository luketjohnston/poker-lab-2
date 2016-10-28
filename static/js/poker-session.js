window.setInterval(function(){
  retrieveGamestate();
}, 5000);

function retrieveGamestate() {
	var pathname = window.location.pathname;
	var pathParts = pathname.split( '/' );
	var sessionID = pathParts[1];
	var target = "/" + sessionID + "/retrieve-gamestate/";
	$.ajax({
		url: target,
		type: "GET",
		success: function(data) {
            updateDisplay(data);
        }
	});
}

function mod(n, m) {
        return ((n % m) + m) % m;
}

function updateSeatInfo(results, playerSeatNum, pokerTable) {
	for(var i = 1; i <= 10; i++) {
		// This is the "visual index" of a certain player
		// given their position relative to this player
		var visIdx = mod(i - playerSeatNum, 10);
		if(visIdx != 0) {
			var seat = $( "#seat-"+visIdx );
			// If that seat is filled
			if(results.filled_seats[i]) {
				// and has not already been marked occupied
				if(! seat.hasClass("occupied")) {
					// Mark it as occupied
					seat.addClass("occupied");
					// Create new divs to hold player info
					// seat title
					$('<div/>', {
						class: 'seat-title',
						text: results.usernames[i][0]
					}).appendTo(seat);
					// player byline
					$('<div/>', {
						class: "player-byline",
						id: "byline-" + visIdx
					}).appendTo(seat);
					var byline = $( "#byline-" + visIdx );
					// user name
					$('<div/>', {
						text: results.usernames[i]
					}).appendTo(byline);
					// byline hr
					$('<hr/>', {
						class: 'seat-info-line',
						id: 'line-' + visIdx,
					}).appendTo(byline);
					var stackString = results['stacks'][i];
					if(stackString > 1000){
						stackString = stackString.toFixed(0);
					} else {
						stackString = stackString.toFixed(2);
					}
					// stack info
                	$('<div/>', {
                		class: 'seat-stack',
                		text: stackString
                	}).appendTo(byline);
				} else {
					// if the seat is already occupied, we can
					// assume the necessary divs are present, and
					// update those divs with new information
					var stackString = results['stacks'][i];
					if(stackString >= 1000){
						stackString = stackString.toFixed(0);
					} else {
						stackString = stackString.toFixed(2);
					}
					// Update stack for this player
					seat.find(".seat-stack").text(stackString);
					// Update dealer chip
					if(results.button_seat == i) {
						// if this seat is the button and doesn't
						// have chip, add it
						if(seat.has(".dealer-chip").length === 0) {
							console.log('does not have chip')
							$('<div/>', {
								class: 'dealer-chip'
							}).appendTo(seat);
							var chip = $( ".dealer-chip" );
							$('<div/>', {
								class: 'chip-text',
								text: 'D'
							}).appendTo(chip);
						}
					} else {
						// if this seat is not the button
						// check if it has the dealer chip and remove it
						if(seat.has(".dealer-chip").length !== 0) {
							seat.find(".dealer-chip").remove();
						}
					}
					// Update action on
					if(seat.hasClass("action-on")) {
						// If seat has class action on
						// check and make sure it still should
						if(results.seat_to_act !== i) {
							// action is no longer on this seat
							// so remove class
							seat.removeClass("action-on");
						}
					} else {
						// If action is on this seat, add class
						if(results.seat_to_act === i) {
							// action is no longer on this seat
							// so remove class
							seat.addClass("action-on");
						} 
					}
				}
			}
			// update bets
			// first check if there are any bets
			if(results.hasOwnProperty('current_bets')) {
				// if there are bets, check if this player has a bet
				if(results.current_bets[i] > 0) {
					var betString = results.current_bets[i];
					if(betString >= 1000){
						betString = betString.toFixed(0);
					} else {
						betString = betString.toFixed(2);
					}
					// if this player has a bet, check if there
					// is a bet at this seat
					var betInfo = $("#bet-info-" + visIdx);
					
					// if there is no bet displayed, add it
					if(betInfo.length === 0) {
						$('<div/>', {
							class: 'bet-info',
							id: 'bet-info-' + visIdx
						}).appendTo(pokerTable);
						betInfo = $("#bet-info-" + visIdx);
						$('<img/>', {
							src: '/static/img/bet-icon.png',
							style: 'height: 25px;'
						}).appendTo(betInfo);
						$('<div/>', {
							class: 'bet-num',
							text: betString
						}).appendTo(betInfo);

					} else {
						// if there is a bet displayed, update it
						betInfo.find('.bet-num').text(betString);
					}
				} else {
					// if this player doesn't have a bet, check
					// if this seat has a bet on the table and
					// remove it
					if(seat.has(".bet-info") !== 0) {
						seat.find(".bet-info").remove();
					}
				}
			} else {
				// if there aren't any bets (because a hand
				// hasn't started), remove bets on table
				$( ".bet-info" ).remove();
			}
		}
	}
}

function updateDisplay(results) {
	// Get the seat number of the player running this instance
	var playerSeatNum = $( "#seat-number" ).attr("data")
	var pokerTable = $( ".poker-table" );
	updateSeatInfo(results, playerSeatNum, pokerTable);

	var boardCards = pokerTable.find('.card');
	for(i=boardCards.length; i < results.board.length; i++) {
		
	}
}



function dealHand() {
	var pathname = window.location.pathname;
	var pathParts = pathname.split( '/' );
	var sessionID = pathParts[1];
	var target = "/" + sessionID + "/deal-hand/";
	console.log(target);
	console.log(pathname);
	$.ajax({
		url: target,
		type: "POST"
	});
}

function call() {
	$.ajax({
		url: "call/",
		type: "POST"
	});
}

function fold() {
	$.ajax({
		url: "fold/",
		type: "POST"
	});
}

function addPlayer(seat_num) {
	swal.withForm({   
		title: "Add another player!", 
		text: 'Type in their email below:',
		confirmButtonColor: '#7EBDC2',
		showCancelButton: true,   
		closeOnConfirm: false,   
		showLoaderOnConfirm: true, 
		html: true,
		formFields: [
			{ id: 'name', placeholder: 'myfriend@email.com' },
		]
	}, 
	function(isConfirm) {
		if (isConfirm) {
			email = this.swalForm.name;
			$.ajax({
				url : "add-player/",
				type: "POST",
				data : JSON.stringify({email:email, seat_num:seat_num}, null, '\t'),
				contentType: 'application/json;charset=UTF-8',
			});
			setTimeout(function(){ 
				swal({
					title: "Invite sent to " + email + "!",
					text: "They will be added once they click the link sent to them.",
					type: "success",
					confirmButtonColor: '#7EBDC2',
				},
				function() {
					// location.replace("/booker/profile/?tab=group");
				});   
    		}, 2000);
		}
	});
}