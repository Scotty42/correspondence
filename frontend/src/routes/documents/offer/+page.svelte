<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { contacts, documents, ai, type Contact, type Position } from '$lib/api/client';
  
  let contactList: Contact[] = $state([]);
  let loading = $state(true);
  let saving = $state(false);
  let generating = $state(false);
  let error = $state('');
  let success = $state('');
  
  // Form
  let selectedContactId = $state<number | null>(null);
  let subject = $state('');
  let validDays = $state(30);
  let prepaymentPercent = $state<number | null>(null);
  let notes = $state('');
  let positions = $state<Position[]>([
    { description: '', quantity: 1, unit: 'Stück', unit_price: 0, vat_rate: 19 }
  ]);
  
  // AI
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
  
  function addPosition() {
    positions = [...positions, { description: '', quantity: 1, unit: 'Stück', unit_price: 0, vat_rate: 19 }];
  }
  
  function removePosition(index: number) {
    positions = positions.filter((_, i) => i !== index);
  }
  
  function calculateNet(): number {
    return positions.reduce((sum, p) => sum + (p.quantity * p.unit_price), 0);
  }
  
  function calculateVat(): number {
    return positions.reduce((sum, p) => sum + (p.quantity * p.unit_price * p.vat_rate / 100), 0);
  }
  
  function calculateGross(): number {
    return calculateNet() + calculateVat();
  }
  
  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(amount);
  }
  
  async function generateIntro() {
    if (!aiContext.trim()) {
      error = 'Bitte beschreibe das Angebot für die KI';
      return;
    }
    
    generating = true;
    error = '';
    
    try {
      const response = await ai.generateDraft({
        doc_type: 'offer_intro',
        context: aiContext,
        contact_id: selectedContactId || undefined
      });
      notes = response.text;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler bei der Textgenerierung';
    } finally {
      generating = false;
    }
  }
  
  async function saveOffer() {
    if (!selectedContactId) {
      error = 'Bitte wähle einen Empfänger';
      return;
    }
    if (!subject.trim()) {
      error = 'Bitte gib einen Betreff ein';
      return;
    }
    
    const validPositions = positions.filter(p => p.description.trim() && p.unit_price > 0);
    if (validPositions.length === 0) {
      error = 'Bitte füge mindestens eine Position hinzu';
      return;
    }
    
    saving = true;
    error = '';
    
    try {
      const doc = await documents.createOffer({
        contact_id: selectedContactId,
        subject,
        positions: validPositions,
        valid_days: validDays,
        prepayment_percent: prepaymentPercent || undefined,
        notes: notes || undefined
      });
      success = `Angebot ${doc.doc_number} wurde erstellt`;
      
      window.open(documents.getPdfUrl(doc.id), '_blank');
      setTimeout(() => goto('/documents'), 1500);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler beim Erstellen';
    } finally {
      saving = false;
    }
  }
  
  function getContactDisplayName(contact: Contact): string {
    if (contact.company_name) {
      return contact.company_name;
    }
    return [contact.first_name, contact.last_name].filter(Boolean).join(' ') || 'Unbenannt';
  }
</script>

<svelte:head>
  <title>Neues Angebot - Korrespondenz</title>
</svelte:head>

<div class="offer-page">
  <div class="flex-between mb-3">
    <h1>Neues Angebot</h1>
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
    <form onsubmit={(e) => { e.preventDefault(); saveOffer(); }}>
      <div class="card mb-2">
        <h2 class="mb-2">Angebots-Details</h2>
        
        <div class="grid grid-2">
          <div class="form-group">
            <label class="form-label">Empfänger *</label>
            <select class="form-select" bind:value={selectedContactId} required>
              <option value={null}>-- Bitte wählen --</option>
              {#each contactList as contact}
                <option value={contact.id}>{getContactDisplayName(contact)}</option>
              {/each}
            </select>
          </div>
          
          <div class="form-group">
            <label class="form-label">Betreff *</label>
            <input type="text" class="form-input" bind:value={subject} required placeholder="z.B. IT-Beratung Digitalisierung">
          </div>
        </div>
        
        <div class="grid grid-2">
          <div class="form-group">
            <label class="form-label">Gültigkeit (Tage)</label>
            <input type="number" class="form-input" bind:value={validDays} min="1" max="365">
          </div>
          
          <div class="form-group">
            <label class="form-label">Anzahlung (%)</label>
            <input type="number" class="form-input" bind:value={prepaymentPercent} min="0" max="100" placeholder="Optional">
          </div>
        </div>
      </div>
      
      <div class="card mb-2">
        <div class="flex-between mb-2">
          <h2>Positionen</h2>
          <button type="button" class="btn btn-secondary btn-sm" onclick={addPosition}>+ Position</button>
        </div>
        
        <table class="table">
          <thead>
            <tr>
              <th style="width: 40%">Beschreibung</th>
              <th style="width: 10%">Menge</th>
              <th style="width: 12%">Einheit</th>
              <th style="width: 15%">Einzelpreis</th>
              <th style="width: 10%">MwSt %</th>
              <th style="width: 13%">Gesamt</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {#each positions as pos, i}
              <tr>
                <td>
                  <input type="text" class="form-input" bind:value={pos.description} placeholder="Beschreibung">
                </td>
                <td>
                  <input type="number" class="form-input" bind:value={pos.quantity} min="0.01" step="0.01">
                </td>
                <td>
                  <select class="form-select" bind:value={pos.unit}>
                    <option value="Stück">Stück</option>
                    <option value="Stunden">Stunden</option>
                    <option value="Tage">Tage</option>
                    <option value="Pauschal">Pauschal</option>
                    <option value="km">km</option>
                  </select>
                </td>
                <td>
                  <input type="number" class="form-input" bind:value={pos.unit_price} min="0" step="0.01">
                </td>
                <td>
                  <select class="form-select" bind:value={pos.vat_rate}>
                    <option value={19}>19%</option>
                    <option value={7}>7%</option>
                    <option value={0}>0%</option>
                  </select>
                </td>
                <td class="text-right">
                  {formatCurrency(pos.quantity * pos.unit_price)}
                </td>
                <td>
                  {#if positions.length > 1}
                    <button type="button" class="btn btn-danger btn-sm" onclick={() => removePosition(i)}>×</button>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
        
        <div class="totals mt-2">
          <div class="total-row">
            <span>Netto:</span>
            <span>{formatCurrency(calculateNet())}</span>
          </div>
          <div class="total-row">
            <span>MwSt:</span>
            <span>{formatCurrency(calculateVat())}</span>
          </div>
          <div class="total-row total-gross">
            <span>Gesamt:</span>
            <span>{formatCurrency(calculateGross())}</span>
          </div>
        </div>
      </div>
      
      <!-- Notes with AI -->
      <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="card">
          <h2 class="mb-2">Notizen / Einleitung</h2>
          <textarea class="form-textarea" bind:value={notes} rows="5" placeholder="Zusätzlicher Text im Angebot..."></textarea>
        </div>
        
        <div class="card">
          <h2 class="mb-2">🤖 KI-Assistent</h2>
          <div class="form-group">
            <textarea 
              class="form-textarea" 
              bind:value={aiContext}
              rows="3"
              placeholder="Beschreibe das Angebot kurz..."
            ></textarea>
          </div>
          <button 
            type="button" 
            class="btn btn-secondary" 
            onclick={generateIntro}
            disabled={generating || !aiContext.trim()}
          >
            {#if generating}
              <span class="loading"></span> Generiere...
            {:else}
              ✨ Einleitung generieren
            {/if}
          </button>
        </div>
      </div>
      
      <div class="mt-2">
        <button type="submit" class="btn btn-primary" disabled={saving}>
          {#if saving}
            <span class="loading"></span> Erstelle...
          {:else}
            Angebot erstellen & PDF öffnen
          {/if}
        </button>
      </div>
    </form>
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
  
  .totals {
    max-width: 300px;
    margin-left: auto;
  }
  
  .total-row {
    display: flex;
    justify-content: space-between;
    padding: 0.375rem 0;
    border-bottom: 1px solid var(--color-border);
  }
  
  .total-gross {
    font-weight: 600;
    font-size: 1.125rem;
    border-bottom: none;
    padding-top: 0.5rem;
  }
</style>
