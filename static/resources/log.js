// Config
const kREFRESH_TIMEOUT = 500;

// Get Elements
const messageCountElem = document.getElementById("messageCount");
const warningCountElem = document.getElementById("warningCount");
const errorCountElem = document.getElementById("errorCount")
const versionElem = document.getElementById("version");
const logElem = document.getElementById("log");

// Loop
var stopTimeout = false;

// Counts
var messageCount = 0;
var warningCount = 0;
var errorCount = 0;
var currentVersion = 0;

// Current Time
function time() {
	let date = new Date();
	return `${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`;
}

// Add to Log
function addToLog(time, message, type) {
	line = document.createElement("div");
	line.innerText = `[${time}] ${message}`;
	line.classList.add(type);
	line.setAttribute("title", type);

	logElem.append(line);
   	logElem.scrollTo(0, logElem.scrollHeight);

	switch(type) {
		case "message":
			messageCount += 1;
			messageCountElem.innerHTML = messageCount;
			break;
		case "warning":
			warningCount += 1;
			warningCountElem.innerHTML = warningCount;
			break;
		case "error":
			errorCount += 1;
			errorCountElem.innerHTML = errorCount;
			break;
		case "local":
			break;
		default:
			let date = new Date();
			addToLog(time(), `Unknown message type: ${type}`, "local");
			break;
	}
}

// Refresh
const request = new XMLHttpRequest();

function refreshLoop() {
	request.open("GET", `/log/raw?version=${currentVersion}`);
	request.send();
}

request.onreadystatechange = function() {
	if (request.readyState != XMLHttpRequest.DONE) { return; }
	if (request.status == 206) {
		// Add Missing Data
		split = request.responseText.split(";");
		v = parseInt(split.shift());

		full = JSON.parse(split.join(";"));

		for (var x = 0; x < full.length; x++) {
			if (x+1 <= currentVersion) { continue; }
			addToLog(full[x]["time"], full[x]["message"], full[x]["level"]);
		}

		currentVersion = v;
	} else if (request.status == 409) {
		// Fix Version (Too High)
		addToLog(time(), `Version too high, is ${currentVersion}, should be ${request.responseText}`, "local");
		currentVersion = parseInt(request.responseText);
	} else if (request.status != 200) {
		// Error
		addToLog(time(), `Server refresh failed (HTTP status ${request.status}): ${request.responseText}`, "local");
	}

	versionElem.innerHTML = currentVersion;

	if (!stopTimeout) {
		window.setTimeout(refreshLoop, kREFRESH_TIMEOUT);
	} else {
		addToLog(time(), "Stopped refreshing. Reload page to continue", "local"); 
	}
}

// Stop Logging
function stop() {
	stopTimeout = true;
}

// Start Loop
refreshLoop();
