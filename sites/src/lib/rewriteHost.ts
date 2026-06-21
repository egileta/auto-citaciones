const ROOT_DOMAIN = 'easyleads.es';

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

  if (pathname === `/${slug}` || pathname.startsWith(`/${slug}/`)) {
    const stripped = pathname.slice(`/${slug}`.length) || '/';
    return { action: 'redirect', path: stripped };
  }

  return {
    action: 'rewrite',
    path: pathname === '/' ? `/${slug}/` : `/${slug}${pathname}`,
  };
}
