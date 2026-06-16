const API_URL = '/api/cost';

function formatUSD(value, decimals = 4) {
  const num = Number(value) || 0;
  const fixed = num.toFixed(decimals);
  // avoid an ugly "-0.0000" caused by floating-point noise around zero
  return fixed === `-${(0).toFixed(decimals)}` ? (0).toFixed(decimals) : fixed;
}

function formatDate(isoDate) {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

async function loadCosts() {
  const grossEl = document.getElementById('gross-total');
  const creditsAppliedEl = document.getElementById('credits-applied');
  const netEl = document.getElementById('net-total');
  const remainingEl = document.getElementById('credits-remaining');
  const expirationEl = document.getElementById('days-until-expiration');
  const expirationSubEl = document.getElementById('expiration-date');
  const periodEl = document.getElementById('period-label');
  const lastUpdatedEl = document.getElementById('last-updated');
  const tbody = document.getElementById('services-table');

  try {
    const res = await fetch(API_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    grossEl.textContent = `$${formatUSD(data.gross_total_mtd)}`;
    creditsAppliedEl.textContent = `-$${formatUSD(Math.abs(data.credits_applied_mtd))}`;
    netEl.textContent = `$${formatUSD(data.net_total_mtd)}`;
    remainingEl.textContent = `$${formatUSD(data.credits_remaining, 2)}`;
    expirationEl.textContent = `${data.days_until_expiration} days`;
    expirationSubEl.textContent = `until ${formatDate(data.credit_expiration_date)}`;

    const periodStart = new Date(`${data.period_start}T00:00:00`);
    periodEl.textContent = periodStart.toLocaleString('en-US', { month: 'long', year: 'numeric' });

    lastUpdatedEl.textContent = `updated ${new Date().toLocaleTimeString()}`;

    if (!data.services || data.services.length === 0) {
      tbody.innerHTML = '<tr><td colspan="2" class="status">No service costs recorded yet this period.</td></tr>';
      return;
    }

    tbody.innerHTML = data.services
      .map(row => `
        <tr>
          <td>${row.service}</td>
          <td class="amount">$${formatUSD(row.gross_cost)}</td>
        </tr>`)
      .join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="2" class="status error">Failed to load cost data: ${err.message}</td></tr>`;
    grossEl.textContent = '—';
    creditsAppliedEl.textContent = '—';
    netEl.textContent = '—';
    remainingEl.textContent = '—';
    expirationEl.textContent = '—';
    lastUpdatedEl.textContent = 'error';
    console.error('Cost API error:', err);
  }
}

loadCosts();
