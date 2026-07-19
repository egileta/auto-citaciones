import { getProjectBaseUrl, type SiteTarget } from './siteTarget';
import { bloggerPublished, type BloggerPublishedEntry } from './blogPublished';
import { tumblrPublished, type TumblrPublishedEntry } from './tumblrPublished';
import { parsePostPath, type PostModule } from './posts';

export interface LinkWheelEntry {
  title: string;
  url: string;
}

type Channel = 'cloudflare' | 'github' | 'blogger' | 'tumblr';

function findChannelModules(
  modules: Record<string, PostModule>,
  projectSlug: string,
  postSlug: string
): Partial<Record<Channel, PostModule>> {
  const result: Partial<Record<Channel, PostModule>> = {};
  for (const [path, module] of Object.entries(modules)) {
    const parsed = parsePostPath(path);
    if (!parsed || parsed.projectSlug !== projectSlug || parsed.postSlug !== postSlug) continue;
    result[parsed.channel] = module;
  }
  return result;
}

/**
 * Cross-channel links for one post, using each channel's own (deliberately
 * varied) title as the anchor text instead of a "Version on X" label —
 * identical anchor text across near-duplicate copies of the same article
 * is a link-scheme signal, a real title per channel isn't.
 */
function buildChannelLinks(
  modules: Record<string, PostModule>,
  projectSlug: string,
  postSlug: string,
  targets: SiteTarget[],
  bloggerEntries: Record<string, BloggerPublishedEntry>,
  tumblrEntries: Record<string, TumblrPublishedEntry>
): LinkWheelEntry[] {
  const channelModules = findChannelModules(modules, projectSlug, postSlug);
  const entries: LinkWheelEntry[] = [];

  for (const target of targets) {
    const module = channelModules[target];
    if (!module) continue;
    entries.push({
      title: module.frontmatter.title,
      url: `${getProjectBaseUrl(projectSlug, target)}/${postSlug}/`,
    });
  }

  const bloggerModule = channelModules.blogger;
  const bloggerEntry = bloggerEntries[`${projectSlug}/${postSlug}`];
  if (bloggerModule && bloggerEntry) {
    entries.push({ title: bloggerModule.frontmatter.title, url: bloggerEntry.blogger_post_url });
  }

  const tumblrModule = channelModules.tumblr;
  const tumblrEntry = tumblrEntries[`${projectSlug}/${postSlug}`];
  if (tumblrModule && tumblrEntry) {
    entries.push({ title: tumblrModule.frontmatter.title, url: tumblrEntry.tumblr_post_url });
  }

  return entries;
}

/** Used by the post page: links to the *other* channels' versions, excluding the current one. */
export function buildPostLinkWheel(
  modules: Record<string, PostModule>,
  projectSlug: string,
  postSlug: string,
  currentTarget: SiteTarget,
  bloggerEntries: Record<string, BloggerPublishedEntry> = bloggerPublished,
  tumblrEntries: Record<string, TumblrPublishedEntry> = tumblrPublished
): LinkWheelEntry[] {
  const otherTargets = (['cloudflare', 'github'] as SiteTarget[]).filter((t) => t !== currentTarget);
  return buildChannelLinks(modules, projectSlug, postSlug, otherTargets, bloggerEntries, tumblrEntries);
}

/** Used by the citation root page: links to all channels' versions of a post (the page itself isn't any one channel's article). */
export function buildAllChannelLinks(
  modules: Record<string, PostModule>,
  projectSlug: string,
  postSlug: string,
  bloggerEntries: Record<string, BloggerPublishedEntry> = bloggerPublished,
  tumblrEntries: Record<string, TumblrPublishedEntry> = tumblrPublished
): LinkWheelEntry[] {
  return buildChannelLinks(modules, projectSlug, postSlug, ['cloudflare', 'github'], bloggerEntries, tumblrEntries);
}
