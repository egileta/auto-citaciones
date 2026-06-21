import { describe, it, expect } from 'vitest';
import { buildPostLinkWheel } from '../src/lib/linkWheel';

describe('buildPostLinkWheel', () => {
  it('links to the other channels but not the current one', () => {
    const entries = buildPostLinkWheel('easyseo', '01-tema', 'cloudflare', {});
    expect(entries).toEqual([
      { label: 'Versión en GitHub Pages', url: 'https://gh.easyleads.es/easyseo/01-tema/' },
    ]);
  });

  it('includes the Blogger entry when the post has been published there', () => {
    const published = {
      'easyseo/01-tema': {
        blogger_post_url: 'https://easy-leads.blogspot.com/2026/06/post.html',
        blogger_post_id: '1',
        content_hash: 'abc',
      },
    };
    const entries = buildPostLinkWheel('easyseo', '01-tema', 'github', published);
    expect(entries).toEqual([
      { label: 'Versión en Cloudflare Pages', url: 'https://easyseo.easyleads.es/01-tema/' },
      { label: 'Versión en Blogger', url: 'https://easy-leads.blogspot.com/2026/06/post.html' },
    ]);
  });

  it('omits the Blogger entry when the post has not been published there', () => {
    const entries = buildPostLinkWheel('arroba', '01-tema', 'cloudflare', {});
    expect(entries.some((entry) => entry.label === 'Versión en Blogger')).toBe(false);
  });
});
