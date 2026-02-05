<script lang="ts">
  import '../app.css';
  
  let { children } = $props();
</script>

<div class="app">
  <header class="header">
    <div class="container">
      <nav class="nav">
        <a href="/" class="logo">📝 Korrespondenz</a>
        <div class="nav-links">
          <a href="/">Dashboard</a>
          <a href="/documents">Dokumente</a>
          <a href="/contacts">Kontakte</a>
        </div>
      </nav>
    </div>
  </header>
  
  <main class="main">
    <div class="container">
      {@render children()}
    </div>
  </main>
</div>

<style>
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  
  .header {
    background: white;
    border-bottom: 1px solid var(--color-border);
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  
  .nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .logo {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-text);
    text-decoration: none;
  }
  
  .nav-links {
    display: flex;
    gap: 1.5rem;
  }
  
  .nav-links a {
    color: var(--color-text-muted);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.15s;
  }
  
  .nav-links a:hover {
    color: var(--color-primary);
  }
  
  .main {
    flex: 1;
    padding: 2rem 0;
  }
</style>
