/* global apiFetch, formatMoney, getGoogleLoginUrl, getToken, setToken, clearToken */

const els = {
  tbody: document.getElementById("poTbody"),
  loadingRow: document.getElementById("loadingRow"),
  errorBox: document.getElementById("errorBox"),
  infoBox: document.getElementById("infoBox"),
  btnRefresh: document.getElementById("btnRefresh"),
  btnLogin: document.getElementById("btnLogin"),
  btnLogout: document.getElementById("btnLogout"),

  modalEl: document.getElementById("poModal"),
  modalTitle: document.getElementById("poModalTitle"),
  modalError: document.getElementById("poModalError"),
  vendorName: document.getElementById("poVendorName"),
  vendorMeta: document.getElementById("poVendorMeta"),
  subtotal: document.getElementById("poSubtotal"),
  tax: document.getElementById("poTax"),
  total: document.getElementById("poTotal"),
  itemsTbody: document.getElementById("poItemsTbody"),
};

function showError(msg) {
  els.errorBox.textContent = msg;
  els.errorBox.classList.remove("d-none");
}

function clearError() {
  els.errorBox.classList.add("d-none");
  els.errorBox.textContent = "";
}

function showInfo(msg) {
  els.infoBox.textContent = msg;
  els.infoBox.classList.remove("d-none");
}

function clearInfo() {
  els.infoBox.classList.add("d-none");
  els.infoBox.textContent = "";
}

function captureTokenFromUrl() {
  const url = new URL(window.location.href);
  const token = url.searchParams.get("token");
  if (!token) return false;
  setToken(token);
  url.searchParams.delete("token");
  window.history.replaceState({}, document.title, url.toString());
  return true;
}

function syncAuthUi() {
  const token = getToken();
  const loggedIn = Boolean(token);
  els.btnLogout.classList.toggle("d-none", !loggedIn);
  els.btnLogin.classList.toggle("d-none", loggedIn);
  els.btnLogin.href = getGoogleLoginUrl(window.location.href);
  return loggedIn;
}

function fmtDate(iso) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso || "—";
  }
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderRows(pos) {
  els.tbody.innerHTML = "";
  if (!pos.length) {
    els.tbody.innerHTML = `<tr><td colspan="8" class="text-center muted py-4">No purchase orders yet.</td></tr>`;
    return;
  }

  for (const po of pos) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="mono">${po.reference_no || `PO#${po.id}`}</td>
      <td>${escapeHtml(fmtDate(po.created_at))}</td>
      <td><span class="badge badge-soft">Vendor #${po.vendor_id}</span></td>
      <td><span class="badge text-bg-light">${escapeHtml(po.status || "—")}</span></td>
      <td class="text-end mono">${formatMoney(po.subtotal)}</td>
      <td class="text-end mono">${formatMoney(po.tax)}</td>
      <td class="text-end mono fw-semibold">${formatMoney(po.total_amount ?? po.total)}</td>
      <td class="text-end">
        <button class="btn btn-outline-primary btn-sm" data-action="view" data-id="${po.id}">View</button>
      </td>
    `;
    els.tbody.appendChild(tr);
  }
}

async function loadPOs() {
  clearError();
  clearInfo();
  els.tbody.innerHTML = `<tr><td colspan="7" class="text-center muted py-4">Loading…</td></tr>`;
  try {
    const pos = await apiFetch("/purchase-orders");
    renderRows(pos);
  } catch (e) {
    showError(e.message || "Failed to load purchase orders");
    els.tbody.innerHTML = "";
  }
}

function modalSetError(msg) {
  els.modalError.textContent = msg;
  els.modalError.classList.remove("d-none");
}

function modalClearError() {
  els.modalError.textContent = "";
  els.modalError.classList.add("d-none");
}

function renderPODetail(po) {
  els.modalTitle.textContent = `PO #${po.id}`;
  els.vendorName.textContent = po.vendor?.name || `Vendor #${po.vendor_id}`;
  const metaParts = [];
  if (po.vendor?.email) metaParts.push(po.vendor.email);
  if (po.vendor?.phone) metaParts.push(po.vendor.phone);
  els.vendorMeta.textContent = metaParts.join(" • ");

  els.subtotal.textContent = formatMoney(po.subtotal);
  els.tax.textContent = formatMoney(po.tax);
  els.total.textContent = formatMoney(po.total);

  els.itemsTbody.innerHTML = "";
  for (const item of po.items || []) {
    const name = item.product ? `${item.product.sku} — ${item.product.name}` : `Product #${item.product_id}`;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(name)}</td>
      <td class="text-end mono">${formatMoney(item.unit_price)}</td>
      <td class="text-end mono">${item.quantity}</td>
      <td class="text-end mono fw-semibold">${formatMoney(item.line_total)}</td>
    `;
    els.itemsTbody.appendChild(tr);
  }
}

async function openPOModal(poId) {
  modalClearError();
  els.modalTitle.textContent = `PO #${poId}`;
  els.vendorName.textContent = "Loading…";
  els.vendorMeta.textContent = "";
  els.subtotal.textContent = "—";
  els.tax.textContent = "—";
  els.total.textContent = "—";
  els.itemsTbody.innerHTML = `<tr><td colspan="4" class="text-center muted py-3">Loading…</td></tr>`;

  const modal = bootstrap.Modal.getOrCreateInstance(els.modalEl);
  modal.show();

  try {
    const po = await apiFetch(`/purchase-orders/${poId}`);
    renderPODetail(po);
  } catch (e) {
    modalSetError(e.message || "Failed to load PO details");
    els.itemsTbody.innerHTML = "";
  }
}

els.btnRefresh.addEventListener("click", () => loadPOs());

els.btnLogout.addEventListener("click", () => {
  clearToken();
  syncAuthUi();
  showInfo("Logged out. Click “Login with Google” to access Purchase Orders.");
  els.tbody.innerHTML = `<tr><td colspan="8" class="text-center muted py-4">Login required.</td></tr>`;
});

els.tbody.addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-action]");
  if (!btn) return;
  if (btn.dataset.action === "view") openPOModal(btn.dataset.id);
});

captureTokenFromUrl();
const loggedIn = syncAuthUi();
if (!loggedIn) {
  showInfo("Login required to view Purchase Orders. Click “Login with Google”.");
  els.tbody.innerHTML = `<tr><td colspan="8" class="text-center muted py-4">Login required.</td></tr>`;
} else {
  loadPOs();
}

