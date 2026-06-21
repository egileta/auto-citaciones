import published from '../../../data/blogger_published.json';

export interface BloggerPublishedEntry {
  blogger_post_url: string;
  blogger_post_id: string;
  content_hash: string;
}

export const bloggerPublished: Record<string, BloggerPublishedEntry> = published;
