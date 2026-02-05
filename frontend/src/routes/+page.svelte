<script lang="ts">
  import { onMount } from 'svelte';
  import { documents, contacts, health, type Document, type Contact, type HealthStatus } from '$lib/api/client';
  
  let recentDocs: Document[] = $state([]);
  let contactCount = $state(0);
  let serviceStatus: HealthStatus | null = $state(null);
  let loading = $state(true);
  let error = $state('');
  
  onMount(async () => {
    try {
      const [docs, contactList, status] = await Promise.all([
        documents.list(),
        contacts.list(),
        health.services()
      ]);
      recentDocs = docs.slice(0, 5);
      contactCount = contactList.length;
      serviceStatus = status;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler beim Laden';
    } finally {
      loading = false;
    }
  });
  
  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('de-DE');
  }
  
  function getDocTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      letter: 'Brief',
      invoice: 'Rechnung',
      offer: 'Angebot'
    };
    return labels[type] || type;
  }
</script>

<svelte:head>
  <title>Dashboard - Korrespondenz</title>
</svelte:head>

<div class="dashboard">
  <h1>Dashboard</h1>
  
  {#if loading}
    <div class="text-center mt-3">
      <span class="loading"></span>
    </div>
  {:else if error}
    <div class="alert alert-error">{error}</div>
  {:else}
    <!-- Quick Actions -->
    <div class="grid grid-3 mt-3">
      <a href="/documents/letter" class="action-card">
        <span class="action-icon">✉️</span>
        <span class="action-label">Neuer Brief</span>
      </a>
      <a href="/documents/invoice" class="action-card">
        <span class="action-icon">🧾</span>
        <span class="action-label">Neue Rechnung</span>
      </a>
      <a href="/documents/offer" class="action-card">
        <span class="action-icon">📋</span>
        <span class="action-label">Neues Angebot</span>
      </a>
    </div>
    
    <!-- Stats -->
    <div class="grid grid-3 mt-3">
      <div class="card stat-card">
        <div class="stat-value">{recentDocs.length}</div>
        <div class="stat-label">Dokumente</div>
      </div>
      <div class="card stat-card">
        <div class="stat-value">{contactCount}</div>
        <div class="stat-label">Kontakte</div>
      </div>
      <div class="card stat-card">
        <div class="stat-value">
          {#if serviceStatus?.ollama.available && serviceStatus?.paperless.available}
            ✅
          {:else}
            ⚠️
          {/if}
        </div>
        <div class="stat-label">Services</div>
      </div>
    </div>
    
    <!-- Recent Documents -->
    <div class="card mt-3">
      <div class="flex-between mb-2">
        <h2>Letzte Dokumente</h2>
        <a href="/documents" class="btn btn-secondary btn-sm">Alle anzeigen</a>
      </div>
      
      {#if recentDocs.length === 0}
        <p class="text-muted">Noch keine Dokumente erstellt.</p>
      {:else}
        <table class="table">
          <thead>
            <tr>
              <th>Nummer</th>
              <th>Typ</th>
              <th>Betreff</th>
              <th>Datum</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {#each recentDocs as doc}
              <tr>
                <td><a href="/api/documents/{doc.id}/pdf" target="_blank">{doc.doc_number}</a></td>
		<td><span class="badge badge-primary">{getDocTypeLabel(doc.doc_type)}</span></td>
                <td>{doc.subject || '-'}</td>
                <td>{formatDate(doc.doc_date)}</td>
                <td>
                  {#if doc.status === 'archived'}
                    <span class="badge badge-success">Archiviert</span>
                  {:else}
                    <span class="badge badge-secondary">{doc.status}</span>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </div>
    
    <!-- Service Status -->
    {#if serviceStatus}
      <div class="card mt-3">
        <h2 class="mb-2">Service Status</h2>
        <div class="services-grid">
          <div class="service-item">
            <span class="service-status" class:online={serviceStatus.ollama.available}></span>
            <div>
              <strong>Ollama (KI)</strong>
              <div class="text-muted">{serviceStatus.ollama.model}</div>
            </div>
          </div>
          <div class="service-item">
            <span class="service-status" class:online={serviceStatus.paperless.available}></span>
            <div>
              <strong>paperless-ngx</strong>
              <div class="text-muted">Archivierung</div>
            </div>
          </div>
        </div>
      </div>
    {/if}
  {/if}
</div>

<style>
  h1 {
    font-size: 1.75rem;
    font-weight: 600;
  }
  
  h2 {
    font-size: 1.125rem;
    font-weight: 600;
  }
  
  .action-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 1.5rem;
    background: white;
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    text-decoration: none;
    color: var(--color-text);
    transition: all 0.15s ease;
  }
  
  .action-card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
    text-decoration: none;
  }
  
  .action-icon {
    font-size: 2rem;
  }
  
  .action-label {
    font-weight: 500;
  }
  
  .stat-card {
    text-align: center;
  }
  
  .stat-value {
    font-size: 2rem;
    font-weight: 600;
    color: var(--color-primary);
  }
  
  .stat-label {
    color: var(--color-text-muted);
    font-size: 0.875rem;
  }
  
  .services-grid {
    display: flex;
    gap: 2rem;
  }
  
  .service-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .service-status {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--color-danger);
  }
  
  .service-status.online {
    background: var(--color-success);
  }
</style>
