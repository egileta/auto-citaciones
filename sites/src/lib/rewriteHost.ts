const ROOT_DOMAIN = 'easyleads.es';

export function rewritePathForHost(
  host: string,
  pathname: string,
  slugs: string[]
): string | null {
  const hostname = host.split(':')[0];
  if (hostname === ROOT_DOMAIN) return null;

  const suffix = `.${ROOT_DOMAIN}`;
  if (!hostname.endsWith(suffix)) return null;

  const slug = hostname.slice(0, -suffix.length);
  if (!slugs.includes(slug)) return null;

  if (pathname === `/${slug}` || pathname.startsWith(`/${slug}/`)) {
    return null;
  }

  return pathname === '/' ? `/${slug}/` : `/${slug}${pathname}`;
}
