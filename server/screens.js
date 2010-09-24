var sys = require("sys"),
    events = require("events"),
    CouchDB = require('./couchdb').CouchDB;
CouchDB.debug = false;

var debug = true;

var emitter = new events.EventEmitter();

var screens = [];

//var db = CouchDB.db('imagination', 'http://yorda.cs.northwestern.edu:5984');
// note: Use the IP address, not localhost. I was receiving a DNS error with localhost.
var db = CouchDB.db('imagination', 'http://127.0.0.1:5984');

/*var currIndices = {Christianity:1, Hinduism:1, Buddhism:1};*/

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

var categoryIndices = [];
categoryIndices['Christianity'] = 0;
categoryIndices['Hinduism'] = 0;
//categoryIndices['Buddhism'] = 0;
categoryIndices['Islam'] = 0;

exports.run = function() {
	setTimeout(function() { runCategory('Christianity', 0); }, 1000);
	setTimeout(function() { runCategory('Islam', 1); }, 11000);
	setTimeout(function() { runCategory('Hinduism', 2); }, 21000);
}

function runCategory(category, column) {
    setInterval(function() { nextCategory(category, column); }, 50000);
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
	
    //result.passage[result.selected_line] = '<span class="key">' + result.passage[result.selected_line] + '</span>';
    //if (debug) sys.puts(result.passage[result.selected_line]);
	
    for (var i = 0; i < 9; i++) {
        var three_count = Math.floor(i / 3);
        var screen_index = three_count * 3 + column_index;
        var text_key = 'text' + (i % 3);
        screens[screen_index][text_key] = result.passage[i];
        if (!(i % 3)) { // only do this once per screen, no need to do 3 times
            screens[screen_index].image_url = 'stored_images/' + result.images[three_count];
            screens[screen_index].rippleDelay = 0; //10000 * three_count;
        }
		if (i % 3 == 2) updateScreen(screen_index);
    }    
}
