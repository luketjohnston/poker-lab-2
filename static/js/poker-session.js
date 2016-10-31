window.setInterval(function(){
  retrieveGamestate();
}, 5000);

function retrieveGamestate() {
	var target = "retrieve-gamestate/";
	$.ajax({
		url: target,
		type: "GET",
		success: function(data) {
            updateDisplay(data);
        }
	});
}

function isValidNumber(char) {
	return char >= 48 && char <= 57;
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
					if(pokerTable.has("#bet-info-" + visIdx).length !== 0) {
						pokerTable.find("#bet-info-" + visIdx).remove();
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

function createCardDiv(cardObj) {
	var imgLocation = '/static/img/' + cardObj[1] + '.png';
	var classes = 'card ' + cardObj[1];
	var suitImg = $('<img/>', {
		class: 'suit-icon',
		src: imgLocation
	});
	var suitImg2 = $('<img/>', {
		class: 'suit-icon',
		src: imgLocation
	});
	var topLeft = $('<div/>', {
		class: 'top-left-corner'
	});
	var bottomRight = $('<div/>', {
		class: 'bottom-right-corner'
	});
	suitImg.appendTo(topLeft);
	suitImg2.appendTo(bottomRight);
	var cardTitle = $('<div/>', {
		class: 'card-title',
		text: cardObj[0]
	});
	var card = $('<div/>', {
		class: classes
	});
	topLeft.appendTo(card);
	bottomRight.appendTo(card);
	cardTitle.appendTo(card);
	return card;
}


function updateDisplay(results) {
	// Get the seat number of the player running this instance
	var playerSeatNum = parseInt($( "#seat-number" ).attr("data"));
	var pokerTable = $( ".poker-table" );
	// Update info regarding seat occupation, player stacks,
	// and bets
	updateSeatInfo(results, playerSeatNum, pokerTable);

	// Update the board cards
	var boardCards = pokerTable.find('.card');
	for(var i=boardCards.length; i < results.board.length; i++) {
		var card = createCardDiv(results.board[i]);
		card.appendTo(pokerTable.find('.card-row'));
	}
	// Update this player's hole cards
	var holeCardsRow = $( "#hole-cards-row" );
	var holeCards = holeCardsRow.find('.card');
	for(var i=holeCards.length; i < results.hole_cards.length; i++) {
		var card = createCardDiv(results.hole_cards[i]);
		card.appendTo(holeCardsRow);
	}
	// Update this player's dash information
	var stackString = results['stacks'][playerSeatNum];
	if(stackString >= 1000){
		stackString = stackString.toFixed(0);
	} else {
		stackString = stackString.toFixed(2);
	}
	$( '.dash-stack' ).text(stackString);
	// Update pot
	if(results.hasOwnProperty('total_pot')) {
		$( '.dash-pot' ).text(results.total_pot);
	} else {
		$( '.dash-pot' ).text('--');
	}
	// Update action buttons
	var buttonColumn = $( '.button-col' );
	// This check is used to determine if there is
	// actually a hand in progress, if so, we can
	// access the dictionaries we need in results

	if(results.hasOwnProperty('can_bet')) {
		
		// Check if this player can bet
		if(results.can_bet[playerSeatNum]) {
			// If can bet, then remove the raise,
			// call, and all-in button if they're there
			if($('#call-button').length !== 0) {
				$('#call-button').remove();
			}
			if($('#raise-button-container').length !== 0) {
				$('#raise-button-container').remove();
			}
			if($('#all-in-button').length !== 0) {
				$('#all-in-button').remove();
			}

			// If player can bet, it can check
			if($('#check-button').length === 0) {
				$('<div/>', {
					class: 'dash-button',
					id: 'check-button',
					onclick: 'check()',
					text: 'Check'
				}).appendTo(buttonColumn);
			}
			// If there's no bet button, add one
			if($( '#bet-button' ).length === 0) {
				var input = $('<input/>', {
					class: 'button-text-input',
					id: 'bet-input',
					onkeypress: 'isValidNumber(event.charCode)'
				});
				var betButton = $('<div/>', {
					class: 'inner-button',
					id: 'bet-button',
					onclick: 'bet()',
					text: 'Bet'
				});
				var buttonContainer = $('<div/>', {
					class: 'dash-button button-input-container',
					id: 'bet-button-container'
				});
				input.appendTo(buttonContainer);
				betButton.appendTo(buttonContainer);
				buttonContainer.appendTo(buttonColumn);
			}
		} else {
			// If player cannot bet
			// remove bet button and check button
			// if they are there
			if($('#check-button').length !== 0) {
				$('#check-button').remove();
			}
			if($('#bet-button-container').length !== 0) {
				$('#bet-button-container').remove();
			}

			// Check if player can call
			if(results.can_call[playerSeatNum]) {
				if($( '#call-button' ).length === 0) {
					$('<div/>', {
						class: 'dash-button',
						id: 'call-button',
						onclick: 'call()',
						text: 'Call'
					}).appendTo(buttonColumn);
				}
				// The player can only possibly raise if he/she
				// also can call
				if(results.can_raise[playerSeatNum]) {
					// If player can raise, check if the all-in
					// button is there, remove it if so
					if($( '#all-in-button' ).length !== 0) {
						$( '#all-in-button' ).remove();
					}
					// If there's no raise button, add one
					if($( '#raise-button' ).length === 0) {
						var input = $('<input/>', {
							class: 'button-text-input',
							id: 'raise-input',
							onkeypress: 'isValidNumber(event.charCode)'
						});
						var raiseButton = $('<div/>', {
							class: 'inner-button',
							id: 'raise-button',
							onclick: 'raise()',
							text: 'Raise'
						});
						var buttonContainer = $('<div/>', {
							class: 'dash-button button-input-container',
							id: 'raise-button-container'
						});
						input.appendTo(buttonContainer);
						raiseButton.appendTo(buttonContainer);
						buttonContainer.appendTo(buttonColumn);
					}
				} else {
					// If player can't raise, and raise button
					// is present, remove it
					if($( '#raise-button' ).length !== 0) {
						$( '#raise-button' ).remove();
					}
					// If player can't raise but can call,
					// the player can go all in
					if($( '#all-in-button' ).length === 0) {
						$('<div/>', {
							class: 'dash-button',
							id: 'all-in-button',
							onclick: 'allIn()'

						}).appendTo(buttonColumn);
					}
				}

			} else {
				// If player cannot call
				// remove the call button if it's there
				if($( '#call-button' ).length !== 0) {
					$( '#call-button' ).remove();
				}
			}
		}
		// The player can always fold during hand
		$( '#fold-button' ).remove();
		$('<div/>', {
			class: 'dash-button',
			id: 'fold-button',
			onclick: 'fold()',
			text: 'Fold'
		}).appendTo(buttonColumn);

		// if action is on this player, remove
		// the disabled class from the action buttons
		// otherwise add it
		if(results.seat_to_act === playerSeatNum) {
			$( '.dash-button' ).removeClass('disabled');
			$( '.inner-button' ).removeClass('disabled');
			$( '.button-text-input' ).removeClass('disabled');
			$( '.button-text-input' ).prop('disabled', false);
			$( '.player-dash' ).addClass('action-on');
		} else {
			$( '.dash-button' ).addClass('disabled');
			$( '.inner-button' ).addClass('disabled');
			$( '.button-text-input' ).addClass('disabled');
			$( '.button-text-input' ).prop('disabled', true);
			$( '.player-dash' ).removeClass('action-on');
		}
	} else {
		// if hand is not in session, remove
		// all action buttons
		if($('.dash-button')) {
			$('.dash-button').remove();
		}
	}
}


function dealHand() {
	var pathname = window.location.pathname;
	var pathParts = pathname.split( '/' );
	var sessionID = pathParts[1];
	var target = "/" + sessionID + "/deal-hand/";
	$.ajax({
		url: target,
		type: "POST"
	});
	$( '.start-button' ).hide();
}


function check() {
	$.ajax({
		url: "check/",
		type: "POST"
	});
}


function bet() {
	var betAmount = parseFloat($( '#bet-input' ).val());
	var stackAmount = parseFloat($( '.dash-stack' ).text());
	console.log('Bet: ' + betAmount);
	console.log('Stack: ' + stackAmount);
	if(betAmount <= stackAmount) {
		console.log('Good bet: ' + betAmount);
		var betUrl = betAmount + '/bet/';
		$.ajax({
			url: betUrl,
			type: "POST"
		});
	} else {
		console.log('Bad bet: ' + betAmount);
	}
}


function call() {
	$.ajax({
		url: "call/",
		type: "POST"
	});
}


function raise() {
	var raiseAmount = parseFloat($( '#raise-input' ).val());
	var stackAmount = parseFloat($( '.dash-stack' ).text());
	console.log('Raise: ' + raiseAmount);
	console.log('Stack: ' + stackAmount);
	if(raiseAmount <= stackAmount) {
		console.log('Good raise: ' + raiseAmount);
		var betUrl = raiseAmount + '/raise/';
		$.ajax({
			url: betUrl,
			type: "POST"
		});
	} else {
		console.log('Bad raise: ' + betAmount);
	}
}

function allIn() {
	$.ajax({
		url: "all-in/",
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