var sys = require("sys"),
    events = require("events"),
    CouchDB = require('./couchdb').CouchDB;
CouchDB.debug = false;

var debug = true;

var emitter = new events.EventEmitter();

var screens = [];

var christianImages = ['http://kiddmillennium.files.wordpress.com/2009/02/jesus-thumps-up1.jpg?w=400&h=400', 'http://scrapetv.com/News/News%20Pages/Entertainment/Images/jesus.jpg', 'http://www.morethings.com/god_and_country/jesus/children-jesus-170.gif', 'http://holyhell.files.wordpress.com/2009/02/jesus-christ-w-lamb.jpg', 'http://faithfool.files.wordpress.com/2007/07/white-jesus.jpg'];
var hinduismImages = ['http://www.indianchild.com/images/hindu_god_ram.jpg', 'http://momstinfoilhat.files.wordpress.com/2009/08/hindu-gods-kali.jpg', 'http://donyes.typepad.com/.a/6a00e554f2e0b988340120a4f85d81970b-800wi', 'http://www.moonbattery.com/archives/hindu-god.jpg', 'https://s3.amazonaws.com:443/cs-vannet/CommunityServer.Components.PostAttachments/00/00/00/16/43/stories+of+krishna+the+adventures+of+a+hindu+god+1.jpg?AWSAccessKeyId=0TTXDM86AJ1CB68A7P02&Expires=1274297361&Signature=7wQIrRGWbr%2bXqR%2b0RMjfwvqswl0%3d'];
var buddhismImages = ['http://thepopeofpentecost.files.wordpress.com/2010/02/buddhism.jpg', 'http://erinsaley.files.wordpress.com/2009/02/buddah1.jpg', 'http://religions.iloveindia.com/images/buddhism.jpg', 'http://sundaytimes.lk/070527/images/mumbai.jpg', 'http://1.bp.blogspot.com/_WUdmYiDgMdo/S1cTuCRvxuI/AAAAAAAAAQ0/AFJmfBSYlA8/s400/Buddhism.jpg'];

//var db = CouchDB.db('imagination', 'http://yorda.cs.northwestern.edu:5984');

// note: Use the IP address, not localhost. I was receiving a DNS error with localhost.
var db = CouchDB.db('imagination', 'http://127.0.0.1:5984');

var currIndices = {Christianity:1, Hinduism:1, Buddhism:1};

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

exports.run = function() {
	if (debug) sys.puts('screens.js - run()');

    for (var i = 0; i < 9; i++) {
        updateScreen(i);
    }
	setTimeout(runChristianity, 1000);
    setTimeout(runHinduism, 10000);
    setTimeout(runBuddhism, 20000);
}

/* ***** BEGIN REFACTORING ***** */

var categoryIndices = [];
categoryIndices['Christianity'] = 0;
categoryIndices['Hinduism'] = 0;
categoryIndices['Buddhism'] = 0;

exports.runNew = function() {
	setTimeout(function() { runCategory('Christianity', 0); }, 1000);
	setTimeout(function() { runCategory('Hinduism', 1); }, 11000);
	setTimeout(function() { runCategory('Buddhism', 2); }, 21000);
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

/* ***** END REFACTORING ***** */

function randElement(arr) {
    var index = Math.floor(Math.random() * arr.length);
    return arr[index];
}

/*function printObject(obj) {
    for (var k in obj) {
        sys.puts(k + "=>" + obj[k]);
    }
}*/

function handleCouchResult(result, column_index) {
    //I hope you like array math!
    try {
        result = result.rows[0].value;
    }
    catch(e) {
        return;
    }
	
    result.passage[result.selected_line] = '<span class="key">' + result.passage[result.selected_line] + '</span>';
    if (debug) sys.puts(result.passage[result.selected_line]);
	
    for (var i = 0; i < 9; i++) {
        var three_count = Math.floor(i / 3);
        var screen_index = three_count * 3 + column_index;
        var text_key = 'text' + (i % 3);
        screens[screen_index][text_key] = result.passage[i];
        if (!(i % 3)) { // only do this once per screen, no need to do 3 times
            screens[screen_index].image_url = 'stored_images/' + result.images[three_count];
            screens[screen_index].rippleDelay = 10000 * three_count;
        }
		if (i % 3 == 2) updateScreen(screen_index);
    }    
}

/*function nextChristian() {
	if (debug) sys.puts('screens.js - nextChristian()');
    db.view("religions/by_religion", {
        key: ['Christianity'],
        success: function(result){
			sys.puts('result.total_rows: ' + result.rows.length)
            if (currIndices.Christianity >= result.total_rows) {
                currIndices.Christianity = 0;
            }
            handleCouchResult(result, 0);
        }
    });
    currIndices.Christianity++;
}

function nextHinduism() {
	if (debug) sys.puts('screens.js - nextHinduism()');
    db.view("religions/religions", {
        key: ['Hinduism', currIndices.Hinduism],
        success: function(result){
			sys.puts('result.total_rows: ' + result.rows.length)
            if (currIndices.Hinduism >= result.total_rows) {
                currIndices.Hinduism = 0;
            }
            handleCouchResult(result, 1);
        }
    });
    currIndices.Hinduism++;
}

function nextBuddhism() {
	if (debug) sys.puts('screens.js - nextBuddhism()');
    db.view("religions/religions", {
        key: ['Buddhism', currIndices.Buddhism],
        success: function(result){
			sys.puts('result.total_rows: ' + result.rows.length)
            if (currIndices.Buddhism >= result.total_rows) {
                currIndices.Buddhism = 0;
            }
            handleCouchResult(result, 2);
        }
    });
    currIndices.Buddhism++;
}

function runChristianity() {
    setInterval(nextChristian, 50000);
    nextChristian();
}

function runHinduism() {
    setInterval(nextHinduism, 50000);
    nextHinduism();
}

function runBuddhism() {
    setInterval(nextBuddhism, 50000);
    nextBuddhism();
}*/
