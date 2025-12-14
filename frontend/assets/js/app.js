document.getElementById('search-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const origin = document.getElementById('origin').value;
  const destination = document.getElementById('destination').value;
  const date = document.getElementById('date').value;

  const results = document.getElementById('results');
  results.textContent = 'Searching...';
  try {
    const resp = await fetch(`/api/amadeus/test?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}&date=${encodeURIComponent(date)}`);
    const data = await resp.json();
    results.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    results.textContent = 'Error: ' + err;
  }
});
