import { getProjectBaseUrl, type SiteTarget } from './siteTarget';
import { bloggerPublished, type BloggerPublishedEntry } from './blogPublished';

export interface LinkWheelEntry {
  label: string;
  url: string;
}

const CHANNEL_LABEL: Record<SiteTarget, string> = {
  cloudflare: 'Versión en Cloudflare Pages',
  github: 'Versión en GitHub Pages',
};

export function buildPostLinkWheel(
  projectSlug: string,
  postSlug: string,
  currentTarget: SiteTarget,
  published: Record<string, BloggerPublishedEntry> = bloggerPublished
): LinkWheelEntry[] {
  const entries: LinkWheelEntry[] = [];

  for (const target of ['cloudflare', 'github'] as SiteTarget[]) {
    if (target === currentTarget) continue;
    entries.push({
      label: CHANNEL_LABEL[target],
      url: `${getProjectBaseUrl(projectSlug, target)}/${postSlug}/`,
    });
  }

  const bloggerEntry = published[`${projectSlug}/${postSlug}`];
  if (bloggerEntry) {
    entries.push({ label: 'Versión en Blogger', url: bloggerEntry.blogger_post_url });
  }

  return entries;
}
