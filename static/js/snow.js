// static/js/snow.js
document.addEventListener('DOMContentLoaded', () => {
  const snow = document.querySelector('.snow');
  const width = window.innerWidth;
  for (let i = 0; i < 200; i++) {
    const flake = document.createElement('span');
    flake.className = 'snowflake';

    // random horizontal start
    flake.style.left = `${Math.random() * width}px`;

    // random speed & delay
    const duration = 10 + Math.random() * 20;
    flake.style.animationDuration = `${duration}s`;
    flake.style.animationDelay    = `${-Math.random() * duration}s`;

    // random size & opacity
    const scale = 0.2 + Math.random() * 0.8;
    flake.style.transform = `scale(${scale})`;
    flake.style.opacity   = `${0.2 + Math.random() * 0.6}`;

    snow.appendChild(flake);
  }
});
