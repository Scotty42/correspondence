import "clsx";
function _layout($$renderer, $$props) {
  let { children } = $$props;
  $$renderer.push(`<div class="app svelte-12qhfyh"><header class="header svelte-12qhfyh"><div class="container"><nav class="nav svelte-12qhfyh"><a href="/" class="logo svelte-12qhfyh">📝 Korrespondenz</a> <div class="nav-links svelte-12qhfyh"><a href="/" class="svelte-12qhfyh">Dashboard</a> <a href="/documents" class="svelte-12qhfyh">Dokumente</a> <a href="/contacts" class="svelte-12qhfyh">Kontakte</a></div></nav></div></header> <main class="main svelte-12qhfyh"><div class="container">`);
  children($$renderer);
  $$renderer.push(`<!----></div></main></div>`);
}
export {
  _layout as default
};
