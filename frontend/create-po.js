/* global apiFetch, formatMoney, toNumber, getGoogleLoginUrl, getToken, setToken, clearToken */

const TAX_RATE = 0.05;

const els = {
  vendorSelect: document.getElementById("vendorSelect"),
  itemsTbody: document.getElementById("itemsTbody"),
  btnAddRow: document.getElementById("btnAddRow"),
  poForm: document.getElementById("poForm"),
  btnSubmit: document.getElementById("btnSubmit"),
  errorBox: document.getElementById("errorBox"),
  successBox: document.getElementById("successBox"),
  infoBox: document.getElementById("infoBox"),
  btnLogin: document.getElementById("btnLogin"),
  btnLogout: document.getElementById("btnLogout"),
  subtotalText: document.getElementById("subtotalText"),
  taxText: document.getElementById("taxText"),
  totalText: document.getElementById("totalText"),
  rowTemplate: document.getElementById("rowTemplate"),
  descModal: document.getElementById("descModal"),
  descModalTitle: document.getElementById("descModalTitle"),
  descModalError: document.getElementById("descModalError"),
  descProductName: document.getElementById("descProductName"),
  descText: document.getElementById("descText"),
};

let products = [];
let productsById = new Map();

function showError(msg) {
  els.errorBox.textContent = msg;
  els.errorBox.classList.remove("d-none");
}

function clearError() {
  els.errorBox.classList.add("d-none");
  els.errorBox.textContent = "";
}

function showSuccess(msg) {
  els.successBox.textContent = msg;
  els.successBox.classList.remove("d-none");
}

function clearSuccess() {
  els.successBox.classList.add("d-none");
  els.successBox.textContent = "";
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

function buildProductOptions(selectEl, selectedId = "") {
  selectEl.innerHTML = `<option value="">Select product…</option>`;
  for (const p of products) {
    const opt = document.createElement("option");
    opt.value = String(p.id);
    opt.textContent = `${p.sku} — ${p.name}`;
    if (String(p.id) === String(selectedId)) opt.selected = true;
    selectEl.appendChild(opt);
  }
}

function getRowEls(tr) {
  return {
    tr,
    productSelect: tr.querySelector(".product-select"),
    qty: tr.querySelector(".qty"),
    unitPrice: tr.querySelector(".unit-price"),
    lineTotal: tr.querySelector(".line-total"),
    genDescBtn: tr.querySelector(".gen-desc"),
    removeBtn: tr.querySelector(".remove-row"),
  };
}

function computeLineTotal(productId, qty) {
  const p = productsById.get(Number(productId));
  const price = p ? toNumber(p.price) : 0;
  return price * toNumber(qty);
}

function updateRow(tr) {
  const { productSelect, qty, unitPrice, lineTotal, genDescBtn } = getRowEls(tr);
  const p = productsById.get(Number(productSelect.value));
  const price = p ? toNumber(p.price) : 0;
  unitPrice.value = formatMoney(price);

  const lt = computeLineTotal(productSelect.value, qty.value);
  lineTotal.textContent = formatMoney(lt);

  genDescBtn.disabled = !productSelect.value;
}

function descModalSetError(msg) {
  els.descModalError.textContent = msg;
  els.descModalError.classList.remove("d-none");
}

function descModalClearError() {
  els.descModalError.textContent = "";
  els.descModalError.classList.add("d-none");
}

async function openDescriptionModal(productId) {
  const p = productsById.get(Number(productId));
  const name = p ? `${p.sku} — ${p.name}` : `Product #${productId}`;

  els.descModalTitle.textContent = "Generated Description";
  els.descProductName.textContent = name;
  els.descText.textContent = "Generating…";
  descModalClearError();

  const modal = bootstrap.Modal.getOrCreateInstance(els.descModal);
  modal.show();

  try {
    const res = await apiFetch(`/products/${productId}/generate-description`, { method: "POST" });
    els.descText.textContent = res.description || "";
  } catch (e) {
    els.descText.textContent = "";
    descModalSetError(e.message || "Failed to generate description");
  }
}

function recalcTotals() {
  let subtotal = 0;
  for (const tr of els.itemsTbody.querySelectorAll("tr")) {
    const { productSelect, qty } = getRowEls(tr);
    if (!productSelect.value) continue;
    subtotal += computeLineTotal(productSelect.value, qty.value);
  }

  const tax = subtotal * TAX_RATE;
  const total = subtotal + tax;

  els.subtotalText.textContent = formatMoney(subtotal);
  els.taxText.textContent = formatMoney(tax);
  els.totalText.textContent = formatMoney(total);
}

function addRow({ productId = "", quantity = 1 } = {}) {
  const frag = els.rowTemplate.content.cloneNode(true);
  const tr = frag.querySelector("tr");
  const row = getRowEls(tr);
  buildProductOptions(row.productSelect, productId);
  row.qty.value = String(quantity);

  // initial calc
  updateRow(tr);
  recalcTotals();

  els.itemsTbody.appendChild(tr);
}

function removeRow(tr) {
  tr.remove();
  if (!els.itemsTbody.querySelector("tr")) addRow();
  recalcTotals();
}

function getPayload() {
  const vendorId = Number(els.vendorSelect.value);
  if (!vendorId) throw new Error("Please select a vendor");

  const items = [];
  for (const tr of els.itemsTbody.querySelectorAll("tr")) {
    const { productSelect, qty } = getRowEls(tr);
    const productId = Number(productSelect.value);
    const quantity = Number(qty.value);
    if (!productId) continue;
    if (!Number.isFinite(quantity) || quantity <= 0) throw new Error("Quantity must be greater than 0");
    items.push({ product_id: productId, quantity });
  }

  if (!items.length) throw new Error("Add at least one product row");
  return { vendor_id: vendorId, items };
}

async function loadVendors() {
  els.vendorSelect.innerHTML = `<option value="">Loading…</option>`;
  const vendors = await apiFetch("/vendors");
  els.vendorSelect.innerHTML = `<option value="">Select vendor…</option>`;
  for (const v of vendors) {
    const opt = document.createElement("option");
    opt.value = String(v.id);
    opt.textContent = `${v.name}${v.email ? ` (${v.email})` : ""}`;
    els.vendorSelect.appendChild(opt);
  }
}

async function loadProducts() {
  products = await apiFetch("/products");
  productsById = new Map(products.map((p) => [Number(p.id), p]));
}

async function init() {
  clearError();
  clearSuccess();
  clearInfo();
  els.btnSubmit.disabled = true;

  try {
    await Promise.all([loadProducts(), loadVendors()]);

    // Ensure at least one row exists
    els.itemsTbody.innerHTML = "";
    addRow();
    els.btnSubmit.disabled = !getToken();
    if (!getToken()) {
      showInfo("Login required to create Purchase Orders. Click “Login with Google”.");
    }
  } catch (e) {
    showError(e.message || "Failed to load vendors/products");
  }
}

els.btnAddRow.addEventListener("click", () => addRow());

els.itemsTbody.addEventListener("change", (ev) => {
  const tr = ev.target.closest("tr");
  if (!tr) return;
  if (ev.target.classList.contains("product-select") || ev.target.classList.contains("qty")) {
    updateRow(tr);
    recalcTotals();
  }
});

els.itemsTbody.addEventListener("input", (ev) => {
  const tr = ev.target.closest("tr");
  if (!tr) return;
  if (ev.target.classList.contains("qty")) {
    updateRow(tr);
    recalcTotals();
  }
});

els.itemsTbody.addEventListener("click", (ev) => {
  const gen = ev.target.closest("button.gen-desc");
  if (gen) {
    const tr = gen.closest("tr");
    const { productSelect } = getRowEls(tr);
    if (!productSelect.value) return;
    openDescriptionModal(productSelect.value);
    return;
  }

  const btn = ev.target.closest("button.remove-row");
  if (!btn) return;
  const tr = btn.closest("tr");
  removeRow(tr);
});

els.poForm.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  clearError();
  clearSuccess();
  clearInfo();

  if (!getToken()) {
    showInfo("Login required. Click “Login with Google”.");
    return;
  }

  let payload;
  try {
    payload = getPayload();
  } catch (e) {
    showError(e.message);
    return;
  }

  els.btnSubmit.disabled = true;
  els.btnSubmit.textContent = "Creating…";

  try {
    const created = await apiFetch("/purchase-orders", { method: "POST", body: payload });
    showSuccess(`PO #${created.id} created successfully.`);

    // reset form
    els.vendorSelect.value = "";
    els.itemsTbody.innerHTML = "";
    addRow();
  } catch (e) {
    showError(e.message || "Failed to create purchase order");
  } finally {
    els.btnSubmit.disabled = false;
    els.btnSubmit.textContent = "Create PO";
    recalcTotals();
  }
});

els.btnLogout.addEventListener("click", () => {
  clearToken();
  syncAuthUi();
  els.btnSubmit.disabled = true;
  showInfo("Logged out. Click “Login with Google” to create Purchase Orders.");
});

captureTokenFromUrl();
syncAuthUi();
init();

