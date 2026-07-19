import { describe, it, expect } from 'vitest';
import { buildPostLinkWheel, buildAllChannelLinks } from '../src/lib/linkWheel';

const MODULES = {
  '/x/content/posts/easyseo/01-tema/cloudflare.md': {
    frontmatter: { title: 'Tema CF', date: '2026-01-01', project: 'easyseo' },
    compiledContent: async () => '<p>cf</p>',
  },
  '/x/content/posts/easyseo/01-tema/github.md': {
    frontmatter: { title: 'Tema GH', date: '2026-01-01', project: 'easyseo' },
    compiledContent: async () => '<p>gh</p>',
  },
  '/x/content/posts/easyseo/01-tema/blogger.md': {
    frontmatter: { title: 'Tema BG', date: '2026-01-01', project: 'easyseo' },
    compiledContent: async () => '<p>bg</p>',
  },
  '/x/content/posts/easyseo/01-tema/tumblr.md': {
    frontmatter: { title: 'Tema TB', date: '2026-01-01', project: 'easyseo' },
    compiledContent: async () => '<p>tb</p>',
  },
};

const PUBLISHED = {
  'easyseo/01-tema': {
    blogger_post_url: 'https://blogger.easyleads.es/2026/01/tema.html',
    blogger_post_id: '1',
    content_hash: 'h',
  },
};

const TUMBLR_PUBLISHED = {
  'easyseo/01-tema': {
    tumblr_post_url: 'https://easyleads.tumblr.com/post/1',
    tumblr_post_id: '1',
    content_hash: 'h',
  },
};

describe('buildPostLinkWheel', () => {
  it('excludes the current target and uses each channel\'s own title', () => {
    const entries = buildPostLinkWheel(MODULES, 'easyseo', '01-tema', 'cloudflare', PUBLISHED, TUMBLR_PUBLISHED);
    expect(entries).toEqual([
      { title: 'Tema GH', url: 'https://gh.easyleads.es/easyseo/01-tema/' },
      { title: 'Tema BG', url: 'https://blogger.easyleads.es/2026/01/tema.html' },
      { title: 'Tema TB', url: 'https://easyleads.tumblr.com/post/1' },
    ]);
  });

  it('omits the Blogger and Tumblr entries when the post has not been published there yet', () => {
    const entries = buildPostLinkWheel(MODULES, 'easyseo', '01-tema', 'cloudflare', {}, {});
    expect(entries).toEqual([{ title: 'Tema GH', url: 'https://gh.easyleads.es/easyseo/01-tema/' }]);
  });
});

describe('buildAllChannelLinks', () => {
  it('includes every channel, none excluded', () => {
    const entries = buildAllChannelLinks(MODULES, 'easyseo', '01-tema', PUBLISHED, TUMBLR_PUBLISHED);
    expect(entries).toEqual([
      { title: 'Tema CF', url: 'https://easyseo.easyleads.es/01-tema/' },
      { title: 'Tema GH', url: 'https://gh.easyleads.es/easyseo/01-tema/' },
      { title: 'Tema BG', url: 'https://blogger.easyleads.es/2026/01/tema.html' },
      { title: 'Tema TB', url: 'https://easyleads.tumblr.com/post/1' },
    ]);
  });
});
