let features = [
	{
		"src": "01.jpg",
		"desc": `Enhances and broadens convenient access to HURDAT2 for analysis. Get raw and derived variables for tropical cyclones, seasons, or eras.`
	},
	{
		"src": "02.svg",
		"desc": `Display detailed summaries or reports for individual cyclones or seasons`
	},
	{
		"src": "03.svg",
		"desc": `Rank and compare cyclones and seasons by requested values`
	},
	{
		"src": "04_AL171995_-_OPAL_Tracks.jpeg",
		"desc": `Render interactive track maps for tropical cyclones using the matplotlib module`
	},
];
// gallery description div
let featgal = document.getElementById("features-gallery"); 		// container
let galdesc = document.getElementById("gallery-description"); 	// text desc of images
let galimg = document.getElementById("features-image");		// images show here
let galmark = document.getElementById("gallery-markers");	// 'bullet' points


function _init() {
	// generate bullet points / markers
	for (let i=0; i < features.length; i++) {
		let pt = document.createElement("span");
		pt.innerHTML = "&bull;";
		galmark.appendChild(pt);
	}
	change_feature(1);
	// auto-change feature stuff
	start_browse_timer()	// initial setting of browser (interval)
	featgal._idle_time_id = null;
	featgal._idle_start = performance.now();
	featgal.onclick = pause_browse_timer;
}

function start_browse_timer(t=5) {
	// console.log("auto change image", t);
	featgal._browse_timer_id = setTimeout(
		function() {
			start_browse_timer();
			change_feature(1);
		},
		t * 1000
	);
}

function increment_idle_time(target=15) {
	// console.log(performance.now() - featgal._idle_start);
	if (performance.now() - featgal._idle_start >= target * 1000) {
		start_browse_timer();
		clearInterval(featgal._idle_time_id);
	}
}

function pause_browse_timer() {
	// console.log("paused browse timer");
	try {
		clearTimeout(featgal._browse_timer_id);
		clearInterval(featgal._idle_time_id);
		featgal._idle_start = performance.now();
	} catch(err) {console.log(err);}
	featgal._idle_time_id = setInterval(increment_idle_time, 1000);
}

function change_feature(dir) {
	let indx = parseInt(galdesc.dataset.index);
	let newindx = (indx + dir > features.length-1) ?
		-1 + dir :
		indx + dir
	;
	let newfeature = features.at(newindx);

	// remove class of previously highlighted feature
	try {
		galmark.childNodes[indx].setAttribute("class", "");
	} catch(err) {};

	// add class to corresponding marker of the newly highlighted feature
	galmark.childNodes[
		features.indexOf(newfeature)
	].setAttribute("class", "marker-select");

	// change description text
	galdesc.innerText = newfeature.desc;
	// change html index of the feature
	galdesc.dataset.index = features.indexOf(newfeature);
	// change image
	try {galimg.src = newfeature.src;} catch(err) {console.log(err)};
}