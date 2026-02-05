import { w as head, x as ensure_array_like, y as attr } from "../../../chunks/index2.js";
import { e as escape_html } from "../../../chunks/context.js";
const BASE_URL = "/api";
async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const config = {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers
    }
  };
  const response = await fetch(url, config);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unbekannter Fehler" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}
const documents = {
  list: (docType) => {
    const params = docType ? `?doc_type=${docType}` : "";
    return request(`/documents/${params}`);
  },
  get: (id) => request(`/documents/${id}`),
  createLetter: (data) => request("/documents/letter", {
    method: "POST",
    body: JSON.stringify(data)
  }),
  createInvoice: (data) => request("/documents/invoice", {
    method: "POST",
    body: JSON.stringify(data)
  }),
  createOffer: (data) => request("/documents/offer", {
    method: "POST",
    body: JSON.stringify(data)
  }),
  archive: (id) => request(`/documents/${id}/archive`, {
    method: "POST"
  }),
  delete: (id) => request(`/documents/${id}`, {
    method: "DELETE"
  }),
  getPdfUrl: (id) => `${BASE_URL}/documents/${id}/pdf`
};
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let docList = [];
    let loading = true;
    let error = "";
    let filter = "";
    async function loadDocuments() {
      loading = true;
      try {
        docList = await documents.list(filter || void 0);
      } catch (e) {
        error = e instanceof Error ? e.message : "Fehler beim Laden";
      } finally {
        loading = false;
      }
    }
    function formatDate(dateStr) {
      return new Date(dateStr).toLocaleDateString("de-DE");
    }
    function formatCurrency(amount) {
      if (amount === null) return "-";
      return new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(amount);
    }
    function getDocTypeLabel(type) {
      const labels = { letter: "Brief", invoice: "Rechnung", offer: "Angebot" };
      return labels[type] || type;
    }
    function applyFilter() {
      loadDocuments();
    }
    head("220hbx", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Dokumente - Korrespondenz</title>`);
      });
    });
    $$renderer2.push(`<div class="documents-page"><div class="flex-between mb-3"><h1 class="svelte-220hbx">Dokumente</h1> <div class="flex gap-1"><a href="/documents/letter" class="btn btn-primary">+ Brief</a> <a href="/documents/invoice" class="btn btn-primary">+ Rechnung</a> <a href="/documents/offer" class="btn btn-primary">+ Angebot</a></div></div> `);
    if (error) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="alert alert-error">${escape_html(error)}</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="card mb-2"><div class="flex gap-1">`);
    $$renderer2.select(
      {
        class: "form-select",
        style: "width: auto;",
        value: filter,
        onchange: applyFilter
      },
      ($$renderer3) => {
        $$renderer3.option({ value: "" }, ($$renderer4) => {
          $$renderer4.push(`Alle Typen`);
        });
        $$renderer3.option({ value: "letter" }, ($$renderer4) => {
          $$renderer4.push(`Briefe`);
        });
        $$renderer3.option({ value: "invoice" }, ($$renderer4) => {
          $$renderer4.push(`Rechnungen`);
        });
        $$renderer3.option({ value: "offer" }, ($$renderer4) => {
          $$renderer4.push(`Angebote`);
        });
      }
    );
    $$renderer2.push(`</div></div> `);
    if (loading) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center mt-3"><span class="loading"></span></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      if (docList.length === 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="card text-center"><p class="text-muted">Keine Dokumente gefunden.</p></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="card"><table class="table"><thead><tr><th>Nummer</th><th>Typ</th><th>Betreff</th><th>Datum</th><th>Betrag</th><th>Status</th><th></th></tr></thead><tbody><!--[-->`);
        const each_array = ensure_array_like(docList);
        for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
          let doc = each_array[$$index];
          $$renderer2.push(`<tr><td><strong>${escape_html(doc.doc_number)}</strong></td><td><span class="badge badge-primary">${escape_html(getDocTypeLabel(doc.doc_type))}</span></td><td>${escape_html(doc.subject || "-")}</td><td>${escape_html(formatDate(doc.doc_date))}</td><td>${escape_html(formatCurrency(doc.gross_total))}</td><td>`);
          if (doc.status === "archived") {
            $$renderer2.push("<!--[-->");
            $$renderer2.push(`<span class="badge badge-success">Archiviert</span>`);
          } else {
            $$renderer2.push("<!--[!-->");
            $$renderer2.push(`<span class="badge badge-secondary">${escape_html(doc.status)}</span>`);
          }
          $$renderer2.push(`<!--]--></td><td class="text-right"><div class="flex gap-1" style="justify-content: flex-end;"><a${attr("href", documents.getPdfUrl(doc.id))} target="_blank" class="btn btn-secondary btn-sm">PDF</a> `);
          if (doc.status !== "archived") {
            $$renderer2.push("<!--[-->");
            $$renderer2.push(`<button class="btn btn-success btn-sm">Archivieren</button>`);
          } else {
            $$renderer2.push("<!--[!-->");
          }
          $$renderer2.push(`<!--]--> <button class="btn btn-danger btn-sm">Löschen</button></div></td></tr>`);
        }
        $$renderer2.push(`<!--]--></tbody></table></div>`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
