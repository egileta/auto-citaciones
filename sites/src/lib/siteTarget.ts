export type SiteTarget = 'cloudflare' | 'github';

const ROOT_DOMAIN = 'easyleads.es';
const GITHUB_DOMAIN = 'gh.easyleads.es';

export function getSiteTarget(): SiteTarget {
  return process.env.SITE_TARGET === 'github' ? 'github' : 'cloudflare';
}

export function getHubBaseUrl(target: SiteTarget = getSiteTarget()): string {
  return target === 'github' ? `https://${GITHUB_DOMAIN}` : `https://${ROOT_DOMAIN}`;
}

export function getProjectBaseUrl(slug: string, target: SiteTarget = getSiteTarget()): string {
  if (target === 'github') {
    return `https://${GITHUB_DOMAIN}/${slug}`;
  }
  return `https://${slug}.${ROOT_DOMAIN}`;
}
