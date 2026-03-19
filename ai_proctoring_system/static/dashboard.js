// ⏱ TIMER + STATS COMBINED LOOP
let seconds = 0;

async function updateAll(){

// ---------- FETCH STATS ----------
let res = await fetch("/stats");
let data = await res.json();

document.getElementById("faces").innerText = data.faces;
document.getElementById("blinks").innerText = data.blinks;
document.getElementById("focus").innerText = data.focus + "%";
document.getElementById("gaze").innerText = data.gaze;
document.getElementById("status").innerText = data.status;

// ---------- TIMER ----------
seconds++;

let hrs = String(Math.floor(seconds / 3600)).padStart(2,'0');
let mins = String(Math.floor((seconds % 3600) / 60)).padStart(2,'0');
let secs = String(seconds % 60).padStart(2,'0');

document.getElementById("timer").innerText = hrs + ":" + mins + ":" + secs;

}

// Run everything together
setInterval(updateAll, 1000);


// 📄 EXPORT
function downloadReport(){
window.location="/export";
}