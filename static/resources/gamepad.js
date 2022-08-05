// Config
const kDEV_MODE = false; // If true, changes will be logged rather than sent to server
const kCONTROL_REFRESH = 50; // Pause between controller refreshes (milliseconds)
const kLATENCY_PRECISION = 2; // Number of decimal places in latency
const kAXIS_PRECISION = 1; // Number of decimal places in joystick

// Get DOM Elements
const streamSelectContainer = document.getElementById("streamChooser");
const streamSelect = document.getElementById("streamDropdown");
const imgElement = document.getElementById("feed");
const connectedGamepadElement = document.getElementById("connectedGamepad");
const latencyElement = document.getElementById("latency");

// Show/Hide Camera Selector
streamSelectContainer.addEventListener("mouseenter", function(e) {
	streamSelectContainer.style.opacity = 0.9;
})

streamSelectContainer.addEventListener("mouseleave", function(e) {
	streamSelectContainer.style.opacity = 0.4;
})

// Change Camera Stream
streamSelect.addEventListener("change", function(e) {
	imgElement.setAttribute("src", `/camera/${streamSelect.value}`)
})

// Check For Gamepad Support
if (window.Gamepad == undefined) { window.location.replace("/noGamepad"); }

// Round to Any Number of Decimal Places
function round(value, numOfDecimalPlaces) {
	var multiplier = Math.pow(10, numOfDecimalPlaces || 0);
	return Math.round(value * multiplier) / multiplier;
}

// Make Request to Server
const request = new XMLHttpRequest();
var controlLoopTimeoutId = null;
var packetSentTime = 0;
var currentLatency = null;

request.onreadystatechange = function() {
	if (request.readyState != XMLHttpRequest.DONE) { return; }

	// Update Latency
	lat = Date.now() - packetSentTime;

	if (currentLatency == null) {
		currentLatency = lat;
	} else {
		currentLatency = (currentLatency + lat)/2;
	}

	latencyElement.innerHTML = `(Avg) Latency: ${round(currentLatency, kLATENCY_PRECISION)}ms`;

	// Handle Error
	if (request.status != 200) {
		alert(`Error while sending request (${request.status}): ${request.responseText}`);
	}

	// (Re)Run Control Loop
	controlLoopTimeoutId = window.setTimeout(controlLoop, kCONTROL_REFRESH);
}

// Connect Gamepad
var gamepadIndex = null;
var gamepadButtons = [];
var gamepadAxes = [];

window.addEventListener("gamepadconnected", function(e) {
	connectedGamepadElement.innerHTML = `[${e.gamepad.index}] ${e.gamepad.id}`;
	gamepadIndex = e.gamepad.index;

	gamepadButtons = [];
	gamepadAxes = [];

	// Save Current State
	for (var x = 0; x < e.gamepad.buttons.length; x++) {
		gamepadButtons.push(e.gamepad.buttons[x].pressed);
	}

	for (var x = 0; x < e.gamepad.axes.length; x++) {
		gamepadAxes.push(round(e.gamepad.axes[x], kAXIS_PRECISION));
	}
	gamepadAxes.push(round(e.gamepad.buttons[7].value, kAXIS_PRECISION));

	if (kDEV_MODE) {
		// Log Initial Packet
		console.log(gamepadButtons);
		console.log(gamepadAxes);

		controlLoopTimeoutId = window.setTimeout(controlLoop, kCONTROL_REFRESH);
	} else {
		// Send Initial Packet
		packetSentTime = Date.now()

		request.open("POST", "/controller/initialPacket");
		request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
		request.setRequestHeader("controllerId", e.gamepad.id.toString());
		request.send(JSON.stringify({
			"buttons": gamepadButtons,
			"axes": gamepadAxes
		}));
	}
})

// Disconnect Gamepad
window.addEventListener("gamepaddisconnected", function(e) {
	if (gamepadIndex != e.gamepad.index) { return }

	gamepadIndex = null;
	gamepadButtons = [];
	gamepadAxes = [];

	if (controlLoopTimeoutId != null) {
		window.clearTimeout(controlLoopTimeoutId);
		controlLoopTimeoutId = null;
	}

	connectedGamepadElement.innerHTML = "Waiting For Controller...";
	alert(`Warning: '${e.gamepad.id}' has disconnected!`);
})

// Control Loop
function controlLoop() {
	if (gamepadIndex == null) { return; }

	let gamepad;

	if (navigator.webkitGetGamepads != undefined) {
		gamepad = navigator.webkitGetGamepads()[gamepadIndex];
	} else {
		gamepad = navigator.getGamepads()[gamepadIndex];
	}

	// Check For Changes
	packetButtons = {};
	packetAxes = {};

	for (var x = 0; x < gamepad.buttons.length; x++) {
		if (gamepadButtons[x] != gamepad.buttons[x].pressed) {
			gamepadButtons[x] = gamepad.buttons[x].pressed;
			packetButtons[x] = gamepad.buttons[x].pressed;

			if (kDEV_MODE) {
				console.log(`Button ${x} is now ${gamepad.buttons[x].pressed}`);
			}
		}
	}

	for (var x = 0; x < gamepad.axes.length; x++) {
		value = round(gamepad.axes[x], kAXIS_PRECISION);
		if (gamepadAxes[x] != value) {
			gamepadAxes[x] = value;
			packetAxes[x] = value;

			if (kDEV_MODE) {
				console.log(`Axis ${x} is now ${value}`);
			}
		}
	}

	r2Val = round(gamepad.buttons[7].value, kAXIS_PRECISION);
	if (r2Val !=  gamepadAxes[4]) {
		gamepadAxes[4] = r2Val
		packetAxes[4] = r2Val;

		if (kDEV_MODE) {
			console.log(`R2 is now ${value}`);
		}
	}

	// Send Packet (Only if NOT Empty and not Dev Mode)
	if ((Object.keys(packetButtons).length == 0 && Object.keys(packetAxes).length == 0) || kDEV_MODE) {
		controlLoopTimeoutId = window.setTimeout(controlLoop, kCONTROL_REFRESH);
		return;
	}

	packetSentTime = Date.now()

	request.open("POST", "/controller/packet");
	request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
	request.send(JSON.stringify({
		"buttons": packetButtons,
		"axes": packetAxes
	}));
}
