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