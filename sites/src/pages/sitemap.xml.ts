import type { APIRoute } from 'astro';
import { projects } from '../lib/projects';
import { getHubBaseUrl, getProjectBaseUrl, getSiteTarget } from '../lib/siteTarget';
import { loadPostsForTarget, type PostModule } from '../lib/posts';

export const GET: APIRoute = () => {
  const hub = getHubBaseUrl();
  const target = getSiteTarget();
  const modules = import.meta.glob<PostModule>('../content/posts/**/*.md', { eager: true });
  const posts = loadPostsForTarget(modules, target);

  const urls = [
    `${hub}/`,
    ...projects.map((p) => `${getProjectBaseUrl(p.slug)}/`),
    ...posts.map((p) => `${getProjectBaseUrl(p.projectSlug)}/blog/${p.postSlug}/`),
  ];

  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls
    .map((url) => `  <url><loc>${url}</loc></url>`)
    .join('\n')}\n</urlset>\n`;

  return new Response(body, {
    headers: { 'Content-Type': 'application/xml' },
  });
};
