#!/bin/bash
# Frontend Setup Script für Korrespondenz-System
# Auf dem Korrespondenz-LXC ausführen

set -e

echo "=== Frontend Setup ==="
echo ""

# 1. Node.js installieren (via NodeSource)
echo "1. Node.js 20 LTS installieren..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
sudo apt-get install -y nodejs

echo "   Node Version: $(node --version)"
echo "   NPM Version: $(npm --version)"
echo ""

# 2. Frontend-Verzeichnis erstellen
echo "2. Frontend-Verzeichnis anlegen..."
mkdir -p /opt/korrespondenz/frontend
cd /opt/korrespondenz/frontend

# 3. SvelteKit Projekt initialisieren
echo "3. SvelteKit Projekt erstellen..."
cat > package.json << 'EOF'
{
  "name": "korrespondenz-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite dev --host 0.0.0.0 --port 5173",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "@sveltejs/adapter-static": "^3.0.0",
    "@sveltejs/kit": "^2.0.0",
    "@sveltejs/vite-plugin-svelte": "^5.0.0",
    "svelte": "^5.0.0",
    "vite": "^6.0.0"
  },
  "type": "module"
}
EOF

# 4. SvelteKit Config
cat > svelte.config.js << 'EOF'
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: 'index.html',
      precompress: false,
      strict: true
    }),
    paths: {
      base: ''
    }
  }
};

export default config;
EOF

# 5. Vite Config
cat > vite.config.js << 'EOF'
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
});
EOF

# 6. TypeScript Config
cat > tsconfig.json << 'EOF'
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "allowJs": true,
    "checkJs": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "sourceMap": true,
    "strict": true,
    "moduleResolution": "bundler"
  }
}
EOF

# 7. Verzeichnisstruktur
mkdir -p src/lib/components
mkdir -p src/lib/api
mkdir -p src/routes/contacts
mkdir -p src/routes/documents
mkdir -p src/routes/documents/letter
mkdir -p src/routes/documents/invoice
mkdir -p src/routes/documents/offer
mkdir -p static

echo ""
echo "4. NPM Pakete installieren..."
npm install

echo ""
echo "=== Setup abgeschlossen ==="
echo ""
echo "Nächste Schritte:"
echo "  cd /opt/korrespondenz/frontend"
echo "  npm run dev    # Development Server starten"
echo ""
