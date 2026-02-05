<script lang="ts">
  import { onMount } from 'svelte';
  import { contacts, type Contact } from '$lib/api/client';
  
  let contactList: Contact[] = $state([]);
  let loading = $state(true);
  let error = $state('');
  let showForm = $state(false);
  let editingContact: Contact | null = $state(null);
  
  // Form state
  let form = $state({
    contact_type: 'company',
    company_name: '',
    salutation: '',
    first_name: '',
    last_name: '',
    gender: '',
    street: '',
    zip_code: '',
    city: '',
    email: '',
    phone: '',
    customer_number: '',
    notes: ''
  });
  
  onMount(loadContacts);
  
  async function loadContacts() {
    loading = true;
    try {
      contactList = await contacts.list();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler beim Laden';
    } finally {
      loading = false;
    }
  }
  
  function resetForm() {
    form = {
      contact_type: 'company',
      company_name: '',
      salutation: '',
      first_name: '',
      last_name: '',
      gender: '',
      street: '',
      zip_code: '',
      city: '',
      email: '',
      phone: '',
      customer_number: '',
      notes: ''
    };
    editingContact = null;
  }
  
  function openNewForm() {
    resetForm();
    showForm = true;
  }
  
  function openEditForm(contact: Contact) {
    editingContact = contact;
    form = {
      contact_type: contact.contact_type,
      company_name: contact.company_name || '',
      salutation: contact.salutation || '',
      first_name: contact.first_name || '',
      last_name: contact.last_name || '',
      gender: contact.gender || '',
      street: contact.street || '',
      zip_code: contact.zip_code || '',
      city: contact.city || '',
      email: contact.email || '',
      phone: contact.phone || '',
      customer_number: contact.customer_number || '',
      notes: contact.notes || ''
    };
    showForm = true;
  }
  
  async function saveContact() {
    try {
      if (editingContact) {
        await contacts.update(editingContact.id, form);
      } else {
        await contacts.create(form);
      }
      showForm = false;
      resetForm();
      await loadContacts();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler beim Speichern';
    }
  }
  
  async function deleteContact(id: number) {
    if (!confirm('Kontakt wirklich löschen?')) return;
    try {
      await contacts.delete(id);
      await loadContacts();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Fehler beim Löschen';
    }
  }
  
  function getDisplayName(contact: Contact): string {
    if (contact.company_name) return contact.company_name;
    return [contact.first_name, contact.last_name].filter(Boolean).join(' ') || 'Unbenannt';
  }
</script>

<svelte:head>
  <title>Kontakte - Korrespondenz</title>
</svelte:head>

<div class="contacts-page">
  <div class="flex-between mb-3">
    <h1>Kontakte</h1>
    <button class="btn btn-primary" onclick={openNewForm}>+ Neuer Kontakt</button>
  </div>
  
  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}
  
  {#if loading}
    <div class="text-center mt-3">
      <span class="loading"></span>
    </div>
  {:else if showForm}
    <div class="card">
      <h2 class="mb-2">{editingContact ? 'Kontakt bearbeiten' : 'Neuer Kontakt'}</h2>
      
      <form onsubmit={(e) => { e.preventDefault(); saveContact(); }}>
        <div class="form-group">
          <label class="form-label">Typ</label>
          <select class="form-select" bind:value={form.contact_type}>
            <option value="company">Firma</option>
            <option value="person">Person</option>
          </select>
        </div>
        
        {#if form.contact_type === 'company'}
          <div class="form-group">
            <label class="form-label">Firmenname *</label>
            <input type="text" class="form-input" bind:value={form.company_name} required>
          </div>
        {/if}
        
        <div class="grid grid-2">
          <div class="form-group">
            <label class="form-label">Anrede</label>
            <select class="form-select" bind:value={form.salutation}>
              <option value="">-</option>
              <option value="Herr">Herr</option>
              <option value="Frau">Frau</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Geschlecht</label>
            <select class="form-select" bind:value={form.gender}>
              <option value="">-</option>
              <option value="m">Männlich</option>
              <option value="f">Weiblich</option>
              <option value="d">Divers</option>
            </select>
          </div>
        </div>
        
        <div class="grid grid-2">
          <div class="form-group">
            <label class="form-label">Vorname</label>
            <input type="text" class="form-input" bind:value={form.first_name}>
          </div>
          <div class="form-group">
            <label class="form-label">Nachname</label>
            <input type="text" class="form-input" bind:value={form.last_name}>
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label">Straße</label>
          <input type="text" class="form-input" bind:value={form.street}>
        </div>
        
        <div class="grid grid-2">
          <div class="form-group">
            <label class="form-label">PLZ</label>
            <input type="text" class="form-input" bind:value={form.zip_code}>
          </div>
          <div class="form-group">
            <label class="form-label">Ort</label>
            <input type="text" class="form-input" bind:value={form.city}>
          </div>
        </div>
        
        <div class="grid grid-2">
          <div class="form-group">
            <label class="form-label">E-Mail</label>
            <input type="email" class="form-input" bind:value={form.email}>
          </div>
          <div class="form-group">
            <label class="form-label">Telefon</label>
            <input type="text" class="form-input" bind:value={form.phone}>
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label">Kundennummer</label>
          <input type="text" class="form-input" bind:value={form.customer_number}>
        </div>
        
        <div class="form-group">
          <label class="form-label">Notizen</label>
          <textarea class="form-textarea" bind:value={form.notes}></textarea>
        </div>
        
        <div class="flex gap-1 mt-2">
          <button type="submit" class="btn btn-primary">Speichern</button>
          <button type="button" class="btn btn-secondary" onclick={() => { showForm = false; resetForm(); }}>Abbrechen</button>
        </div>
      </form>
    </div>
  {:else if contactList.length === 0}
    <div class="card text-center">
      <p class="text-muted">Noch keine Kontakte vorhanden.</p>
      <button class="btn btn-primary mt-2" onclick={openNewForm}>Ersten Kontakt anlegen</button>
    </div>
  {:else}
    <div class="card">
      <table class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Ort</th>
            <th>E-Mail</th>
            <th>Telefon</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {#each contactList as contact}
            <tr>
              <td>
                <strong>{getDisplayName(contact)}</strong>
                {#if contact.contact_type === 'company' && contact.first_name}
                  <div class="text-muted">{contact.first_name} {contact.last_name}</div>
                {/if}
              </td>
              <td>{contact.city || '-'}</td>
              <td>{contact.email || '-'}</td>
              <td>{contact.phone || '-'}</td>
              <td class="text-right">
                <button class="btn btn-secondary btn-sm" onclick={() => openEditForm(contact)}>Bearbeiten</button>
                <button class="btn btn-danger btn-sm" onclick={() => deleteContact(contact.id)}>Löschen</button>
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
  
  h2 {
    font-size: 1.25rem;
    font-weight: 600;
  }
</style>
