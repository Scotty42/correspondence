import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
  // Proxy /api requests to backend
  if (event.url.pathname.startsWith('/api')) {
    const backendUrl = 'http://localhost:8080' + event.url.pathname + event.url.search;
    
    const response = await fetch(backendUrl, {
      method: event.request.method,
      headers: event.request.headers,
      body: event.request.method !== 'GET' && event.request.method !== 'HEAD' 
        ? await event.request.text() 
        : undefined,
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  }

  return resolve(event);
};
