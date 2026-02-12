// API Client für das Korrespondenz-Backend

const BASE_URL = '/api';


export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}


export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    //const apiPath = path.startsWith('/') ? path : `/${path}`;
    // remove trailing slash except for root "/"
    //const normalized = apiPath.length > 1 ? apiPath.replace(/\/+$/, '') : apiPath;
    //const res = `/api${normalized}`

    const res = await fetch(`/api${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    ...options,
  });

  // Try to parse JSON error body (FastAPI uses {"detail": "..."} )
  let body: any = null;
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try { body = await res.json(); } catch { /* ignore */ }
  } else {
    try { body = await res.text(); } catch { /* ignore */ }
  }

  if (!res.ok) {
    const detail = body?.detail ?? (typeof body === 'string' ? body : undefined);

    if (res.status === 404) {
      throw new ApiError(404, 'Not found', detail);
    }
    if (res.status === 409) {
      throw new ApiError(409, 'Conflict', detail);
    }

    throw new ApiError(res.status, 'Request failed', detail);
  }

  return (body ?? (await res.json())) as T;
}


export function normalizeContactPayload(data: Partial<Contact>) {
  const out: any = {};

  for (const [k, v] of Object.entries(data)) {
    if (v === undefined || v === null) continue;

    if (typeof v === 'string') {
      const trimmed = v.trim();
      if (trimmed === '') continue;          // omit empty fields (recommended)
      out[k] = trimmed;
    } else {
      out[k] = v;
    }
  }

  return out;
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
  
  get: (id: number) => request<Contact>(`/contacts/${id}`),
  
  create: (data: Partial<Contact>) => 
    request<Contact>('/contacts/', {
      method: 'POST',
      body: JSON.stringify(normalizeContactPayload(data)),
    }),
  
  update: (id: number, data: Partial<Contact>) =>
    request<Contact>(`/contacts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(normalizeContactPayload(data)),
    }),
  
  delete: (id: number) =>
    request<{ status: string }>(`/contacts/${id}`, {
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
