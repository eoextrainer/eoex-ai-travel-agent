// Premium UI interactions: continent->country->capital selection and flight offers
document.addEventListener('DOMContentLoaded', () => {
  const continentSel = document.getElementById('continent');
  const countrySel = document.getElementById('country');
  const capitalSel = document.getElementById('capital');
  const offersDiv = document.getElementById('offers');
  
  // If the new UI elements are missing, create them dynamically to ensure functionality
  if (!continentSel || !countrySel || !capitalSel) {
    const container = document.querySelector('.container') || document.body;
    const section = document.createElement('section'); section.className = 'card';
    section.innerHTML = `
      <h2>Choose Destination</h2>
      <div class="grid">
        <div>
          <label for="continent">Continent</label>
          <select id="continent"></select>
        </div>
        <div>
          <label for="country">Country</label>
          <select id="country"></select>
        </div>
        <div>
          <label for="capital">Capital City</label>
          <select id="capital"></select>
        </div>
      </div>
      <button id="findFlights" class="primary">Find Flights from Paris</button>
    `;
    container.prepend(section);
  }
  // Re-resolve references
  const _continentSel = document.getElementById('continent');
  const _countrySel = document.getElementById('country');
  const _capitalSel = document.getElementById('capital');
  const _offersDiv = document.getElementById('offers') || (() => { const d = document.createElement('div'); d.id='offers'; d.className='offers'; (document.querySelector('.container')||document.body).appendChild(d); return d; })();
  continentSel = _continentSel; countrySel = _countrySel; capitalSel = _capitalSel; offersDiv = _offersDiv;

  async function loadContinents() {
    try {
      const res = await fetch('/api/geo/continents');
      const continents = await res.json();
      continentSel.innerHTML = '';
      continents.forEach(c => { const opt = document.createElement('option'); opt.value = c; opt.textContent = c; continentSel.appendChild(opt); });
    } catch (e) {
      console.warn('Failed to load continents', e);
    }
  }

  // Static fallback data to ensure dropdowns work even if CORS blocks fetching
  async function fetchCountriesByContinent(continent) {
    try {
      const res = await fetch(`/api/geo/countries?continent=${encodeURIComponent(continent)}`);
      return await res.json();
    } catch (e) {
      console.warn('Failed to load countries', e);
      return [];
    }
  }

  async function fetchCapitalByCountry(country) {
    try {
      const res = await fetch(`/api/geo/capitals?country=${encodeURIComponent(country)}`);
      const arr = await res.json();
      return arr[0] || '';
    } catch (e) {
      console.warn('Failed to load capital', e);
      return '';
    }
  }

  async function populateCountries() {
    countrySel.innerHTML = '';
    capitalSel.innerHTML = '';
    const countries = await fetchCountriesByContinent(continentSel.value);
    countries.forEach(ct => { const opt = document.createElement('option'); opt.value = ct; opt.textContent = ct; countrySel.appendChild(opt); });
    // Auto-trigger capital for first country for better UX
    if (countries.length) {
      countrySel.value = countries[0];
      await populateCapital();
    }
  }
  continentSel?.addEventListener('change', populateCountries);

  async function populateCapital() {
    capitalSel.innerHTML = '';
    const capital = await fetchCapitalByCountry(countrySel.value);
    if (capital) { const opt = document.createElement('option'); opt.value = capital; opt.textContent = capital; capitalSel.appendChild(opt); }
  }
  countrySel?.addEventListener('change', populateCapital);

  // Initialize with a default continent to make the UI immediately functional
  await loadContinents();
  if (continentSel.options.length) {
    continentSel.value = continentSel.options[0].value;
    populateCountries();
  }

  document.getElementById('findFlights')?.addEventListener('click', async () => {
    const capital = capitalSel.value || countrySel.value;
    offersDiv.innerHTML = 'Loading flight offers...';
    try {
      const r = await fetch(`/api/amadeus/flight-offers-by-cities?originCity=Paris&destinationCity=${encodeURIComponent(capital)}&departure=2026-01-15&adults=1`);
      const data = await r.json();
      offersDiv.innerHTML = '';
      (data || []).slice(0, 6).forEach(off => {
        const price = off?.price?.total || 'N/A';
        const segs = off?.itineraries?.[0]?.segments || [];
        const route = segs.length ? `${segs[0]?.departure?.iataCode} → ${segs[segs.length-1]?.arrival?.iataCode}` : '';
        const el = document.createElement('div'); el.className = 'offer';
        el.innerHTML = `<strong>${route}</strong><div>Price: ${price}</div>`;
        offersDiv.appendChild(el);
      });
    } catch (e) {
      offersDiv.innerHTML = 'Error: ' + e;
    }
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const results = document.getElementById('results');
  const endpoints = [
    { id: 'btn-health', url: '/api/amadeus/health' },
    { id: 'btn-checkin', url: '/api/amadeus/checkin-links?airlineCode=BA' },
    { id: 'btn-locations', url: '/api/amadeus/locations?keyword=Athens&subType=CITY' },
    { id: 'btn-destinations', url: '/api/amadeus/flight-destinations?origin=MAD' },
    { id: 'btn-dates', url: '/api/amadeus/flight-dates?origin=MAD&destination=MUC' },
    { id: 'btn-hotels', url: '/api/amadeus/hotel-offers?hotelIds=ADPAR001&adults=2' },
    { id: 'btn-airlines', url: '/api/amadeus/airlines?airlineCodes=BA' },
    { id: 'btn-locations-any', url: '/api/amadeus/locations-any?keyword=LON' },
    { id: 'btn-locations-city', url: '/api/amadeus/locations-city?keyword=PAR' },
    { id: 'btn-air-traffic-booked', url: '/api/amadeus/air-traffic-booked?originCityCode=MAD&period=2017-08' },
    { id: 'btn-air-traffic-traveled', url: '/api/amadeus/air-traffic-traveled?originCityCode=MAD&period=2017-01' },
    { id: 'btn-air-traffic-busiest', url: '/api/amadeus/air-traffic-busiest?cityCode=MAD&period=2017&direction=ARRIVING' },
    { id: 'btn-activities-geo', url: '/api/amadeus/activities-by-geo?latitude=40.41436995&longitude=-3.69170868' },
    { id: 'btn-activities-square', url: '/api/amadeus/activities-by-square?north=41.397158&west=2.160873&sout
h=41.394582&east=2.177181' }
  ];

  if (results) {
    endpoints.forEach(ep => {
      const btn = document.getElementById(ep.id);
      btn?.addEventListener('click', async () => {
        results.textContent = `Calling ${ep.url}...`;
        try {
          const res = await fetch(ep.url);
          const data = await res.json();
          results.textContent = JSON.stringify(data, null, 2);
        } catch (e) {
          results.textContent = 'Error: ' + e;
        }
      });
    });
  }
});
