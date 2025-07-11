function loadEvents() {
  fetch('/events')
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById('event-list');
      list.innerHTML = '';
      data.forEach(event => {
        const li = document.createElement('li');
        li.innerText = event;
        list.appendChild(li);
      });
    });
}

loadEvents(); // Initial call
setInterval(loadEvents, 15000); // Refresh every 15 seconds
