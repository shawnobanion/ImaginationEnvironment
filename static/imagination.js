var socket = null;
var fade_ins = [], fade_outs = [];

var TEXT = {};
TEXT.in_time = 3000; // 2500;
TEXT.hold_time = 10000; // 5000;
TEXT.out_time = 4000; // 5000;
TEXT.delay_zero = 0;
TEXT.delay_one = 4000; // 3333;
TEXT.delay_two = 8000; // 6666;
TEXT.opacify_interval = 83;

$(function(foo) {
	setupControls();
	//setInterval(function() {fade('in');}, TEXT.opacify_interval);
	//setInterval(function() {fade('out');}, TEXT.opacify_interval);
	var id = getQueryStringParameter('id');
	if (id != '') {
		setupSingleScreen(id);
		hideControls();
	} else {
		setupGrid();
	}
	if (getQueryStringParameter('run')) { runScreens(); }
});

/*
function fade(in_or_out) {
    var stop_fades = [];
    var now = (new Date).valueOf();
    
    var arr = in_or_out == 'in' ? fade_ins : fade_outs;
    
    $.each(arr, function(i, info) {
        var text = info[0], start_time = info[1], stop_time = info[2];
        if ((start_time < now) && (now < stop_time)) {
            var total_time = stop_time - start_time;
            var elapsed = now - start_time;
            var progress = elapsed / total_time;
            progress = Math.min(progress, 1.0);
            if (in_or_out == 'out') {
                progress = 1 - progress;
            }
            text.css('opacity', progress);
        }
        if (now > stop_time) {
            var progress = in_or_out == 'in' ? 1.0 : 0.0;
            text.css('opacity', progress);
        }
    });
    arr = $.grep(arr, function(info, i) {
        return now < info[2];
    });
    
    // (in_or_out == 'in' ? fade_ins : fade_outs) = arr;
    
    if (in_or_out == 'in') {
        //blech
        fade_ins = arr;
    }
    else {
        fade_outs = arr;
    }
}

function set_fade(text, in_or_out, start_time_offset, fade_time) {
    //console.log('start_time_offset is %o, fade_time is %o', start_time_offset, fade_time);
    var fades = in_or_out == 'in' ? fade_ins : fade_outs;
    var curr_time = (new Date).valueOf();
    
    fades.push([text, curr_time + start_time_offset, curr_time + start_time_offset + fade_time]);
}

function ripple(screen_selector) {
    var text_zero = $(screen_selector + ' .text:eq(0)').first();
    var text_one = $(screen_selector + ' .text:eq(1)').first();
    var text_two = $(screen_selector + ' .text:eq(2)').first();
    
    var current_time = (new Date).valueOf();
    
    set_fade(text_zero, 'in', TEXT.delay_zero, TEXT.in_time);
    set_fade(text_zero, 'out', TEXT.delay_zero + TEXT.in_time + TEXT.hold_time, TEXT.out_time);
    
    set_fade(text_one, 'in', TEXT.delay_one, TEXT.in_time);
    set_fade(text_one, 'out', TEXT.delay_one + TEXT.in_time + TEXT.hold_time, TEXT.out_time);
    
    set_fade(text_two, 'in', TEXT.delay_two, TEXT.in_time);
    set_fade(text_two, 'out', TEXT.delay_two + TEXT.in_time + TEXT.hold_time, TEXT.out_time);
}
*/

function animateScreens() {
	console.log('animating screens');
	var initial_delay = 5000;
	setTimeout('highlightKeys()', initial_delay);
	setTimeout('fadeText()', initial_delay);
	setTimeout('fadeKeys()', initial_delay + 5000);
	setTimeout('highlightSearchKeys()', initial_delay + 5000);
	setTimeout('displayScreenImages()', initial_delay + 13000);
}

function highlightKeys() {
	$('.key').animate({color: '#f7da15'}, 2000);
	$('.search_key').animate({color: '#f7da15'}, 2000);
}

function highlightSearchKeys() {
	$(".search_key").animate({color: '#FFF'}, 2000);
}

function fadeText() {
	$('.screen').animate({color: '#343434'}, 4000);
}

function fadeKeys() {
	$(".key").animate({color: '#343434'}, 2000);
}

function displayScreenImages() {
	console.log('displaying images');
	$('.screen').each(function(i, obj) {
		$(obj).css('background-image', 'url("' + $(obj).attr('rel') + '")');
		$(obj).children('.text').fadeOut(2000);
	});
}

function onBulkUpdate(data) {
	var data = JSON.parse(data);
	for (var id = 0; id < data.length; id++) {
		var screen_ = $('#screen-' + id).first();
		if (screen_.length) {		
			console.log('updating screen id: ' + id);
			screen_.css('color', '#FFF');
			$('.text:eq(0)', screen_).html(data[id]['text0']);
			$('.text:eq(1)', screen_).html(data[id]['text1']);
			$('.text:eq(2)', screen_).html(data[id]['text2']);
			screen_.attr('rel', data[id]['image_url']);
		}
	}
	$('.screen').children('.text').fadeIn(2000);
	animateScreens();
}

function onUpdate(data) {
    var data = JSON.parse(data);
	var id = data['id'];
    var screen_ = $('#screen-' + id).first();
    if (screen_.length) {		
		console.log('updating screen id: ' + id);
		screen_.css('color', '#FFF');
		$('.text:eq(0)', screen_).html(data['text0']);
		$('.text:eq(1)', screen_).html(data['text1']);
		$('.text:eq(2)', screen_).html(data['text2']);
		screen_.attr('rel', data['image_url']);
		
		if (id % 3 == 1) {
			screen_.children('.text').fadeIn(2000);
		}
    }
	
	if (id == 8) animateScreens();
}

function resetSocket() {
    if (socket) {
		console.log('disconnecting socket');
        socket.disconnect();
        socket = null;
    }
	
	console.log('creating new socket and connecting');
	var server = 'localhost';
    socket = new io.Socket(server, {rememberTransport: false, port: 8080});
    socket.connect();
    socket.addEvent('message', onBulkUpdate);
}

function htmlForScreen(class_, id) {
    var ret = '<div class="' + class_ + ' screen" id="screen-' + id + '">'
    console.log("creating html for screen #" + id);
    ret += '<div class="text"></div>';
    ret += '<div class="text"></div>';
    ret += '<div class="text"></div>';
    ret += '</div>';
    return ret
}

function setupSingleScreen(id) {
	resetSocket();
	$('.title').text('Showing screen ' + (id));
	$('.screens').empty();
	$('.screens').append(htmlForScreen('single', id));
}

function setupGrid() {
	resetSocket();
	$('.title').text("Showing all nine screens");
	$('.screens').empty().css('width', '990px').css('height', '690px');
	for (var screen_id = 0; screen_id < 9; screen_id++) {
		$('.screens').append(htmlForScreen('grid', screen_id));
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
    $('.control.column').click(function () {
        resetSocket();
        var column_id = parseInt($(this).attr('id'), 10);
        $('.title').text('Showing column ' + (column_id));
        $('.screens').empty();
        for (var i =0 ; i < 3; i++) {
            var screen_id = column_id + 3 * i;
            $('.screens').append(htmlForScreen('column', screen_id));
        }
    });
    $('.control.single').click(function () {
        var screen_id = parseInt($(this).attr('id'), 10);
        setupSingleScreen(screen_id);
    });
}