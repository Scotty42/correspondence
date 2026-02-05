<script lang="ts">
  import { onMount } from 'svelte';
  import { documents, type Document } from '$lib/api/client';
  
  let docList: Document[] = $state([]);
  let loading = $state(true);
  let error = $state('');
  let filter = $state('');
  
  onMount(loadDocuments);
  
  async function loadDocuments() {
    loading = true;
    try {
      docList = await documents.list(filter || undefined);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler beim Laden';
    } finally {
      loading = false;
    }
  }
  
  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('de-DE');
  }
  
  function formatCurrency(amount: number | null): string {
    if (amount === null) return '-';
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(amount);
  }
  
  function getDocTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      letter: 'Brief',
      invoice: 'Rechnung',
      offer: 'Angebot'
    };
    return labels[type] || type;
  }
  
  async function archiveDoc(doc: Document) {
    if (doc.status === 'archived') return;
    try {
      await documents.archive(doc.id);
      await loadDocuments();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler beim Archivieren';
    }
  }
  
  async function deleteDoc(id: number) {
    if (!confirm('Dokument wirklich löschen?')) return;
    try {
      await documents.delete(id);
      await loadDocuments();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler beim Löschen';
    }
  }
  
  function applyFilter() {
    loadDocuments();
  }
</script>

<svelte:head>
  <title>Dokumente - Korrespondenz</title>
</svelte:head>

<div class="documents-page">
  <div class="flex-between mb-3">
    <h1>Dokumente</h1>
    <div class="flex gap-1">
      <a href="/documents/letter" class="btn btn-primary">+ Brief</a>
      <a href="/documents/invoice" class="btn btn-primary">+ Rechnung</a>
      <a href="/documents/offer" class="btn btn-primary">+ Angebot</a>
    </div>
  </div>
  
  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}
  
  <!-- Filter -->
  <div class="card mb-2">
    <div class="flex gap-1">
      <select class="form-select" style="width: auto;" bind:value={filter} onchange={applyFilter}>
        <option value="">Alle Typen</option>
        <option value="letter">Briefe</option>
        <option value="invoice">Rechnungen</option>
        <option value="offer">Angebote</option>
      </select>
    </div>
  </div>
  
  {#if loading}
    <div class="text-center mt-3">
      <span class="loading"></span>
    </div>
  {:else if docList.length === 0}
    <div class="card text-center">
      <p class="text-muted">Keine Dokumente gefunden.</p>
    </div>
  {:else}
    <div class="card">
      <table class="table">
        <thead>
          <tr>
            <th>Nummer</th>
            <th>Typ</th>
            <th>Betreff</th>
            <th>Datum</th>
            <th>Betrag</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {#each docList as doc}
            <tr>
              <td><strong>{doc.doc_number}</strong></td>
              <td><span class="badge badge-primary">{getDocTypeLabel(doc.doc_type)}</span></td>
              <td>{doc.subject || '-'}</td>
              <td>{formatDate(doc.doc_date)}</td>
              <td>{formatCurrency(doc.gross_total)}</td>
              <td>
                {#if doc.status === 'archived'}
                  <span class="badge badge-success">Archiviert</span>
                {:else}
                  <span class="badge badge-secondary">{doc.status}</span>
                {/if}
              </td>
              <td class="text-right">
                <div class="flex gap-1" style="justify-content: flex-end;">
                  <a href={documents.getPdfUrl(doc.id)} target="_blank" class="btn btn-secondary btn-sm">PDF</a>
                  {#if doc.status !== 'archived'}
                    <button class="btn btn-success btn-sm" onclick={() => archiveDoc(doc)}>Archivieren</button>
                  {/if}
                  <button class="btn btn-danger btn-sm" onclick={() => deleteDoc(doc.id)}>Löschen</button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  h1 {
    font-size: 1.75rem;
    font-weight: 600;
  }
</style>
