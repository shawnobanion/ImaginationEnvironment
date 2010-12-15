var socket = null;
var isSingleScreen = false;
var singleScreenId = -1;

$(function(foo) {
	setupControls();
	var id = getQueryStringParameter('id');
	if (id != '') {
		setupSingleScreen(id);
		hideControls();
	} 
	else {
		setupGrid();
	}
});

function animateScreens() {
	console.log('animating screens');
	
	$('.screen .text').css('color', '#FFF');
	$('.screen').delay(12000).animate({opacity: "1"}, 1000);
	
	var initialDelay = 18000;
	
	setTimeout('fadeTextColor()', initialDelay);
	setTimeout('highlightKeys()', initialDelay);
	//setTimeout('highlightSearchKeys()', initialDelay + 5000);
	//setTimeout('fadeKeysColor()', initialDelay + 10000);
	setTimeout('displayScreenImages()', initialDelay + 10000);
	setTimeout('hideText()', initialDelay + 14000);
}

function hideText() {
	console.log('hiding text');
	$(".screen").animate({opacity: '0'}, 2000);
}

function highlightKeys() {
	console.log('highlight keys');
	//$('.screen .text .key').animate({color: '#f7da15'}, 2000);
	$('.screen .text .search_key').animate({color: '#f7da15'}, 2000);
}
/*
function highlightSearchKeys() {
	console.log('highlighting search keys');
	$(".screen .text .search_key").animate({color: '#FFF'}, 2000);
}
*/
function fadeTextColor() {
	console.log('fading text color');
	$(".screen .text").animate({color: '#343434'}, 2000);
}
/*
function fadeKeysColor() {
	console.log('fading keys color');
	$(".screen .text .key").animate({color: '#343434'}, 2000);
}
*/

function displayScreenImages() {
	console.log('displaying images');
	$(".screenbkgd").each(function(i, obj) {
		$(obj).css('background-image', 'url("' + $(obj).attr('rel') + '")').attr('rel', '').animate({opacity: '1'}, 2000);
	});
	//$(".screen .text .search_key").animate({color: '#000'}, 2000);
}

function onBulkUpdate(data) {
	
	$(".screenbkgd").animate({opacity: "0"}, 1000);
	
	var data = JSON.parse(data);
	
	var centerColumnText = '';
	for (var id = 0; id < data.length; id++) {
		if (id % 3 == 1) {
			centerColumnText += '<div class="text">' + data[id]['text0'] + "</div>";
			centerColumnText += '<div class="text">' + data[id]['text1'] + "</div>";
			centerColumnText += '<div class="text">' + data[id]['text2'] + "</div>";
		}
		var screen_ = $('#screen-' + id).first();
		var screenbkgd_ = $('#screenbkgd-' + id).first();
		if (screen_.length) {		
			console.log('updating screen id: ' + id);
			if (id % 3 != 1) {
				$('.text:eq(0)', screen_).html(data[id]['text0']);
				$('.text:eq(1)', screen_).html(data[id]['text1']);
				$('.text:eq(2)', screen_).html(data[id]['text2']);
			}
			screenbkgd_.attr('rel', data[id]['image_url']);
		}
	}
	
	// setup middle column
	for (var id = 1; id < data.length; id += 3) {
		if ((isSingleScreen && singleScreenId == id) || (!isSingleScreen && id == 7)) {
			var screen_ = $('#screen-' + id).first();
			var animTopFactor = ((-1 * (Math.floor(id / 3))) + 2);
			var animTop = getScreenHeight() * animTopFactor;
			console.log('animating top factor: ' + animTopFactor);
			console.log('animating screen #' + id + ' to -' + animTop + 'px');
			console.log('center column text: ' + centerColumnText);
			screen_.css('top', getScreenPositionTop(id)).css('position', 'absolute').css('opacity', 1).html(centerColumnText).animate({"top": "-" + animTop + "px"}, 10000);
		}
	}

	animateScreens();
}

function resetSocket() {
    if (socket) {
		console.log('disconnecting socket');
        socket.disconnect();
        socket = null;
    }
	
	console.log('creating new socket and connecting');
	var server = '165.124.115.144';
    socket = new io.Socket(server, {rememberTransport: false, port: 8080});
    socket.connect();
    socket.addEvent('message', onBulkUpdate);
}

function htmlForScreen(class_, id, top, left) {
    var ret = '<div class="' + class_ + ' screen" id="screen-' + id + '" style="top: ' + top + 'px; left: ' + left + 'px;">';
    console.log("creating html for screen #" + id);
    ret += '<div class="text"></div>';
    ret += '<div class="text"></div>';
    ret += '<div class="text"></div>';
    ret += '</div>';
    return ret
}

function htmlForScreenBkgd(class_, id, top, left) {
	var ret = '<div class="' + class_ + ' screenbkgd" id="screenbkgd-' + id + '" style="top: ' + top + 'px; left: ' + left + 'px;"></div>';
    console.log("creating html for screenbkdg #" + id);
    return ret
}

function getScreenHeight() {
	if (isSingleScreen) {
		return self.innerHeight;
	}
	return 231;
}

function getScreenPositionTop(id) {
	if (id % 3 == 1) {
		if (isSingleScreen)
			return getScreenHeight();
		return (Math.floor(id / 3) + 1) * getScreenHeight();
	}
	return Math.floor(id / 3) * getScreenHeight();
}

function getScreenPositionLeft(id) {
	return (id % 3) * 330;
}

function getScreenBkgdPositionTop(id) {
	return Math.floor(id / 3) * getScreenHeight();
}

function getScreenBkgdPositionLeft(id) {
	return (id % 3) * 330;
}


function setupSingleScreen(id) {
	isSingleScreen = true;
	singleScreenId = id;
	resetSocket();
	$('.title').text('Showing screen ' + (id));
	$('.container').empty();
	$('#bkgdContainer').empty();
	$('.container').append(htmlForScreen('single', id, getScreenPositionTop(id), 0));
	$('#bkgdContainer').append(htmlForScreenBkgd('single', id, 0, 0));
}

function setupGrid() {
	isSingleScreen = false;
	singleScreenId = -1;
	resetSocket();
	$('.title').text("Showing all nine screens");
	$('#bkgdContainer').empty();
	$('.container').empty().css('width', '990px').css('height', '690px');
	for (var screen_id = 0; screen_id < 9; screen_id++) {
		$('.container').append(htmlForScreen('grid', screen_id, getScreenPositionTop(screen_id), getScreenPositionLeft(screen_id)));
		$('#bkgdContainer').append(htmlForScreenBkgd('grid', screen_id, getScreenBkgdPositionTop(screen_id), getScreenBkgdPositionLeft(screen_id)));
	}
}

function runScreens() {
	$.get('http://localhost:8080/run');
}

function hideControls() {
	$('.controls').hide();
	$('.title').hide();
}

function setupControls() {
    $('.control#run').click(function () {
        runScreens();
    })
    $('.control.grid').click(function () {
		setupGrid();
    });
    $('.control.single').click(function () {
        var screen_id = parseInt($(this).attr('id'), 10);
        setupSingleScreen(screen_id);
    });
}