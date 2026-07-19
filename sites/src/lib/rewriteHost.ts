const ROOT_DOMAIN = 'easyleads.es';

// Rutas globales servidas igual en cualquier subdominio (no son páginas por
// proyecto bajo /<slug>/), así que deben pasar sin reescribir o el fetch al
// fichero /<slug>/sitemap.xml (o /<slug>/robots.txt) inexistente cae al
// fallback SPA de Cloudflare Pages y devuelve el HTML de la home en vez del
// fichero esperado.
const GLOBAL_PATHS = ['/sitemap.xml', '/robots.txt'];

export interface HostRoutingRewrite {
  action: 'rewrite';
  path: string;
}

export interface HostRoutingRedirect {
  action: 'redirect';
  path: string;
}

export type HostRoutingResult = HostRoutingRewrite | HostRoutingRedirect | null;

export function resolveHostRouting(
  host: string,
  pathname: string,
  slugs: string[]
): HostRoutingResult {
  const hostname = host.split(':')[0];
  if (hostname === ROOT_DOMAIN) return null;

  const suffix = `.${ROOT_DOMAIN}`;
  if (!hostname.endsWith(suffix)) return null;

  const slug = hostname.slice(0, -suffix.length);
  if (!slugs.includes(slug)) return null;

  if (GLOBAL_PATHS.includes(pathname)) return null;

  if (pathname === `/${slug}` || pathname.startsWith(`/${slug}/`)) {
    const stripped = pathname.slice(`/${slug}`.length) || '/';
    return { action: 'redirect', path: stripped };
  }

  return {
    action: 'rewrite',
    path: pathname === '/' ? `/${slug}/` : `/${slug}${pathname}`,
  };
}
