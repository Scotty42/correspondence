// API Client für das Korrespondenz-Backend

const BASE_URL = '/api';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const response = await fetch(url, config);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unbekannter Fehler' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

function normalizeContactPayload<T extends Record<string, any>>(data: T) {
  const out: Record<string, any> = {};

  for (const [k, v] of Object.entries(data)) {
    if (v === undefined) continue;

    // Trim bei Strings
    if (typeof v === "string") {
      const trimmed = v.trim();
      // leere Strings -> null
      out[k] = trimmed === "" ? null : trimmed;
      continue;
    }

    out[k] = v;
  }

  return out as Partial<T>;
}

// Types
export interface Contact {
  id: number;
  contact_type: string;
  company_name: string | null;
  salutation: string | null;
  first_name: string | null;
  last_name: string | null;
  gender: string | null;
  street: string | null;
  zip_code: string | null;
  city: string | null;
  country: string;
  email: string | null;
  phone: string | null;
  customer_number: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Position {
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  vat_rate: number;
}

export interface Document {
  id: number;
  doc_type: string;
  doc_number: string;
  contact_id: number;
  subject: string | null;
  status: string;
  net_total: number | null;
  gross_total: number | null;
  doc_date: string;
  pdf_path: string | null;
  paperless_id: number | null;
  created_at: string;
}

export interface DraftResponse {
  text: string;
  model: string;
  tokens_used: number | null;
}

export interface HealthStatus {
  ollama: {
    configured: boolean;
    url: string;
    model: string;
    available: boolean;
  };
  paperless: {
    configured: boolean;
    url: string;
    available: boolean;
  };
}

export type LetterType = 'business' | 'private';

// Contacts API
export const contacts = {
  list: () => request<Contact[]>('/contacts/'),
  
  get: (id: number) => request<Contact>(`/contacts/${id}/`),
  
  create: (data: Partial<Contact>) => 
    request<Contact>('/contacts/', {
      method: 'POST',
      body: JSON.stringify(normalizeContactPayload(data)),
    }),
  
  update: (id: number, data: Partial<Contact>) =>
    request<Contact>(`/contacts/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(normalizeContactPayload(data)),
    }),
  
  delete: (id: number) =>
    request<{ message: string }>(`/contacts/${id}/`, {
      method: 'DELETE',
    }),
};

// Documents API
export const documents = {
  list: (docType?: string) => {
    const params = docType ? `?doc_type=${docType}` : '';
    return request<Document[]>(`/documents/${params}`);
  },
  
  get: (id: number) => request<Document>(`/documents/${id}`),
  
  createLetter: (data: {
    contact_id: number;
    subject: string;
    content: string;
    letter_type?: LetterType;
    doc_date?: string;
  }) => request<Document>('/documents/letter', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  createInvoice: (data: {
    contact_id: number;
    positions: Position[];
    due_days?: number;
    notes?: string;
    doc_date?: string;
  }) => request<Document>('/documents/invoice', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  createOffer: (data: {
    contact_id: number;
    subject: string;
    positions: Position[];
    valid_days?: number;
    prepayment_percent?: number;
    notes?: string;
    doc_date?: string;
  }) => request<Document>('/documents/offer', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  archive: (id: number) =>
    request<{ message: string; task_id: string }>(`/documents/${id}/archive`, {
      method: 'POST',
    }),
  
  delete: (id: number) =>
    request<{ message: string }>(`/documents/${id}`, {
      method: 'DELETE',
    }),
  
  getPdfUrl: (id: number) => `${BASE_URL}/documents/${id}/pdf`,
};

// AI API
export const ai = {
  generateDraft: (data: {
    doc_type: string;
    context: string;
    tone?: string;
    letter_type?: LetterType;
    contact_id?: number;
  }) => request<DraftResponse>('/ai/draft', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  improveText: (text: string) =>
    request<{ original: string; improved: string }>('/ai/improve', {
      method: 'POST',
      body: JSON.stringify(text),
    }),
};

// Health API
export const health = {
  check: () => request<{ status: string }>('/health'),
  services: () => request<HealthStatus>('/health/services'),
};
