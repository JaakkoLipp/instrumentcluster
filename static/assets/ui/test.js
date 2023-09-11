const speedo = document.getElementById("speedo");
const durations = [300, 1000, 500, 800]; // Time intervals in milliseconds
let currentIndex = 0;
const menoperkel = document.getElementsByClassName("blinkperkel");

function animateWidth() {
    speedo.style.width = "10%";
    
    for (let i = 0; i < menoperkel.length; i++) {
        // Do something with each element
        menoperkel[i]. setAttribute("stroke", "white");
      }
      speedo.style.backgroundColor = "white";
      setTimeout(() => {
        speedo.style.width = "40%";
    setTimeout(() => {
        speedo.style.width = "80%";
    setTimeout(() => {
        speedo.style.width = "92%";

        for (let i = 0; i < menoperkel.length; i++) {
            // Do something with each element
            menoperkel[i]. setAttribute("stroke", "red");
          }
          speedo.style.backgroundColor = "red";
        setTimeout(() => {
            speedo.style.width = "100%";

            setTimeout(() => {
                currentIndex = (currentIndex + 1) % durations.length;
                animateWidth();
            }, durations[currentIndex]);
        }, durations[currentIndex]);
    }, durations[currentIndex]);
}, durations[currentIndex]);
    }, durations[currentIndex]);
}

animateWidth(); // Start the animation loop
