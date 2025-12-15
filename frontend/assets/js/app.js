// Premium UI interactions: continent->country->capital selection and flight offers
document.addEventListener('DOMContentLoaded', async () => {
  let regionSel = document.getElementById('region');
  let countrySel = document.getElementById('country');
  let citySel = document.getElementById('city');
  let originInput = document.getElementById('origin');
  let offersDiv = document.getElementById('offers');
  const container = document.querySelector('.container') || document.body;
  // Simple wiring test: display a small sample from backend DB
  const wiringCard = document.createElement('section'); wiringCard.className = 'card';
  wiringCard.innerHTML = `<h2>Backend Data Snapshot</h2><pre id="geoDump" style="max-height:200px; overflow:auto; background:#0b1324; color:#d7e3ff; padding:12px; border-radius:8px;"></pre>`;
  container.prepend(wiringCard);
  
  // If the new UI elements are missing, create them dynamically to ensure functionality
  if (!regionSel || !countrySel || !citySel || !originInput) {
    const section = document.createElement('section'); section.className = 'card';
    section.innerHTML = `
      <h2>Choose Destination</h2>
      <div class="grid">
        <div>
          <label for="origin">Origin</label>
          <input id="origin" placeholder="e.g., Paris" />
        </div>
        <div>
          <label for="region">Region</label>
          <select id="region"></select>
        </div>
        <div>
          <label for="country">Country</label>
          <select id="country"></select>
        </div>
        <div>
          <label for="city">City</label>
          <select id="city"></select>
        </div>
      </div>
      <button id="findFlights" class="primary">Find Flights</button>
    `;
    container.prepend(section);
  }
  // Re-resolve references
  const _regionSel = document.getElementById('region');
  const _countrySel = document.getElementById('country');
  const _citySel = document.getElementById('city');
  const _originInput = document.getElementById('origin');
  const _offersDiv = document.getElementById('offers') || (() => { const d = document.createElement('div'); d.id='offers'; d.className='offers'; (document.querySelector('.container')||document.body).appendChild(d); return d; })();
  regionSel = _regionSel; countrySel = _countrySel; citySel = _citySel; originInput = _originInput; offersDiv = _offersDiv;

  // Load geo dump to verify wiring
  (async () => {
    const dumpEl = document.getElementById('geoDump');
    try {
      const res = await fetch('/api/geo/dump');
      const json = await res.json();
      const preview = {
        regions: (json.regions||[]).map(c => c.name).slice(0, 9),
        countries: (json.countries||[]).map(c => c.name).slice(0, 10),
        cities: (json.cities||[]).map(c => c.name).slice(0, 10),
        counts: {
          regions: (json.regions||[]).length,
          countries: (json.countries||[]).length,
          cities: (json.cities||[]).length
        }
      };
      dumpEl.textContent = JSON.stringify(preview, null, 2);
    } catch (e) {
      dumpEl.textContent = 'Failed to fetch /api/geo/dump: ' + e;
    }
  })();

  async function loadRegions() {
    try {
      const res = await fetch('/api/geo/regions');
      const regions = await res.json();
      regionSel.innerHTML = '';
        const list = Array.isArray(regions) ? regions : [];
        if (!list.length) {
          ['Africa','America','Asia','Pacific','Indian','Europe','Atlantic','Australia','Arctic'].forEach(c => {
            const opt = document.createElement('option'); opt.value = c; opt.textContent = c; regionSel.appendChild(opt);
          });
        } else {
          list.forEach(c => {
            // Expecting {id, name}
            const opt = document.createElement('option');
            opt.value = c.id || c.name;
            opt.textContent = c.name;
            regionSel.appendChild(opt);
          });
        }
    } catch (e) {
      console.warn('Failed to load regions', e);
      // Fallback on error
      regionSel.innerHTML = '';
      ['Africa','America','Asia','Pacific','Indian','Europe','Atlantic','Australia','Arctic'].forEach(c => {
        const opt = document.createElement('option'); opt.value = c; opt.textContent = c; regionSel.appendChild(opt);
      });
    }
  }

  // Static fallback data to ensure dropdowns work even if CORS blocks fetching
  async function fetchCountriesByRegion(region) {
    try {
      const res = await fetch(`/api/geo/countries?region_id=${encodeURIComponent(region)}`);
      const arr = await res.json();
      if (Array.isArray(arr) && arr.length) return arr.map(c => ({ id: c.id, name: c.name }));
      // Fallback minimal mapping
      const MAP = {
        'Europe': [{name:'France'},{name:'Germany'},{name:'Greece'},{name:'Italy'},{name:'Spain'},{name:'United Kingdom'}],
        'Asia': [{name:'Japan'},{name:'China'},{name:'India'},{name:'South Korea'},{name:'Thailand'}],
        'America': [{name:'United States'},{name:'Canada'},{name:'Mexico'},{name:'Brazil'},{name:'Argentina'}],
        'Africa': [{name:'South Africa'},{name:'Nigeria'},{name:'Egypt'},{name:'Kenya'}],
        'Pacific': [{name:'Fiji'},{name:'Samoa'}],
        'Indian': [{name:'Mauritius'},{name:'Madagascar'}],
        'Atlantic': [{name:'Iceland'},{name:'Azores'}],
        'Australia': [{name:'Australia'}],
        'Arctic': []
      };
      return MAP[region] || [];
    } catch (e) {
      console.warn('Failed to load countries', e);
      const MAP = {
        'Europe': ['France','Germany','Greece','Italy','Spain','United Kingdom'],
        'Asia': ['Japan','China','India','South Korea','Thailand'],
        'America': ['United States','Canada','Mexico','Brazil','Argentina'],
        'Africa': ['South Africa','Nigeria','Egypt','Kenya'],
        'Pacific': ['Fiji','Samoa'],
        'Indian': ['Mauritius','Madagascar'],
        'Atlantic': ['Iceland','Azores'],
        'Australia': ['Australia'],
        'Arctic': []
      };
      return MAP[region] || [];
    }
  }

  async function fetchCitiesByCountry(country) {
    try {
      const res = await fetch(`/api/geo/cities?country_id=${encodeURIComponent(country)}`);
      const arr = await res.json();
      if (Array.isArray(arr) && arr.length) return arr;
      return [];
    } catch (e) {
      console.warn('Failed to load cities', e);
      return [];
    }
  }

  async function populateCountries() {
    countrySel.innerHTML = '';
    citySel.innerHTML = '';
    const countries = await fetchCountriesByRegion(regionSel.value);
    countries.forEach(ct => {
      // ct: {id, name}
      const opt = document.createElement('option');
      opt.value = ct.id || ct.name;
      opt.textContent = ct.name;
      countrySel.appendChild(opt);
    });
    // Auto-trigger capital for first country for better UX
    if (countries.length) {
      countrySel.value = countries[0].id || countries[0].name;
      await populateCities();
    }
  }
  regionSel?.addEventListener('change', populateCountries);

  async function populateCities() {
    citySel.innerHTML = '';
    const arr = await fetchCitiesByCountry(countrySel.value);
    arr.forEach(ci => {
      // ci: {id, name, ...}
      const opt = document.createElement('option');
      opt.value = ci.id || ci.name;
      opt.textContent = ci.name + (ci.is_capital ? ' (capital)' : '');
      citySel.appendChild(opt);
    });
  }
  countrySel?.addEventListener('change', populateCities);

  // --- FLIGHT SEARCH WIRING ---
  async function findFlights() {
    offersDiv.innerHTML = '<div class="loading">Searching for flights...</div>';
    const origin = originInput.value || '';
    const regionId = regionSel.value;
    const countryId = countrySel.value;
    const cityId = citySel.value;
    // Compose payload for backend
    const payload = {
      origin,
      region_id: regionId,
      country_id: countryId,
      city_id: cityId
    };
    try {
      const res = await fetch('/api/amadeus/search-flights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('Backend error: ' + res.status);
      const data = await res.json();
      if (Array.isArray(data) && data.length) {
        offersDiv.innerHTML = data.map(f => `<div class="offer-card"><b>${f.itinerary || f.carrier || 'Flight'}</b><br>From: ${f.origin} To: ${f.destination}<br>Price: ${f.price || 'N/A'}</div>`).join('');
      } else if (data && data.offers && Array.isArray(data.offers)) {
        offersDiv.innerHTML = data.offers.map(f => `<div class="offer-card"><b>${f.itinerary || f.carrier || 'Flight'}</b><br>From: ${f.origin} To: ${f.destination}<br>Price: ${f.price || 'N/A'}</div>`).join('');
      } else {
        offersDiv.innerHTML = '<div class="no-results">No flights found.</div>';
      }
    } catch (e) {
      offersDiv.innerHTML = `<div class="error">Error: ${e.message || e}</div>`;
    }
  }
  document.getElementById('findFlights')?.addEventListener('click', findFlights);

  // Initialize with a default continent to make the UI immediately functional
  await loadRegions();
  await populateCountries();
  await populateCities();

  document.getElementById('findFlights')?.addEventListener('click', async () => {
    const origin = (originInput?.value || 'Paris').trim();
    const destCity = citySel.value || countrySel.value;
    offersDiv.innerHTML = 'Loading flight offers...';
    try {
      const r = await fetch(`/api/amadeus/flight-offers-by-cities?originCity=${encodeURIComponent(origin)}&destinationCity=${encodeURIComponent(destCity)}&departure=2026-01-15&adults=1&includeMeta=true`);
      if (!r.ok) {
        const errText = await r.text();
        throw new Error(`HTTP ${r.status}: ${errText}`);
      }
      const data = await r.json();
      offersDiv.innerHTML = '';
      const list = Array.isArray(data) ? data : (Array.isArray(data?.data) ? data.data : []);
      if (!list.length) {
        offersDiv.innerHTML = 'No flight offers found or provider error.';
        return;
      }
      list.slice(0, 6).forEach(off => {
        const price = off?.price?.total || 'N/A';
        const segs = off?.itineraries?.[0]?.segments || [];
        const route = segs.length ? `${segs[0]?.departure?.iataCode} → ${segs[segs.length-1]?.arrival?.iataCode}` : '';
        const el = document.createElement('div'); el.className = 'offer';
        el.innerHTML = `<strong>${route}</strong><div>Price: ${price}</div>`;
        offersDiv.appendChild(el);
      });
    } catch (e) {
      offersDiv.innerHTML = 'Error: ' + (e?.message || e);
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
    { id: 'btn-activities-square', url: '/api/amadeus/activities-by-square?north=41.397158&west=2.160873&south=41.394582&east=2.177181' }
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
