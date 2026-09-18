/**
 * Fayda Postal Counter Terminal Logic (Staff Portal)
 * Handles storage bin physical retrieval, visual rack locator, digital ID verification,
 * live handover issuing, receipt modal printing, and inventory management.
 */

// Dynamic API Base:
// - In local separate-port mode (port 3000 / 4000), target localhost:8000
// - On Render / production (or unified port 8000), use relative path ''
const API_BASE = (window.location.port === '3000' || window.location.port === '4000')
  ? (window.location.hostname === '127.0.0.1' ? 'http://127.0.0.1:8000' : 'http://localhost:8000')
  : '';

let currentActiveCard = null;
let currentFilterStatus = 'All';
let cachedCards = [];

document.addEventListener('DOMContentLoaded', () => {
  // 1. Authentication Guard
  const rawAuth = sessionStorage.getItem('fayda_clerk_auth');
  if (!rawAuth) {
    window.location.href = 'index.html';
    return;
  }

  let authData = {};
  try {
    authData = JSON.parse(rawAuth);
  } catch (err) {
    sessionStorage.removeItem('fayda_clerk_auth');
    window.location.href = 'index.html';
    return;
  }

  // 2. Populate Authenticated User Info in Header
  const clerkSessionName = document.getElementById('clerkSessionName');
  const clerkSessionDesk = document.getElementById('clerkSessionDesk');
  const clerkLogoutBtn = document.getElementById('clerkLogoutBtn');
  const navKioskLink = document.getElementById('navKioskLink');

  if (clerkSessionName && authData.clerk_name) {
    clerkSessionName.textContent = authData.clerk_name;
  }
  if (clerkSessionDesk && authData.desk) {
    const shortDesk = authData.desk.includes('Desk 1') ? 'Desk 1 (Priority)' 
                    : (authData.desk.includes('Desk 2') ? 'Desk 2' 
                    : (authData.desk.includes('Desk 3') ? 'Desk 3' : authData.desk));
    clerkSessionDesk.textContent = shortDesk;
  }

  // Dynamic Kiosk View link
  if (navKioskLink) {
    if (window.location.port === '4000') {
      navKioskLink.href = `${window.location.protocol}//${window.location.hostname}:3000`;
    } else {
      navKioskLink.href = '../kiosk/';
    }
  }

  // Live Digital Clock
  function updateClock() {
    const clockEl = document.getElementById('liveClock');
    if (!clockEl) return;
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
    clockEl.textContent = `🕒 ${timeStr} (EAT)`;
  }
  setInterval(updateClock, 1000);
  updateClock();

  // Handle Logout
  if (clerkLogoutBtn) {
    clerkLogoutBtn.addEventListener('click', () => {
      sessionStorage.removeItem('fayda_clerk_auth');
      showToast('Logged out of counter terminal.', 'info');
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 400);
    });
  }

  // 3. Elements
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
  const inventorySearchInput = document.getElementById('inventorySearchInput');
  const receiptModal = document.getElementById('receiptModal');
  const printReceiptBtn = document.getElementById('printReceiptBtn');
  const closeReceiptBtn = document.getElementById('closeReceiptBtn');

  // Receipt Modal Actions
  if (printReceiptBtn) {
    printReceiptBtn.addEventListener('click', () => {
      window.print();
    });
  }
  if (closeReceiptBtn) {
    closeReceiptBtn.addEventListener('click', () => {
      receiptModal.style.display = 'none';
      clerkSearchInput.focus();
    });
  }

  // Sync selected desk and clerk with auth
  if (deskSelect && authData.desk) {
    deskSelect.value = authData.desk;
  }
  if (clerkSelect && authData.clerk_id) {
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
    applyInventoryFilter();
  });

  // Real-time Inventory Table Search Filter
  if (inventorySearchInput) {
    inventorySearchInput.addEventListener('input', applyInventoryFilter);
  }

  function applyInventoryFilter() {
    const q = inventorySearchInput ? inventorySearchInput.value.trim().toLowerCase() : '';
    let list = cachedCards;

    if (currentFilterStatus !== 'All') {
      list = list.filter(c => c.status === currentFilterStatus);
    }

    if (q) {
      list = list.filter(c => 
        c.full_name.toLowerCase().includes(q) ||
        c.fayda_id.toLowerCase().includes(q) ||
        c.phone_number.toLowerCase().includes(q) ||
        (c.storage_bin && c.storage_bin.toLowerCase().includes(q))
      );
    }

    renderInventoryTable(list);
  }

  // Initial Data Load
  loadTerminalData();
  loadSampleButtons();

  async function loadTerminalData() {
    refreshAuditBtn.classList.add('loading');
    try {
      const res = await fetch(`${API_BASE}/api/v1/clerk/records`);
      if (!res.ok) throw new Error('Failed to fetch records');
      const data = await res.json();

      cachedCards = data.cards || [];
      renderStats(data.stats);
      renderAuditTable(data.recent_handovers);
      applyInventoryFilter();

    } catch (err) {
      console.error('Terminal load error:', err);
      showToast('Could not load postal branch records.', 'error');
    } finally {
      refreshAuditBtn.classList.remove('loading');
    }
  }

  async function loadSampleButtons() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/citizens/samples`);
      if (!res.ok) return;
      const samples = await res.json();

      clerkSamplePills.innerHTML = samples.map(s => {
        let label = s.status;
        let styleBadge = 'background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe;';

        if (s.status === 'Ready for Collection') {
          if (s.age >= 60) {
            label = 'Senior Desk 1';
            styleBadge = 'background:#fef3c7; color:#92400e; border:1px solid #f59e0b;';
          } else if (s.storage_bin && s.storage_bin.includes('Shelf A')) {
            label = 'Shelf A (Desk 2)';
            styleBadge = 'background:#eff6ff; color:#1d4ed8; border:1px solid #93c5fd;';
          } else {
            label = 'Shelf B (Desk 3)';
            styleBadge = 'background:#f5f3ff; color:#6d28d9; border:1px solid #c4b5fd;';
          }
        } else if (s.status === 'In Transit') {
          label = 'In Transit';
          styleBadge = 'background:#fffbeb; color:#b45309; border:1px solid #fde68a;';
        } else if (s.status === 'Collected') {
          label = 'Collected';
          styleBadge = 'background:#f1f5f9; color:#475569; border:1px solid #cbd5e1;';
        }

        return `
          <button type="button" class="sample-btn" data-id="${escapeHtml(s.fayda_id)}">
            <span>${escapeHtml(s.full_name.split(' ')[0])}</span>
            <span class="pill-tag" style="${styleBadge}">${escapeHtml(label)}</span>
          </button>
        `;
      }).join('');

      clerkSamplePills.querySelectorAll('.sample-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          clerkSamplePills.querySelectorAll('.sample-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const id = btn.getAttribute('data-id');
          clerkSearchInput.value = id;
          fetchActiveCitizen(id);
        });
      });
    } catch (e) {
      console.warn('Sample buttons load error:', e);
    }
  }

  function renderStats(stats) {
    if (!stats) return;
    document.getElementById('statReady').textContent = stats.ready_for_collection;
    document.getElementById('statTransit').textContent = stats.in_transit;
    document.getElementById('statToday').textContent = stats.collected_today;
    document.getElementById('statTotal').textContent = stats.total_cards;
  }

  async function fetchActiveCitizen(query) {
    if (!query) {
      showToast('Please enter a Fayda ID or Phone Number to search.', 'error');
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
      showToast(`Loaded: ${card.full_name}`, 'success');

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
    document.getElementById('activeDeskDisplay').textContent = card.assigned_desk || 'Not Assigned';
    document.getElementById('activeArrivedAt').textContent = card.arrived_at ? formatDate(card.arrived_at) : 'N/A';

    const statusPill = document.getElementById('activeStatusPill');
    statusPill.className = 'status-pill';

    if (card.status === 'Ready for Collection') {
      statusPill.classList.add('ready');
      statusPill.textContent = 'Ready for Collection';
      confirmHandoverBtn.disabled = false;
      confirmHandoverBtn.innerHTML = `<span>✓ Confirm Handover & Issue Official Receipt</span>`;
      confirmHandoverBtn.style.opacity = '1';
    } else if (card.status === 'In Transit') {
      statusPill.classList.add('transit');
      statusPill.textContent = 'In Transit';
      confirmHandoverBtn.disabled = true;
      confirmHandoverBtn.innerHTML = `<span>⏳ Cannot Issue: Card In Transit from Hub</span>`;
      confirmHandoverBtn.style.opacity = '0.6';
    } else if (card.status === 'Collected') {
      statusPill.classList.add('collected');
      statusPill.textContent = 'Already Collected';
      confirmHandoverBtn.disabled = true;
      confirmHandoverBtn.innerHTML = `<span>✓ Card Already Handed Over on ${formatDate(card.collected_at)}</span>`;
      confirmHandoverBtn.style.opacity = '0.6';
    }

    // Highlight Physical Storage Rack Diagram
    highlightStorageRack(card.storage_bin);
  }

  function highlightStorageRack(binStr) {
    const podA = document.getElementById('rackPodA');
    const podB = document.getElementById('rackPodB');
    const badge = document.getElementById('rackTargetBadge');

    if (podA) podA.classList.remove('active-rack');
    if (podB) podB.classList.remove('active-rack');
    document.querySelectorAll('.box-cell').forEach(c => c.classList.remove('active-box'));

    if (!binStr || binStr === 'Storage Bin Unassigned' || binStr.includes('Unassigned')) {
      if (badge) badge.textContent = 'Bin Unassigned';
      return;
    }

    const isShelfA = binStr.toLowerCase().includes('shelf a');
    const isShelfB = binStr.toLowerCase().includes('shelf b');

    let activePod = null;
    if (isShelfA && podA) {
      podA.classList.add('active-rack');
      activePod = podA;
    } else if (isShelfB && podB) {
      podB.classList.add('active-rack');
      activePod = podB;
    }

    const boxMatch = binStr.match(/Box\s*(\d+)/i);
    if (boxMatch && activePod) {
      const boxNum = boxMatch[1].padStart(2, '0');
      const boxTag = `Box ${boxNum}`;
      const targetCell = activePod.querySelector(`.box-cell[data-box="${boxTag}"]`);
      if (targetCell) {
        targetCell.classList.add('active-box');
      }
      if (badge) {
        badge.textContent = `➔ LOCATE ${isShelfA ? 'SHELF A' : 'SHELF B'} / BOX ${boxNum}`;
      }
    } else if (badge) {
      badge.textContent = binStr;
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

    const clerkId = clerkSelect.value;
    const deskUsed = deskSelect.value;

    confirmHandoverBtn.disabled = true;
    confirmHandoverBtn.innerHTML = `<span>Processing Handover & Recording Audit...</span>`;

    try {
      const res = await fetch(`${API_BASE}/api/v1/handover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fayda_id: currentActiveCard.fayda_id,
          clerk_id: clerkId,
          desk_used: deskUsed
        })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Handover failed');
      }

      showToast(`Success! Fayda Card issued to ${data.citizen_name}.`, 'success');

      // Refresh active card view to Collected
      currentActiveCard.status = 'Collected';
      currentActiveCard.collected_at = data.collected_at;
      displayActiveCard(currentActiveCard);

      // Trigger Official Receipt Slip Modal
      showReceiptModal(currentActiveCard, data, clerkId, deskUsed);

      // Reload live stats and audit trail
      loadTerminalData();

    } catch (err) {
      console.error('Handover error:', err);
      showToast(err.message, 'error');
      confirmHandoverBtn.disabled = false;
      confirmHandoverBtn.innerHTML = `<span>✓ Confirm Handover & Issue Official Receipt</span>`;
    }
  }

  function showReceiptModal(card, data, clerkId, deskUsed) {
    if (!receiptModal) return;
    const randNum = Math.floor(1000 + Math.random() * 9000);
    document.getElementById('receiptCode').textContent = `RCP-ADAMA-${randNum}`;
    document.getElementById('receiptCitizenName').textContent = card.full_name;
    document.getElementById('receiptFaydaId').textContent = card.fayda_id;
    document.getElementById('receiptPhone').textContent = card.phone_number;
    document.getElementById('receiptDesk').textContent = deskUsed;
    document.getElementById('receiptClerk').textContent = clerkId;
    document.getElementById('receiptTime').textContent = new Date().toLocaleString();

    receiptModal.style.display = 'flex';
  }

  function renderInventoryTable(cards) {
    const tbody = document.getElementById('inventoryTableBody');
    if (!cards || cards.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:2.5rem; color:#94a3b8; font-weight:600;">No registry records match your criteria.</td></tr>`;
      return;
    }

    tbody.innerHTML = cards.map(c => {
      let statusClass = 'transit';
      if (c.status === 'Ready for Collection') statusClass = 'ready';
      if (c.status === 'Collected') statusClass = 'collected';

      return `
        <tr>
          <td><strong style="font-family: 'JetBrains Mono', monospace; font-size:0.85rem; color:#0f172a;">${escapeHtml(c.fayda_id)}</strong></td>
          <td><strong style="color:#1e293b;">${escapeHtml(c.full_name)}</strong></td>
          <td style="font-family: 'JetBrains Mono', monospace; font-size:0.82rem; color:#475569;">${escapeHtml(c.phone_number)}</td>
          <td>
            <span style="background: #fef3c7; color: #78350f; font-family: 'JetBrains Mono', monospace; font-weight:800; padding: 3px 8px; border-radius: 6px; border: 1px solid #fde68a; font-size:0.8rem; display:inline-flex; align-items:center; gap:0.3rem;">
              📦 ${escapeHtml(c.storage_bin)}
            </span>
          </td>
          <td>
            <span class="status-pill ${statusClass}" style="font-size:0.75rem; padding: 3px 9px;">
              ${escapeHtml(c.status)}
            </span>
          </td>
          <td style="font-size:0.82rem; color:#1d4ed8; font-weight:700;">
            ${escapeHtml(c.assigned_desk || '-')}
          </td>
          <td>
            <button type="button" class="btn-secondary-action select-row-btn" data-id="${escapeHtml(c.fayda_id)}" style="padding: 0.35rem 0.75rem; font-size: 0.78rem;">
              ⚡ Retrieve
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
        window.scrollTo({ top: 180, behavior: 'smooth' });
      });
    });
  }

  function renderAuditTable(logs) {
    const tbody = document.getElementById('auditTableBody');

    if (!logs || logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2.5rem; color: #94a3b8; font-weight:600;">No handovers recorded yet today.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(log => `
      <tr>
        <td style="font-size: 0.8rem; color: #64748b; font-family: 'JetBrains Mono', monospace; font-weight:600;">
          ${formatDate(log.timestamp)}
        </td>
        <td><strong style="color:#0f172a;">${escapeHtml(log.citizen_name)}</strong></td>
        <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color:#475569;">${escapeHtml(log.fayda_id)}</td>
        <td style="font-size: 0.8rem; color: #1d4ed8; font-weight:700;">${escapeHtml(log.desk_used)}</td>
        <td>
          <span style="background:#ecfdf5; color:#047857; font-weight:800; font-size:0.75rem; padding:2px 7px; border-radius:4px; border:1px solid #a7f3d0;">
            ${escapeHtml(log.clerk_id)}
          </span>
        </td>
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
      <span>${type === 'error' ? '⚠️' : (type === 'info' ? 'ℹ️' : '✓')}</span>
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
