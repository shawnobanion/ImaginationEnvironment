var sys = require("sys"),
    events = require("events"),
    CouchDB = require('./couchdb').CouchDB;

CouchDB.debug = false;
var debug = true;
var emitter = new events.EventEmitter();
var screens = [];

//var db = CouchDB.db('imagination', 'http://yorda.cs.northwestern.edu:5984');
// note: Use the IP address, not localhost. I was receiving a DNS error with localhost.
var db = CouchDB.db('illumination', 'http://127.0.0.1:5984');

exports.get_screen_emitter = function () {return emitter};

/*Creates an array of 9 screens*/
exports.setup = function() {
    for (var i = 0; i < 9; i++) {
        var screen_ = {};
        screen_.id = i;
        screen_.image_url = 'http://infolab.northwestern.edu/media/uploaded_images/featured_illumination.jpg';
        screen_.text0 = 'Welcome to';
        screen_.text1 = 'the';
        screen_.text2 = 'Imagination Environment';
        screens.push(screen_);
    }    
}

function updateScreen(screen_index) {
	if (debug) sys.puts('screens.js - updateScreen() - screen_index = ' + screen_index);
    emitter.emit('screen', screens[screen_index]);
}

function bulkUpdate() {
	if (debug) sys.puts('screens.js - bulkUpdate()');
	emitter.emit('screen', screens);
}

var categoryIndices = [];
categoryIndices['Christianity'] = 0;
categoryIndices['Hinduism'] = 0;
//categoryIndices['Buddhism'] = 0;
categoryIndices['Islam'] = 0;

exports.run = function() {
	setTimeout(function() { runCategory('Christianity', 0); }, 1000);
	//setTimeout(function() { runCategory('Islam', 1); }, 11000);
	//setTimeout(function() { runCategory('Hinduism', 2); }, 21000);
}

function runCategory(category, column) {
    setInterval(function() { nextCategory(category, column); }, 40000);
    nextCategory(category, column);
}

function nextCategory(category, column)
{
    db.view("religions/religions", {
        key: [category, categoryIndices[category]],
        success: function(result){
			if (result.rows.length == 0) // no results returned, we must have reached our max. start over.
			{
				categoryIndices[category] = 0;
				nextCategory(category, column);
			}
			else
			{
				handleCouchResult(result, column);
			}
        }
    });
	categoryIndices[category]++;
}

function randElement(arr) {
    var index = Math.floor(Math.random() * arr.length);
    return arr[index];
}

function handleCouchResult(result, column_index) {
    //I hope you like array math!
    try {
        result = result.rows[0].value;
    }
    catch(e) {
        return;
    }

	// remove search terms from common words
	common_words = result.common_words.sort(sortByStringLen);
	highlight_words = result.image_search_terms.sort(sortByStringLen);
	for (h = 0; h < highlight_words.length; h++) {
		var index_of = common_words.indexOf(highlight_words[h]);
		if (index_of != -1) {
			common_words.splice(index_of, 1);
		}
	}
		
	// highlight common words
	for (var p = 0; p < result.passages.length; p++){	
		var passage = result.passages[p];
		for (var x = 0; x < common_words.length; x++){
			var word = common_words[x];
			var regex = new RegExp('\\b' + word + '\\b', 'ig');
			for (y = 0; y < passage.length; y++){
				
				passage[y] = passage[y].replace(regex, '<span class="key">' + word + '</span>');
			}
		}
	}
	
	sys.puts('passage num: ' + result.passage_num);
	sys.puts('common words: ' + common_words);
	sys.puts('search term words: ' + highlight_words);
	
	// setup and update screens (in order of column)
	var keyword_regex = new RegExp('\\b' + result.image_search_term + '\\b', 'ig');
	var NUM_COLUMNS = result.passages.length;
	var LINES_PER_SCREEN = 3;
	var i = 0;
	for (column_index = 0; column_index < NUM_COLUMNS; column_index++){
		for (screen_index = column_index; screen_index < (NUM_COLUMNS * NUM_COLUMNS); screen_index += 3) {
			
			// ensure the first passage is setup in the middle column
			var passage_index = column_index - 1;
			if (passage_index < 0) passage_index = NUM_COLUMNS - 1;
			var passage = result.passages[passage_index];
			
			// setup the passage text
			for (text_index = 0; text_index < LINES_PER_SCREEN; text_index++){
				var text_key = 'text' + text_index;
				var passage_line_index = (Math.floor(screen_index / NUM_COLUMNS) * NUM_COLUMNS) + text_index;
				
				// highlight image search terms
				passage_line_text = passage[passage_line_index];
				if (passage_line_text) {
					for (h = 0; h < highlight_words.length; h++){
						var regex = new RegExp('\\b' + highlight_words[h] + '\\b', 'ig');
						passage_line_text = passage_line_text.replace(regex, '<span class="search_key">' + highlight_words[h] + '</span>');
					}
					screens[screen_index][text_key] = passage_line_text;
				}
			}
			
			// setup the images
			screens[screen_index].image_url = 'stored_images/' + result.images[i];
			screens[screen_index].rippleDelay = Math.floor(screen_index / NUM_COLUMNS) * 12000; // 10000;
			i++;
		}
	}
	
	bulkUpdate();
}

function sortByStringLen(a, b){
	return b.length - a.length;
}
