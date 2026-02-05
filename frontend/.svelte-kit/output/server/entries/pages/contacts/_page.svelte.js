import { w as head } from "../../../chunks/index2.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    head("67057e", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Kontakte - Korrespondenz</title>`);
      });
    });
    $$renderer2.push(`<div class="contacts-page"><div class="flex-between mb-3"><h1 class="svelte-67057e">Kontakte</h1> <button class="btn btn-primary">+ Neuer Kontakt</button></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center mt-3"><span class="loading"></span></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
