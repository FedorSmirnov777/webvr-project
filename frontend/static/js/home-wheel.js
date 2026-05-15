(function () {
  const wheel = document.getElementById('wheelInteractive');
  if (!wheel) return;

  let dragging = false;
  let angle = 0;
  let lastX = 0;

  const setAngle = (value) => {
    angle = value;
    wheel.style.transform = `rotate(${angle}deg)`;
  };

  const getX = (e) => (e.touches ? e.touches[0].clientX : e.clientX);

  const onDown = (e) => {
    dragging = true;
    lastX = getX(e);
    wheel.classList.add('dragging');
  };

  const onMove = (e) => {
    if (!dragging) return;
    const x = getX(e);
    const dx = x - lastX;
    lastX = x;
    setAngle(angle + dx * 0.9);
  };

  const onUp = () => {
    dragging = false;
    wheel.classList.remove('dragging');
  };

  wheel.addEventListener('mousedown', onDown);
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);

  wheel.addEventListener('touchstart', onDown, { passive: true });
  window.addEventListener('touchmove', onMove, { passive: true });
  window.addEventListener('touchend', onUp);
})();
