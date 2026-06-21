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

const CHANNEL_SHORT_LABEL: Record<SiteTarget | 'blogger', string> = {
  cloudflare: 'Cloudflare Pages',
  github: 'GitHub Pages',
  blogger: 'Blogger',
};

export interface ChannelLink {
  channel: SiteTarget | 'blogger';
  channelLabel: string;
  url: string;
}

/**
 * All channel variants of a single post belonging to one project, used by
 * the citation root page where each owned post fans out into one entry per
 * channel (own subdomain + the other 2), instead of one entry per post.
 */
export function buildAllChannelLinks(
  projectSlug: string,
  postSlug: string,
  published: Record<string, BloggerPublishedEntry> = bloggerPublished
): ChannelLink[] {
  const entries: ChannelLink[] = (['cloudflare', 'github'] as SiteTarget[]).map((target) => ({
    channel: target,
    channelLabel: CHANNEL_SHORT_LABEL[target],
    url: `${getProjectBaseUrl(projectSlug, target)}/${postSlug}/`,
  }));

  const bloggerEntry = published[`${projectSlug}/${postSlug}`];
  if (bloggerEntry) {
    entries.push({
      channel: 'blogger',
      channelLabel: CHANNEL_SHORT_LABEL.blogger,
      url: bloggerEntry.blogger_post_url,
    });
  }

  return entries;
}
