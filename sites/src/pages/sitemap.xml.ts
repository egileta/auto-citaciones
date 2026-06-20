import type { APIRoute } from 'astro';
import { projects } from '../lib/projects';
import { getHubBaseUrl, getProjectBaseUrl } from '../lib/siteTarget';

export const GET: APIRoute = () => {
  const hub = getHubBaseUrl();
  const urls = [`${hub}/`, ...projects.map((p) => `${getProjectBaseUrl(p.slug)}/`)];

  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls
    .map((url) => `  <url><loc>${url}</loc></url>`)
    .join('\n')}\n</urlset>\n`;

  return new Response(body, {
    headers: { 'Content-Type': 'application/xml' },
  });
};
