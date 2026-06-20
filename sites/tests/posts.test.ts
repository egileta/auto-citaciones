import { describe, it, expect } from 'vitest';
import { parsePostPath, loadPostsForTarget } from '../src/lib/posts';

describe('parsePostPath', () => {
  it('parses a valid post path', () => {
    const parsed = parsePostPath('/x/content/posts/easyseo/01-tema/cloudflare.md');
    expect(parsed).toEqual({ projectSlug: 'easyseo', postSlug: '01-tema', channel: 'cloudflare' });
  });

  it('returns null for an unrelated path', () => {
    expect(parsePostPath('/x/content/posts/easyseo/readme.md')).toBeNull();
  });
});

describe('loadPostsForTarget', () => {
  const modules = {
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
  };

  it('returns only the cloudflare variant for the cloudflare target', () => {
    const posts = loadPostsForTarget(modules, 'cloudflare');
    expect(posts).toHaveLength(1);
    expect(posts[0].frontmatter.title).toBe('Tema CF');
  });

  it('returns only the github variant for the github target', () => {
    const posts = loadPostsForTarget(modules, 'github');
    expect(posts).toHaveLength(1);
    expect(posts[0].frontmatter.title).toBe('Tema GH');
  });
});
