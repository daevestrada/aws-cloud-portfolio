const API_URL = '/api/cost';

async function loadCosts() {
  const tbody = document.getElementById('daily-table');
  const mtdEl = document.getElementById('mtd-total');
  const activeDaysEl = document.getElementById('active-days');
  const lastUpdatedEl = document.getElementById('last-updated');
  const mtdMonthEl = document.getElementById('mtd-month');

  try {
    const res = await fetch(API_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // MTD total
    mtdEl.textContent = `$${data.mtd_total.toFixed(4)}`;

    // Month label
    const now = new Date();
    mtdMonthEl.textContent = now.toLocaleString('en-US', { month: 'long', year: 'numeric' });

    // Active days count
    const activeDays = data.daily_costs.filter(r => parseFloat(r.amount) > 0).length;
    activeDaysEl.textContent = activeDays;

    // Last updated
    lastUpdatedEl.textContent = `updated ${new Date().toLocaleTimeString()}`;

    // Daily table
    if (data.daily_costs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="3" class="status">No cost data available.</td></tr>';
      return;
    }

    tbody.innerHTML = data.daily_costs
      .map(row => `
        <tr>
          <td>${row.date}</td>
          <td>${row.service}</td>
          <td class="amount">$${parseFloat(row.amount).toFixed(4)}</td>
        </tr>`)
      .join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="3" class="status error">Failed to load cost data: ${err.message}</td></tr>`;
    mtdEl.textContent = '—';
    lastUpdatedEl.textContent = 'error';
    console.error('Cost API error:', err);
  }
}

loadCosts();

