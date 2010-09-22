var filenames = ['buddah.json', 'quran.json', 'vedas.json', 'bible.json'];

function display_codes(){
	var chars = [];
	$.each(filenames, function(i, filename){	
		$.getJSON(filename, function(data) {
			$.each(data, function(i, item){
				$.each(item.verses, function(z, verse)
				{
					var pattern = '&#[0-9]+;';
					var re = new RegExp(pattern);
					matches = verse.match(re);
					if (matches)
					{
						$.each(matches, function(x, m){
							if ($.inArray(m, chars) == -1){
								chars.push(m);
							}
						});
					}
				});
			});
		});
	});
	$.each(chars.sort(), function(i, c){
		var num = c.substr(2, c.indexOf(';') - 2);
		$('#result').append('<tr><td>' + num + '</td><td>' + c + '</td></tr>');
	});
}