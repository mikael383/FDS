/**
 * Fayda Citizen Kiosk Logic
 * Handles tracking lookups, priority toggle, dynamic desk banner rendering, and visual state management.
 */

// API Base URL - points to localhost backend on port 8000
const API_BASE = window.location.port === '8000'
  ? ''
  : (window.location.hostname === '127.0.0.1' ? 'http://127.0.0.1:8000' : 'http://localhost:8000');

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  const priorityCheckbox = document.getElementById('priorityCheckbox');
  const trackBtn = document.getElementById('trackBtn');
  const trackForm = document.getElementById('trackForm');
  const resultsSection = document.getElementById('resultsSection');
  const samplePills = document.getElementById('samplePills');

  // Submit via Enter key or button click
  trackForm.addEventListener('submit', (e) => {
    e.preventDefault();
    performLookup();
  });

  trackBtn.addEventListener('click', (e) => {
    e.preventDefault();
    performLookup();
  });

  // Handle Quick-Fill Sample Pills
  samplePills.addEventListener('click', (e) => {
    const btn = e.target.closest('.sample-btn');
    if (!btn) return;

    // Highlight selected sample pill
    document.querySelectorAll('.sample-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const id = btn.getAttribute('data-id');
    const prio = btn.getAttribute('data-prio') === 'true';

    searchInput.value = id;
    priorityCheckbox.checked = prio;
    performLookup();
  });

  async function performLookup() {
    const rawQuery = searchInput.value.trim();
    if (!rawQuery) {
      showToast('Please enter your Fayda ID or Phone Number.', 'error');
      searchInput.focus();
      return;
    }

    // Sync active state on sample buttons matching query
    document.querySelectorAll('.sample-btn').forEach(b => {
      if (b.getAttribute('data-id') === rawQuery) {
        b.classList.add('active');
      } else {
        b.classList.remove('active');
      }
    });

    const isPriority = priorityCheckbox.checked;

    trackBtn.disabled = true;
    trackBtn.innerHTML = `<span>Searching records...</span>`;

    try {
      const encodedId = encodeURIComponent(rawQuery);
      const url = `${API_BASE}/api/v1/track/${encodedId}?priority_requested=${isPriority}`;

      const response = await fetch(url);
      const data = await response.json();

      if (!response.ok) {
        renderNotFound(data.detail || 'Card not found.');
        showToast(data.detail || 'No record found.', 'error');
        return;
      }

      renderCardResult(data);
      showToast(`Record found for ${data.full_name}`, 'success');
      resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    } catch (err) {
      console.error('Lookup error:', err);
      showToast('Failed to connect to Postal Dispatch System. Please check connection.', 'error');
    } finally {
      trackBtn.disabled = false;
      trackBtn.innerHTML = `<span>Check Status & Get Counter Desk</span><span aria-hidden="true">➔</span>`;
    }
  }

  function renderCardResult(card) {
    resultsSection.style.display = 'block';

    const status = card.status;
    const isReady = status === 'Ready for Collection';
    const isTransit = status === 'In Transit';
    const isCollected = status === 'Collected';

    let deskBannerHtml = '';
    let statusPillClass = 'transit';
    let statusPillText = status;

    if (isReady) {
      statusPillClass = 'ready';
      statusPillText = 'Ready for Collection';

      const deskLabel = card.assigned_desk || 'Desk 2 (Counter Desk 2)';
      const isPriorityCounter = deskLabel.includes('Desk 1');

      deskBannerHtml = `
        <div class="desk-dispatch-banner">
          <div class="desk-banner-eyebrow">
            <span>${isPriorityCounter ? '⚡ PRIORITY COUNTER DISPATCH' : '📍 COUNTER DISPATCH'}</span>
          </div>
          <div class="desk-banner-target">
            PROCEED TO <span class="desk-banner-highlight">${escapeHtml(deskLabel.split('(')[0].trim())}</span>
          </div>
          <div class="desk-banner-instruction">
            <strong>${escapeHtml(deskLabel)}</strong><br>
            ${escapeHtml(card.instruction || 'Please proceed to the designated counter with your physical receipt or identity document.')}
          </div>
        </div>
      `;
    } else if (isTransit) {
      statusPillClass = 'transit';
      statusPillText = 'In Transit';
      deskBannerHtml = `
        <div class="state-notice-banner transit">
          <span class="state-notice-icon">🚚</span>
          <div class="state-notice-title">Card In Transit to Post Office</div>
          <div class="state-notice-desc">
            Your Fayda National ID card has been printed and is in transit to <strong>${escapeHtml(card.branch_name)}</strong>.
            Please check again in 24 to 48 hours for your counter desk assignment.
          </div>
        </div>
      `;
    } else if (isCollected) {
      statusPillClass = 'collected';
      statusPillText = 'Already Collected';
      const formattedDate = card.collected_at ? formatDate(card.collected_at) : 'Earlier Date';
      deskBannerHtml = `
        <div class="state-notice-banner collected">
          <span class="state-notice-icon">✅</span>
          <div class="state-notice-title">Card Already Issued</div>
          <div class="state-notice-desc">
            This card was previously collected on <strong>${formattedDate}</strong> at ${escapeHtml(card.branch_name)}.
          </div>
        </div>
      `;
    }

    const priorityBadge = card.priority_applied
      ? `<span class="pill-tag" style="background:#fef3c7; color:#92400e; font-weight:700; border:1px solid #f59e0b; margin-left:6px;">⚡ Priority Access</span>`
      : '';

    const arrivedDate = card.arrived_at ? formatDate(card.arrived_at) : 'Pending Dispatch';
    const storageBinDisplay = card.storage_bin || 'Unassigned';

    resultsSection.innerHTML = `
      <article class="kiosk-card ${isReady ? 'ready-state' : ''}">
        ${deskBannerHtml}

        <div class="card-details-body">
          <div class="card-top-meta">
            <div class="citizen-identity">
              <h3>${escapeHtml(card.full_name)} ${priorityBadge}</h3>
              <p>Fayda ID: <strong>${escapeHtml(card.fayda_id)}</strong></p>
            </div>
            <div>
              <span class="status-pill ${statusPillClass}">
                <span aria-hidden="true">${isReady ? '●' : (isTransit ? '⏳' : '✓')}</span>
                ${statusPillText}
              </span>
            </div>
          </div>

          <div class="details-grid">
            <div class="detail-box">
              <div class="detail-box-label">Mobile Phone</div>
              <div class="detail-box-value">${escapeHtml(card.phone_number)}</div>
            </div>

            <div class="detail-box">
              <div class="detail-box-label">Age & DOB</div>
              <div class="detail-box-value">${card.age} yrs (${escapeHtml(card.date_of_birth)})</div>
            </div>

            <div class="detail-box">
              <div class="detail-box-label">Collection Branch</div>
              <div class="detail-box-value">${escapeHtml(card.branch_name)}</div>
            </div>

            <div class="detail-box storage-bin-box">
              <div class="detail-box-label">Physical Storage Location</div>
              <div class="detail-box-value">📦 ${escapeHtml(storageBinDisplay)}</div>
            </div>
          </div>

          ${isReady ? `
            <div style="margin-top: 1.5rem; padding: 1rem; background: #eff6ff; border-radius: 8px; border-left: 4px solid #1d4ed8; font-size: 0.9rem; color: #1e3a8a;">
              <strong>Counter Instructions:</strong> Show your ticket to the postal officer at <strong>${escapeHtml(card.assigned_desk)}</strong>. Card is filed in <strong>${escapeHtml(storageBinDisplay)}</strong>.
            </div>
          ` : ''}
        </div>
      </article>
    `;
  }

  function renderNotFound(message) {
    resultsSection.style.display = 'block';
    resultsSection.innerHTML = `
      <div class="kiosk-card" style="padding: 2.5rem; text-align: center;">
        <span style="font-size: 3rem; display: block; margin-bottom: 0.75rem;">🔍</span>
        <h3 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 0.5rem;">No Record Found</h3>
        <p style="color: #64748b; max-width: 480px; margin: 0 auto;">
          ${escapeHtml(message)}
        </p>
      </div>
    `;
  }

  function formatDate(isoStr) {
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoStr;
    }
  }

  function showToast(msg, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type === 'error' ? 'error' : ''}`;
    toast.innerHTML = `
      <span>${type === 'error' ? '⚠️' : '✓'}</span>
      <span>${escapeHtml(msg)}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.4s ease';
      setTimeout(() => toast.remove(), 400);
    }, 4000);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
