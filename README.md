# Automated Correspondence Management System

[![CI Smoke](https://github.com/Scotty42/correspondence/actions/workflows/ci-smoke.yml/badge.svg?branch=main)](https://github.com/Scotty42/correspondence/actions/workflows/ci-smoke.yml)
[![codecov](https://codecov.io/gh/Scotty42/correspondence/branch/main/graph/badge.svg)](https://codecov.io/gh/Scotty42/correspondence)
![Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/github/license/Scotty42/correspondence)

A self-hosted web application for creating and managing business and private correspondence (letters, invoices, offers) with template-based PDF generation, LLM assistance, and optional archiving integration.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [LXC Container Setup](#lxc-container-setup)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)

---

## Overview


## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [LXC Container Setup](#lxc-container-setup)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)

---

## Overview

This system replaces traditional word processors for correspondence creation by:

- **Template-based PDF generation** using Typst (modern LaTeX alternative)
- **Separation of content and layout** - users enter text, system handles formatting
- **Contact management** for business and private recipients
- **AI assistance** via local LLM (Ollama) for content suggestions
- **Optional archiving** with paperless-ngx integration
- **Business/Private modes** with different sender data and templates

### Key Features

- **Document Types**: Letters (business/private), invoices, offers
- **DIN 5008 compliant** templates with fold and punch marks
- **VAT handling** including Kleinunternehmer (small business) mode
- **Responsive web interface** built with SvelteKit
- **RESTful API** for extensibility
- **Self-contained** - runs in a single LXC container

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                              Browser                                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         nginx (Port 80)                             │
│  ┌─────────────┐                            ┌─────────────┐         │
│  │ / (static)  │ ───────────────────────────▶│ SvelteKit   │        │
│  └─────────────┘                            └─────────────┘         │
│  ┌─────────────┐                            ┌─────────────┐         │
│  │ /api/*      │ ───────────────────────────▶│ FastAPI     │        │
│  └─────────────┘                            │ (Port 8080) │         │
│                                             └─────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
             ┌───────────┐   ┌───────────┐   ┌───────────┐
             │ Typst     │   │ SQLite    │   │ Ollama    │
             │ Compiler  │   │ Database  │   │ (LLM)     │
             └───────────┘   └───────────┘   └───────────┘
                    │                               │
                    ▼                               │
             ┌───────────────────────────────────────────────┐
             │            PDF Output Directory               │
             └───────────────────────────────────────────────┘
                    │
                    ▼
             ┌───────────────────────────────────────────────┐
             │        paperless-ngx (Optional)               │
             └───────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- FastAPI (Python 3.12+)
- SQLAlchemy (async)
- Typst (PDF generation)
- Pydantic (validation)
- aiosqlite (database)

**Frontend:**
- SvelteKit 5.0
- TypeScript
- Vite
- Static adapter (pre-rendered)

**Infrastructure:**
- nginx (reverse proxy)
- systemd (service management)
- Debian/Ubuntu LXC container

---

## LXC Container Setup

### Prerequisites

- Proxmox VE or LXC-capable host
- Debian 12 or Ubuntu 24.04 LTS container template
- At least 2GB RAM, 10GB storage
- Network connectivity to optional services (Ollama, paperless-ngx)

### Base Container Creation

```bash
# On Proxmox host
pct create <VMID> local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  --hostname correspondence \
  --cores 2 \
  --memory 2048 \
  --swap 512 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --storage local-lvm \
  --rootfs local-lvm:10

pct start <VMID>
pct enter <VMID>
```

### System Packages

```bash
# Update system
apt update && apt upgrade -y

# Essential build tools
apt install -y \
  curl \
  wget \
  git \
  build-essential \
  pkg-config \
  libssl-dev \
  python3 \
  python3-pip \
  python3-venv \
  nginx \
  sqlite3

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Install Inter font (for templates)
apt install -y fonts-inter
fc-cache -fv

# Verify installations
node --version  # Should be v20.x
npm --version   # Should be v10.x
python3 --version  # Should be v3.12+
```

### Install Typst Compiler

```bash
# Download and install Typst
TYPST_VERSION="0.11.1"
wget https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz
tar -xf typst-x86_64-unknown-linux-musl.tar.xz
mv typst-x86_64-unknown-linux-musl/typst /usr/local/bin/
chmod +x /usr/local/bin/typst

# Verify installation
typst --version
```

### Directory Structure

```bash
# Create application directories
mkdir -p /opt/korrespondenz/{app,data,logs,templates,frontend}
mkdir -p /opt/korrespondenz/templates/{letter,invoice,offer}
mkdir -p /opt/korrespondenz/data/documents

# Set permissions
chown -R www-data:www-data /opt/korrespondenz
```

---

## Backend Architecture

### Overview

The backend is built with FastAPI and follows a modular architecture with clear separation of concerns.

```
/opt/korrespondenz/app/
├── main.py              # FastAPI application entry point
├── settings.py          # Pydantic settings management
├── database.py          # Database configuration and models
├── api/
│   ├── __init__.py
│   ├── contacts.py      # Contact CRUD endpoints
│   ├── documents.py     # Document generation endpoints
│   ├── ai.py           # LLM integration endpoints
│   └── health.py       # Health check endpoints
└── services/
    ├── __init__.py
    ├── typst.py        # Typst PDF generation service
    ├── ollama.py       # Ollama LLM service
    └── paperless.py    # paperless-ngx integration service
```

### Core Components

#### 1. Application Entry (`main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Korrespondenz-System",
    description="Self-hosted correspondence management",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers
app.include_router(contacts.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(health.router, prefix="/api")
```

#### 2. Settings Management (`settings.py`)

Uses Pydantic BaseSettings for hierarchical configuration:

```python
class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    log_level: str = "info"

class DatabaseSettings(BaseModel):
    url: str = "sqlite+aiosqlite:///data/korrespondenz.sqlite"

class TypstSettings(BaseModel):
    binary: str = "/usr/local/bin/typst"
    templates_dir: str = "/opt/korrespondenz/templates"
    output_dir: str = "/opt/korrespondenz/data/documents"

class Settings(BaseModel):
    server: ServerSettings
    database: DatabaseSettings
    typst: TypstSettings
    sender: SenderData  # Business sender
    sender_private: SenderData  # Private sender
    # ...
```

Configuration loaded from:
1. `config.yaml` (main configuration)
2. `secrets.env` (sensitive data like API tokens)

#### 3. Database Models (`database.py`)

SQLAlchemy async models with two main entities:

**Contact Model:**
```python
class Contact(Base):
    __tablename__ = "contacts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contact_type: Mapped[str]  # "company" | "private"
    company_name: Mapped[Optional[str]]
    contact_person: Mapped[Optional[str]]
    gender: Mapped[Optional[str]]  # "m" | "f" | "d"
    street: Mapped[str]
    zip: Mapped[str]
    city: Mapped[str]
    country: Mapped[str]
    email: Mapped[Optional[str]]
    phone: Mapped[Optional[str]]
    notes: Mapped[Optional[str]]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

**Document Model:**
```python
class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    document_type: Mapped[str]  # "letter" | "invoice" | "offer"
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))
    subject: Mapped[str]
    content: Mapped[str]
    metadata_: Mapped[dict]  # JSON field for type-specific data
    filepath: Mapped[Optional[str]]
    paperless_id: Mapped[Optional[int]]
    created_at: Mapped[datetime]
    
    # Relationship
    contact: Mapped["Contact"] = relationship()
```

#### 4. API Routes

**Contacts API (`api/contacts.py`):**
```python
router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.get("/", response_model=List[ContactResponse])
async def list_contacts(db: AsyncSession = Depends(get_db))

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db))

@router.post("/", response_model=ContactResponse)
async def create_contact(contact: ContactCreate, db: AsyncSession = Depends(get_db))

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, contact: ContactUpdate, db: AsyncSession = Depends(get_db))

@router.delete("/{contact_id}")
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db))
```

**Documents API (`api/documents.py`):**
```python
router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/generate")
async def generate_document(
    doc: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
)
```

Document generation flow:
1. Validate input (contact exists, required fields)
2. Load appropriate template based on `document_type`
3. Prepare data dictionary with sender, contact, document data
4. Write data as JSON to temporary file
5. Compile Typst template with data to PDF
6. Save document record to database
7. Optionally upload to paperless-ngx
8. Return PDF file or error

#### 5. Typst Service (`services/typst.py`)

```python
class TypstService:
    def __init__(self, settings: TypstSettings):
        self.binary = settings.binary
        self.templates_dir = Path(settings.templates_dir)
        self.output_dir = Path(settings.output_dir)
    
    async def compile_template(
        self,
        template_name: str,
        data: dict,
        output_filename: str
    ) -> Path:
        """
        Compiles a Typst template with given data to PDF.
        
        Process:
        1. Write data to temporary _data.json
        2. Execute: typst compile template.typ output.pdf
        3. Return output path
        """
        template_path = self.templates_dir / template_name
        output_path = self.output_dir / output_filename
        data_path = template_path.parent / "_data.json"
        
        # Write data JSON
        async with aiofiles.open(data_path, "w") as f:
            await f.write(json.dumps(data))
        
        # Compile
        proc = await asyncio.create_subprocess_exec(
            self.binary, "compile", str(template_path), str(output_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise TypstCompilationError(stderr.decode())
        
        return output_path
```

#### 6. LLM Service (`services/ollama.py`)

```python
class OllamaService:
    def __init__(self, settings: OllamaSettings):
        self.url = settings.url
        self.model = settings.model
        self.timeout = settings.timeout
    
    async def generate_suggestion(self, prompt: str, context: dict) -> str:
        """
        Generates text suggestion using Ollama LLM.
        
        Used for:
        - Letter content suggestions
        - Subject line generation
        - Formal/informal style adjustments
        """
        system_prompt = self._build_system_prompt(context)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False
                }
            )
        
        return response.json()["response"]
```

#### 7. paperless-ngx Integration (`services/paperless.py`)

```python
class PaperlessService:
    async def upload_document(
        self,
        filepath: Path,
        title: str,
        correspondent: str,
        document_type: str,
        tags: List[str] = []
    ) -> int:
        """
        Uploads generated PDF to paperless-ngx for archiving.
        
        Returns: Document ID in paperless
        """
        # Upload via paperless API
        # POST /api/documents/post_document/
        # Returns document ID for reference
```

### Database Schema

```sql
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_type TEXT NOT NULL,
    company_name TEXT,
    contact_person TEXT,
    gender TEXT,
    street TEXT NOT NULL,
    zip TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type TEXT NOT NULL,
    contact_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata_ TEXT,  -- JSON
    filepath TEXT,
    paperless_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);
```

### Template System

Templates are written in Typst and located in:
```
/opt/korrespondenz/templates/
├── letter/
│   ├── default.typ          # Standard business letter
│   └── private.typ          # Private letter template
├── invoice/
│   └── default.typ          # Invoice with VAT handling
└── offer/
    └── default.typ          # Offer/quote template
```

Each template receives data via `_data.json` in the same directory:

```typst
#let data = json("_data.json")

// Access sender data
#data.sender.name
#data.sender.address.street

// Access contact data
#data.contact.company_name
#data.contact.street

// Access document data
#data.document.subject
#data.document.content

// Conditional logic example
#if data.sender.kleinunternehmer [
  // No VAT display for small business
] else [
  // Show VAT breakdown
]
```

**Key Template Features:**
- DIN 5008 compliance (fold marks, punch marks, address window)
- Responsive to data (gender-based salutation, company vs. private)
- Inter font family for modern typography
- Automatic page breaks and headers/footers
- VAT calculation for invoices/offers

---

## Frontend Architecture

### Overview

SvelteKit 5 application with TypeScript, compiled to static files for production.

```
/opt/korrespondenz/frontend/
├── src/
│   ├── routes/
│   │   ├── +page.svelte         # Home: Document creation
│   │   ├── contacts/
│   │   │   └── +page.svelte     # Contact management
│   │   └── documents/
│   │       └── +page.svelte     # Document history
│   ├── lib/
│   │   ├── api/
│   │   │   └── client.ts        # API client wrapper
│   │   ├── components/
│   │   │   ├── DocumentForm.svelte
│   │   │   ├── ContactForm.svelte
│   │   │   └── ContactList.svelte
│   │   └── stores/
│   │       ├── contacts.ts      # Svelte stores
│   │       └── documents.ts
│   └── app.html
├── static/                      # Static assets
├── svelte.config.js
├── vite.config.js
└── package.json
```

### Key Components

#### 1. API Client (`src/lib/api/client.ts`)

Centralized API communication with type safety:

```typescript
const API_BASE = '/api';

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API request failed');
  }

  return response.json();
}

export const api = {
  contacts: {
    list: () => request<Contact[]>('/contacts'),
    get: (id: number) => request<Contact>(`/contacts/${id}`),
    create: (data: ContactCreate) =>
      request<Contact>('/contacts', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: number, data: Partial<Contact>) =>
      request<Contact>(`/contacts/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: number) =>
      request<{ message: string }>(`/contacts/${id}`, {
        method: 'DELETE',
      }),
  },
  documents: {
    generate: (data: DocumentCreate) =>
      request<Blob>('/documents/generate', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    list: () => request<Document[]>('/documents'),
  },
  ai: {
    suggest: (prompt: string, context: Record<string, any>) =>
      request<{ suggestion: string }>('/ai/suggest', {
        method: 'POST',
        body: JSON.stringify({ prompt, context }),
      }),
  },
};
```

#### 2. Main Page - Document Creation (`src/routes/+page.svelte`)

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client';
  import type { Contact } from '$lib/types';

  let contacts: Contact[] = [];
  let selectedContact: number | null = null;
  let documentType: 'letter' | 'invoice' | 'offer' = 'letter';
  let letterType: 'business' | 'private' = 'business';
  let subject = '';
  let content = '';

  onMount(async () => {
    contacts = await api.contacts.list();
  });

  async function generateDocument() {
    try {
      const pdfBlob = await api.documents.generate({
        document_type: documentType,
        contact_id: selectedContact!,
        subject,
        content,
        metadata: {
          letter_type: documentType === 'letter' ? letterType : undefined,
        },
      });

      // Download PDF
      const url = URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${documentType}_${Date.now()}.pdf`;
      a.click();
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  }
</script>

<main>
  <h1>Neues Dokument erstellen</h1>

  <div class="form">
    <!-- Document Type Selection -->
    <div class="type-selector">
      <button on:click={() => (documentType = 'letter')}>Brief</button>
      <button on:click={() => (documentType = 'invoice')}>Rechnung</button>
      <button on:click={() => (documentType = 'offer')}>Angebot</button>
    </div>

    {#if documentType === 'letter'}
      <div class="letter-type">
        <label>
          <input type="radio" bind:group={letterType} value="business" />
          Geschäftsbrief
        </label>
        <label>
          <input type="radio" bind:group={letterType} value="private" />
          Privatbrief
        </label>
      </div>
    {/if}

    <!-- Contact Selection -->
    <select bind:value={selectedContact}>
      <option value={null}>Empfänger wählen...</option>
      {#each contacts as contact}
        <option value={contact.id}>
          {contact.contact_type === 'company'
            ? contact.company_name
            : contact.contact_person}
        </option>
      {/each}
    </select>

    <!-- Subject and Content -->
    <input type="text" bind:value={subject} placeholder="Betreff" />
    <textarea bind:value={content} placeholder="Inhalt" rows="10" />

    <button on:click={generateDocument}>PDF erstellen</button>
  </div>
</main>
```

#### 3. Contact Management (`src/routes/contacts/+page.svelte`)

Full CRUD interface for contacts with:
- List view with search/filter
- Create/edit modal
- Delete confirmation
- Validation

#### 4. Svelte Stores

Reactive state management:

```typescript
// src/lib/stores/contacts.ts
import { writable } from 'svelte/store';
import type { Contact } from '$lib/types';

function createContactStore() {
  const { subscribe, set, update } = writable<Contact[]>([]);

  return {
    subscribe,
    load: async () => {
      const contacts = await api.contacts.list();
      set(contacts);
    },
    add: async (contact: ContactCreate) => {
      const created = await api.contacts.create(contact);
      update((contacts) => [...contacts, created]);
    },
    remove: async (id: number) => {
      await api.contacts.delete(id);
      update((contacts) => contacts.filter((c) => c.id !== id));
    },
  };
}

export const contacts = createContactStore();
```

### Build Configuration

**SvelteKit Config (`svelte.config.js`):**
```javascript
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: 'index.html',
      precompress: false,
      strict: true,
    }),
  },
};

export default config;
```

**Vite Config (`vite.config.js`):**
```javascript
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
});
```

---

## Installation

### 1. Clone or Download

```bash
cd /opt/korrespondenz
git clone <your-repo-url> .
# Or manually copy files to the directory
```

### 2. Backend Setup

```bash
cd /opt/korrespondenz

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install \
  fastapi \
  uvicorn[standard] \
  sqlalchemy[asyncio] \
  aiosqlite \
  pydantic \
  pydantic-settings \
  pyyaml \
  python-multipart \
  httpx \
  aiofiles

# Create configuration files
cp config.example.yaml config.yaml
cp secrets.example.env secrets.env

# Edit with your data
nano config.yaml
nano secrets.env

# Initialize database
python -m app.database
```

### 3. Frontend Setup

```bash
cd /opt/korrespondenz/frontend

# Install dependencies
npm install

# Build for production
npm run build

# Build output will be in: /opt/korrespondenz/frontend/build/
```

### 4. Systemd Service

Create `/etc/systemd/system/korrespondenz.service`:

```ini
[Unit]
Description=Korrespondenz System Backend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/korrespondenz
Environment="PATH=/opt/korrespondenz/venv/bin"
ExecStart=/opt/korrespondenz/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080 --log-config /opt/korrespondenz/logging.conf

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable korrespondenz
systemctl start korrespondenz
systemctl status korrespondenz
```

### 5. nginx Configuration

Create `/etc/nginx/sites-available/korrespondenz`:

```nginx
server {
    listen 80;
    server_name correspondence.lan.internal;

    # Frontend (static files)
    location / {
        root /opt/korrespondenz/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8080/api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Generated PDFs (if serving directly)
    location /documents/ {
        alias /opt/korrespondenz/data/documents/;
        internal;
    }
}
```

Enable and reload:
```bash
ln -s /etc/nginx/sites-available/korrespondenz /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## Configuration

### Main Configuration (`config.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8080
  debug: false
  log_level: "info"

database:
  url: "sqlite+aiosqlite:///data/korrespondenz.sqlite"

typst:
  binary: "/usr/local/bin/typst"
  templates_dir: "/opt/korrespondenz/templates"
  output_dir: "/opt/korrespondenz/data/documents"

# Business sender data
sender:
  name: "Your Business Name"
  address:
    street: "Street 123"
    zip: "12345"
    city: "City"
    country: "Country"
  contact:
    phone: "+49 123 456789"
    email: "info@example.com"
  tax:
    ustid: "DE123456789"
  kleinunternehmer: false

# Private sender data
sender_private:
  name: "Your Name"
  address:
    street: "Street 123"
    zip: "12345"
    city: "City"

# Optional: Ollama LLM
ollama:
  enabled: true
  url: "http://ollama.lan.internal:11434"
  model: "gemma2-small-ctx:latest"

# Optional: paperless-ngx
paperless:
  enabled: true
  url: "http://paperless.lan.internal:8000"
  verify_ssl: false
```

### Secrets (`secrets.env`)

```bash
# paperless-ngx API token
PAPERLESS_TOKEN=your_token_here

# Other sensitive data
```

---

## Usage

### Creating Documents

1. **Access the web interface**: `http://correspondence.lan.internal`
2. **Select document type**: Letter, Invoice, or Offer
3. **Choose recipient** from contacts (or create new)
4. **Enter subject and content**
5. **Generate PDF** - downloads automatically

### Managing Contacts

1. Navigate to **Contacts** page
2. **Add new contact** - company or private
3. **Edit/Delete** existing contacts
4. Contacts are available in document creation dropdown

### AI Assistance (Optional)

If Ollama is configured:
- Click **AI Help** button when writing content
- Provide context (formal/informal, topic)
- System generates suggestion using local LLM

### Archiving (Optional)

If paperless-ngx is configured:
- Generated PDFs automatically upload
- Tagged with document type and correspondent
- Searchable in paperless-ngx

---

## Development & CI

The project includes lightweight smoke tests (backend + frontend) that verify
basic startup and health endpoints. Runtime data (SQLite DB, generated PDFs)
is intentionally excluded from the repository and injected via environment
configuration to ensure reproducibility and data separation.

### Running in Development Mode

**Backend:**
```bash
cd /opt/korrespondenz
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

**Frontend:**
```bash
cd /opt/korrespondenz/frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

Access: `http://correspondence.lan.internal:5173` (frontend dev server proxies API)

### Testing

```bash
# Backend tests
cd /opt/korrespondenz
pytest tests/

# Frontend tests
cd /opt/korrespondenz/frontend
npm run test
```

### Adding New Templates

1. Create template in `/opt/korrespondenz/templates/<type>/<name>.typ`
2. Ensure template reads `_data.json`
3. Test compilation manually:
   ```bash
   echo '{"sender":{"name":"Test"}}' > /tmp/_data.json
   typst compile your-template.typ output.pdf
   ```
4. Add template option in frontend UI

### Extending Document Types

1. Add new type to `DocumentType` enum in backend
2. Create corresponding template
3. Update frontend with new UI option
4. Add validation and metadata schema if needed

---

## Troubleshooting

### PDF Generation Fails

- Check Typst installation: `typst --version`
- Check template syntax: Compile manually
- Verify `_data.json` structure matches template expectations
- Check backend logs: `journalctl -u korrespondenz -f`

### Frontend Can't Connect to Backend

- Verify backend is running: `systemctl status korrespondenz`
- Check nginx proxy configuration: `nginx -t`
- Check CORS settings in backend `main.py`
- Inspect browser console for error details

### Database Errors

- Check database file permissions: `/opt/korrespondenz/data/korrespondenz.sqlite`
- Reinitialize database: `python -m app.database`
- Check SQLAlchemy connection string in `config.yaml`

### paperless-ngx Upload Fails

- Verify network connectivity: `curl http://paperless.lan.internal:8000`
- Check API token in `secrets.env`
- Review paperless logs for rejection reasons

---

## License

MIT License - see LICENSE file

## Contributing

Pull requests welcome! Please:
- Follow existing code style
- Add tests for new features
- Update documentation

---

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [SvelteKit](https://kit.svelte.dev/)
- [Typst](https://typst.app/)
- [Ollama](https://ollama.com/)
- [paperless-ngx](https://docs.paperless-ngx.com/)
