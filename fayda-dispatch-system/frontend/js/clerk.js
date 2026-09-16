/**
 * Fayda Postal Counter Terminal Logic
 * Handles storage bin physical retrieval, live handover issuing, running audit trail, and inventory management.
 */

// API Base URL - handles both relative paths (when served from FastAPI) and local dev
const API_BASE = window.location.origin.includes('8000')
  ? ''
  : (window.location.origin.startsWith('http') ? '' : 'http://127.0.0.1:8000');

let currentActiveCard = null;
let currentFilterStatus = 'All';
let cachedCards = [];

document.addEventListener('DOMContentLoaded', () => {
  // Authentication Guard
  const rawAuth = sessionStorage.getItem('fayda_clerk_auth');
  if (!rawAuth) {
    window.location.href = 'login.html';
    return;
  }

  let authData = {};
  try {
    authData = JSON.parse(rawAuth);
  } catch (err) {
    sessionStorage.removeItem('fayda_clerk_auth');
    window.location.href = 'login.html';
    return;
  }

  // Populate authenticated user info in header
  const clerkSessionName = document.getElementById('clerkSessionName');
  const clerkSessionDesk = document.getElementById('clerkSessionDesk');
  const clerkLogoutBtn = document.getElementById('clerkLogoutBtn');

  if (clerkSessionName && authData.clerk_name) {
    clerkSessionName.textContent = authData.clerk_name;
  }
  if (clerkSessionDesk && authData.desk) {
    // Shorten desk title for pill if needed
    const shortDesk = authData.desk.includes('Desk 1') ? 'Desk 1 (Priority)'
      : (authData.desk.includes('Desk 2') ? 'Desk 2'
        : (authData.desk.includes('Desk 3') ? 'Desk 3' : authData.desk));
    clerkSessionDesk.textContent = shortDesk;
  }

  // Handle Logout
  if (clerkLogoutBtn) {
    clerkLogoutBtn.addEventListener('click', () => {
      sessionStorage.removeItem('fayda_clerk_auth');
      showToast('Logged out successfully.', 'info');
      setTimeout(() => {
        window.location.href = 'login.html';
      }, 500);
    });
  }

  // Elements
  const clerkSearchInput = document.getElementById('clerkSearchInput');
  const clerkSearchBtn = document.getElementById('clerkSearchBtn');
  const clerkSamplePills = document.getElementById('clerkSamplePills');
  const activeHandoverBox = document.getElementById('activeHandoverBox');
  const clerkEmptyState = document.getElementById('clerkEmptyState');
  const confirmHandoverBtn = document.getElementById('confirmHandoverBtn');
  const refreshAuditBtn = document.getElementById('refreshAuditBtn');
  const statusFilterPills = document.getElementById('statusFilterPills');
  const clerkSelect = document.getElementById('clerkSelect');
  const deskSelect = document.getElementById('deskSelect');

  // Sync selected desk and clerk with auth
  if (deskSelect && authData.desk) {
    deskSelect.value = authData.desk;
  }
  if (clerkSelect && authData.clerk_id) {
    // Check if clerk exists in dropdown, else append
    let exists = false;
    for (let opt of clerkSelect.options) {
      if (opt.value === authData.clerk_id) {
        exists = true;
        break;
      }
    }
    if (!exists) {
      const newOpt = document.createElement('option');
      newOpt.value = authData.clerk_id;
      newOpt.textContent = `${authData.clerk_id} (${authData.clerk_name})`;
      clerkSelect.appendChild(newOpt);
    }
    clerkSelect.value = authData.clerk_id;
  }

  // Search Listeners
  clerkSearchBtn.addEventListener('click', () => {
    fetchActiveCitizen(clerkSearchInput.value.trim());
  });

  clerkSearchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      fetchActiveCitizen(clerkSearchInput.value.trim());
    }
  });

  // Handover confirmation button
  confirmHandoverBtn.addEventListener('click', processHandover);

  // Refresh Audit Button
  refreshAuditBtn.addEventListener('click', loadTerminalData);

  // Status Filter Pills
  statusFilterPills.addEventListener('click', (e) => {
    const pill = e.target.closest('.filter-pill');
    if (!pill) return;
    document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    currentFilterStatus = pill.getAttribute('data-status');
    renderInventoryTable(cachedCards);
  });

  // Initial Data Load
  loadTerminalData();
  loadSampleButtons();

  async function loadTerminalData() {
    try {
      const response = await fetch(`${API_BASE}/api/v1/clerk/records`);
      if (!response.ok) throw new Error('Failed to fetch records');
      const data = await response.json();

      // Render stats
      document.getElementById('statReady').textContent = data.stats.ready_for_collection;
      document.getElementById('statTransit').textContent = data.stats.in_transit;
      document.getElementById('statToday').textContent = data.stats.collected_today;
      document.getElementById('statTotal').textContent = data.stats.total_cards;

      // Update filter counts
      document.getElementById('countAll').textContent = data.stats.total_cards;
      document.getElementById('countReady').textContent = data.stats.ready_for_collection;
      document.getElementById('countTransit').textContent = data.stats.in_transit;
      document.getElementById('countCollected').textContent = data.stats.collected_total;

      // Render tables
      cachedCards = data.cards;
      renderInventoryTable(data.cards);
      renderAuditTable(data.recent_handovers);

    } catch (err) {
      console.error('Error loading terminal data:', err);
      showToast('Error connecting to counter service API.', 'error');
    }
  }

  async function loadSampleButtons() {
    try {
      const response = await fetch(`${API_BASE}/api/v1/citizens/samples`);
      if (!response.ok) return;
      const samples = await response.json();

      clerkSamplePills.innerHTML = samples.map(c => `
        <button type="button" class="sample-btn" data-id="${escapeHtml(c.fayda_id)}">
          <span>${escapeHtml(c.full_name.split(' ')[0])}</span>
          <span class="pill-tag">${escapeHtml(c.status === 'Ready for Collection' ? c.storage_bin : c.status)}</span>
        </button>
      `).join('');

      clerkSamplePills.querySelectorAll('.sample-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const id = btn.getAttribute('data-id');
          clerkSearchInput.value = id;
          fetchActiveCitizen(id);
        });
      });
    } catch (err) {
      console.error('Error fetching sample citizens:', err);
    }
  }

  async function fetchActiveCitizen(query) {
    if (!query) {
      showToast('Please enter a Fayda ID or Phone Number.', 'error');
      return;
    }

    try {
      const encoded = encodeURIComponent(query);
      const res = await fetch(`${API_BASE}/api/v1/track/${encoded}`);
      const card = await res.json();

      if (!res.ok) {
        showToast(card.detail || 'Citizen not found in records.', 'error');
        return;
      }

      currentActiveCard = card;
      displayActiveCard(card);
      showToast(`Loaded citizen: ${card.full_name}`, 'success');

    } catch (err) {
      console.error('Error fetching citizen:', err);
      showToast('Failed to fetch citizen record.', 'error');
    }
  }

  function displayActiveCard(card) {
    clerkEmptyState.style.display = 'none';
    activeHandoverBox.style.display = 'block';

    document.getElementById('activeStorageBin').textContent = card.storage_bin || 'Storage Bin Unassigned';
    document.getElementById('activeCitizenName').textContent = card.full_name;
    document.getElementById('activeFaydaId').textContent = `Fayda ID: ${card.fayda_id}`;
    document.getElementById('activePhone').textContent = card.phone_number;
    document.getElementById('activeDob').textContent = `${card.age} yrs (${card.date_of_birth})`;
    document.getElementById('activeAssignedDesk').textContent = card.assigned_desk || 'Not Assigned';
    document.getElementById('activeArrivedAt').textContent = card.arrived_at ? formatDate(card.arrived_at) : 'N/A';

    const statusPill = document.getElementById('activeStatusPill');
    statusPill.className = 'status-pill';

    if (card.status === 'Ready for Collection') {
      statusPill.classList.add('ready');
      statusPill.textContent = 'Ready for Collection';
      confirmHandoverBtn.disabled = false;
      confirmHandoverBtn.innerHTML = `<span>✓ Confirm Handover & Issue Card</span>`;
      confirmHandoverBtn.style.opacity = '1';
    } else if (card.status === 'In Transit') {
      statusPill.classList.add('transit');
      statusPill.textContent = 'In Transit';
      confirmHandoverBtn.disabled = true;
      confirmHandoverBtn.innerHTML = `<span>⏳ Cannot Issue: Card In Transit</span>`;
      confirmHandoverBtn.style.opacity = '0.6';
    } else if (card.status === 'Collected') {
      statusPill.classList.add('collected');
      statusPill.textContent = 'Already Collected';
      confirmHandoverBtn.disabled = true;
      confirmHandoverBtn.innerHTML = `<span>✓ Already Issued on ${formatDate(card.collected_at)}</span>`;
      confirmHandoverBtn.style.opacity = '0.6';
    }
  }

  async function processHandover() {
    if (!currentActiveCard) {
      showToast('No active citizen selected.', 'error');
      return;
    }

    if (currentActiveCard.status !== 'Ready for Collection') {
      showToast(`Cannot issue card: Status is currently "${currentActiveCard.status}".`, 'error');
      return;
    }

    const payload = {
      fayda_id: currentActiveCard.fayda_id,
      clerk_id: clerkSelect.value,
      desk_used: deskSelect.value
    };

    confirmHandoverBtn.disabled = true;
    confirmHandoverBtn.innerHTML = `<span>Issuing card...</span>`;

    try {
      const response = await fetch(`${API_BASE}/api/v1/handover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        showToast(data.detail || 'Failed to confirm handover.', 'error');
        confirmHandoverBtn.disabled = false;
        confirmHandoverBtn.innerHTML = `<span>✓ Confirm Handover & Issue Card</span>`;
        return;
      }

      showToast(`Success! Card issued to ${data.citizen_name}`, 'success');

      // Update current card view
      currentActiveCard.status = 'Collected';
      currentActiveCard.collected_at = data.collected_at;
      displayActiveCard(currentActiveCard);

      // Refresh master tables and live stats
      await loadTerminalData();

    } catch (err) {
      console.error('Handover error:', err);
      showToast('Handover network error. Please retry.', 'error');
      confirmHandoverBtn.disabled = false;
      confirmHandoverBtn.innerHTML = `<span>✓ Confirm Handover & Issue Card</span>`;
    }
  }

  function renderInventoryTable(cards) {
    const tbody = document.getElementById('inventoryTableBody');

    const filtered = currentFilterStatus === 'All'
      ? cards
      : cards.filter(c => c.status === currentFilterStatus);

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:2rem; color:#94a3b8;">No cards found for filter "${escapeHtml(currentFilterStatus)}".</td></tr>`;
      return;
    }

    tbody.innerHTML = filtered.map(c => {
      let statusClass = 'transit';
      if (c.status === 'Ready for Collection') statusClass = 'ready';
      if (c.status === 'Collected') statusClass = 'collected';

      return `
        <tr>
          <td><strong style="font-family: monospace;">${escapeHtml(c.fayda_id)}</strong></td>
          <td><strong>${escapeHtml(c.full_name)}</strong></td>
          <td>${escapeHtml(c.phone_number)}</td>
          <td>
            <span style="background: #fef3c7; color: #78350f; font-family: monospace; font-weight:700; padding: 2px 6px; border-radius: 4px; border: 1px solid #fde68a;">
              📦 ${escapeHtml(c.storage_bin)}
            </span>
          </td>
          <td>
            <span class="status-pill ${statusClass}" style="font-size:0.75rem; padding: 2px 8px;">
              ${escapeHtml(c.status)}
            </span>
          </td>
          <td style="font-size:0.8rem; color:#1d4ed8; font-weight:600;">
            ${escapeHtml(c.assigned_desk || '-')}
          </td>
          <td>
            <button type="button" class="sample-btn select-row-btn" data-id="${escapeHtml(c.fayda_id)}">
              Select
            </button>
          </td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('.select-row-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-id');
        clerkSearchInput.value = id;
        fetchActiveCitizen(id);
        window.scrollTo({ top: 120, behavior: 'smooth' });
      });
    });
  }

  function renderAuditTable(logs) {
    const tbody = document.getElementById('auditTableBody');

    if (!logs || logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2rem; color: #94a3b8;">No handovers recorded yet today.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(log => `
      <tr>
        <td style="font-size: 0.8rem; color: #64748b; font-family: monospace;">
          ${formatDate(log.timestamp)}
        </td>
        <td><strong>${escapeHtml(log.citizen_name)}</strong></td>
        <td style="font-family: monospace; font-size: 0.8rem;">${escapeHtml(log.fayda_id)}</td>
        <td style="font-size: 0.8rem; color: #1d4ed8; font-weight:600;">${escapeHtml(log.desk_used)}</td>
        <td style="font-size: 0.8rem; font-weight:600; color: #047857;">${escapeHtml(log.clerk_id)}</td>
      </tr>
    `).join('');
  }

  function formatDate(isoStr) {
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
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
