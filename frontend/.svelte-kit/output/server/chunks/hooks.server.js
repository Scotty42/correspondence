const handle = async ({ event, resolve }) => {
  if (event.url.pathname.startsWith("/api")) {
    const backendUrl = "http://localhost:8080" + event.url.pathname + event.url.search;
    const response = await fetch(backendUrl, {
      method: event.request.method,
      headers: event.request.headers,
      body: event.request.method !== "GET" && event.request.method !== "HEAD" ? await event.request.text() : void 0
    });
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers
    });
  }
  return resolve(event);
};
export {
  handle
};
