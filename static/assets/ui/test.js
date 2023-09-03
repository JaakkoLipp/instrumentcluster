const speedo = document.getElementById("speedo");
const durations = [300, 1000, 1000, 300]; // Time intervals in milliseconds
let currentIndex = 0;

function animateWidth() {
    speedo.style.width = "10%";
    setTimeout(() => {
        speedo.style.width = "40%";
    setTimeout(() => {
        speedo.style.width = "70%";
        setTimeout(() => {
            speedo.style.width = "100%";

            setTimeout(() => {
                currentIndex = (currentIndex + 1) % durations.length;
                animateWidth();
            }, durations[currentIndex]);
        }, durations[currentIndex]);
    }, durations[currentIndex]);
    }, durations[currentIndex]);
}

animateWidth(); // Start the animation loop
