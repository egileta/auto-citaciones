import published from '../../../data/tumblr_published.json';

export interface TumblrPublishedEntry {
  tumblr_post_url: string;
  tumblr_post_id: string;
  content_hash: string;
}

export const tumblrPublished: Record<string, TumblrPublishedEntry> = published;
