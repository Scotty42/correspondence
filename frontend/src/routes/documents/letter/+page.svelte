<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { contacts, documents, ai, type Contact } from '$lib/api/client';
  
  let contactList: Contact[] = $state([]);
  let loading = $state(true);
  let saving = $state(false);
  let generating = $state(false);
  let error = $state('');
  let success = $state('');
  
  // Form
  let letterType = $state<'business' | 'private'>('business');
  let selectedContactId = $state<number | null>(null);
  let subject = $state('');
  let content = $state('');
  let aiContext = $state('');
  
  onMount(async () => {
    try {
      contactList = await contacts.list();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler beim Laden der Kontakte';
    } finally {
      loading = false;
    }
  });
  
  async function generateDraft() {
    if (!aiContext.trim()) {
      error = 'Bitte beschreibe das Anliegen für die KI';
      return;
    }
    
    generating = true;
    error = '';
    
    try {
      const response = await ai.generateDraft({
        doc_type: 'letter',
        context: aiContext,
        tone: letterType === 'business' ? 'formal' : 'friendly',
        letter_type: letterType,
        contact_id: selectedContactId || undefined
      });
      content = response.text;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler bei der Textgenerierung';
    } finally {
      generating = false;
    }
  }
  
  async function saveLetter() {
    if (!selectedContactId) {
      error = 'Bitte wähle einen Empfänger';
      return;
    }
    if (!subject.trim()) {
      error = 'Bitte gib einen Betreff ein';
      return;
    }
    if (!content.trim()) {
      error = 'Bitte gib den Briefinhalt ein';
      return;
    }
    
    saving = true;
    error = '';
    
    try {
      const doc = await documents.createLetter({
        contact_id: selectedContactId,
        subject,
        content,
        letter_type: letterType
      });
      success = `${letterType === 'business' ? 'Geschäftsbrief' : 'Privatbrief'} ${doc.doc_number} wurde erstellt`;
      
      // PDF in neuem Tab öffnen
      window.open(documents.getPdfUrl(doc.id), '_blank');
      
      // Nach kurzer Pause zur Dokumentenliste
      setTimeout(() => goto('/documents'), 1500);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler beim Erstellen';
    } finally {
      saving = false;
    }
  }
  
  function getContactDisplayName(contact: Contact): string {
    if (contact.company_name) {
      if (contact.first_name) {
        return `${contact.company_name} (${contact.first_name} ${contact.last_name})`;
      }
      return contact.company_name;
    }
    return [contact.first_name, contact.last_name].filter(Boolean).join(' ') || 'Unbenannt';
  }
</script>

<svelte:head>
  <title>Neuer Brief - Korrespondenz</title>
</svelte:head>

<div class="letter-page">
  <div class="flex-between mb-3">
    <h1>Neuer Brief</h1>
    <a href="/documents" class="btn btn-secondary">← Zurück</a>
  </div>
  
  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}
  
  {#if success}
    <div class="alert alert-success">{success}</div>
  {/if}
  
  {#if loading}
    <div class="text-center mt-3">
      <span class="loading"></span>
    </div>
  {:else}
    <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 1.5rem;">
      <!-- Formular -->
      <div class="card">
        <h2 class="mb-2">Brief erstellen</h2>
        
        <form onsubmit={(e) => { e.preventDefault(); saveLetter(); }}>
          <!-- Brieftyp Auswahl -->
          <div class="form-group">
            <label class="form-label">Brieftyp</label>
            <div class="letter-type-selector">
              <button 
                type="button"
                class="type-btn" 
                class:active={letterType === 'business'}
                onclick={() => letterType = 'business'}
              >
                <span class="type-icon">🏢</span>
                <span class="type-label">Geschäftsbrief</span>
                <span class="type-desc">Mit Firmenname & Geschäftsdaten</span>
              </button>
              <button 
                type="button"
                class="type-btn" 
                class:active={letterType === 'private'}
                onclick={() => letterType = 'private'}
              >
                <span class="type-icon">👤</span>
                <span class="type-label">Privatbrief</span>
                <span class="type-desc">Nur persönlicher Name</span>
              </button>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">Empfänger *</label>
            <select class="form-select" bind:value={selectedContactId} required>
              <option value={null}>-- Bitte wählen --</option>
              {#each contactList as contact}
                <option value={contact.id}>{getContactDisplayName(contact)}</option>
              {/each}
            </select>
            {#if contactList.length === 0}
              <div class="mt-1">
                <a href="/contacts" class="text-muted">Erst Kontakt anlegen →</a>
              </div>
            {/if}
          </div>
          
          <div class="form-group">
            <label class="form-label">Betreff *</label>
            <input type="text" class="form-input" bind:value={subject} required placeholder="z.B. Anfrage zu Ihrem Angebot">
          </div>
          
          <div class="form-group">
            <label class="form-label">Inhalt *</label>
            <textarea 
              class="form-textarea" 
              bind:value={content} 
              required 
              rows="12"
              placeholder="Brieftext (ohne Anrede und Grußformel - diese werden automatisch ergänzt)"
            ></textarea>
          </div>
          
          <div class="flex gap-1">
            <button type="submit" class="btn btn-primary" disabled={saving}>
              {#if saving}
                <span class="loading"></span> Erstelle...
              {:else}
                {letterType === 'business' ? 'Geschäftsbrief' : 'Privatbrief'} erstellen
              {/if}
            </button>
          </div>
        </form>
      </div>
      
      <!-- KI-Assistent -->
      <div class="card">
        <h2 class="mb-2">🤖 KI-Assistent</h2>
        <p class="text-muted mb-2">Beschreibe dein Anliegen und lass dir einen Textentwurf generieren.</p>
        
        <div class="form-group">
          <label class="form-label">Anliegen beschreiben</label>
          <textarea 
            class="form-textarea" 
            bind:value={aiContext}
            rows="4"
            placeholder="z.B. Absage eines Termins wegen Krankheit, Nachfrage zum Status einer Bestellung, Beschwerde über verspätete Lieferung..."
          ></textarea>
        </div>
        
        <button 
          type="button" 
          class="btn btn-secondary" 
          onclick={generateDraft}
          disabled={generating || !aiContext.trim()}
        >
          {#if generating}
            <span class="loading"></span> Generiere...
          {:else}
            ✨ Text generieren
          {/if}
        </button>
        
        <div class="ai-hint mt-2">
          <strong>Tipp:</strong> Der generierte Text wird im Inhaltsfeld eingefügt. 
          {#if letterType === 'business'}
            Für Geschäftsbriefe wird ein formeller Ton verwendet.
          {:else}
            Für Privatbriefe wird ein freundlicherer Ton verwendet.
          {/if}
        </div>
        
        <!-- Info-Box zum Brieftyp -->
        <div class="info-box mt-3">
          <h3>📋 {letterType === 'business' ? 'Geschäftsbrief' : 'Privatbrief'}</h3>
          {#if letterType === 'business'}
            <ul>
              <li>Absender: <strong>Ingenieurbüro Dr.-Ing. Friedrich</strong></li>
              <li>Mit Geschäftsdaten in der Fußzeile</li>
              <li>Aktenzeichen/Dokumentennummer wird angezeigt</li>
              <li>Nummernkreis: BRF-YYYY-XXXX</li>
            </ul>
          {:else}
            <ul>
              <li>Absender: <strong>Dr.-Ing. Markus Friedrich</strong> (privat)</li>
              <li>Minimale Fußzeile</li>
              <li>Ohne Aktenzeichen</li>
              <li>Nummernkreis: PRV-YYYY-XXXX</li>
            </ul>
          {/if}
        </div>
      </div>
    </div>
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
  
  h3 {
    font-size: 0.9375rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }
  
  .letter-type-selector {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }
  
  .type-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    padding: 1rem;
    background: var(--color-bg);
    border: 2px solid var(--color-border);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all 0.15s ease;
  }
  
  .type-btn:hover {
    border-color: var(--color-primary);
  }
  
  .type-btn.active {
    border-color: var(--color-primary);
    background: #eff6ff;
  }
  
  .type-icon {
    font-size: 1.5rem;
  }
  
  .type-label {
    font-weight: 600;
    font-size: 0.9375rem;
  }
  
  .type-desc {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }
  
  .ai-hint {
    font-size: 0.8125rem;
    color: var(--color-text-muted);
    background: var(--color-bg);
    padding: 0.75rem;
    border-radius: var(--radius);
  }
  
  .info-box {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-radius: var(--radius);
    padding: 1rem;
  }
  
  .info-box ul {
    margin: 0;
    padding-left: 1.25rem;
    font-size: 0.875rem;
  }
  
  .info-box li {
    margin-bottom: 0.25rem;
  }
</style>
