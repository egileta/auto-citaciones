import { describe, it, expect } from 'vitest';
import { rewritePathForHost } from '../src/lib/rewriteHost';

const SLUGS = ['easyseo', 'newcom', 'arroba'];

describe('rewritePathForHost', () => {
  it('rewrites the root path for a known subdomain', () => {
    expect(rewritePathForHost('easyseo.easyleads.es', '/', SLUGS)).toBe('/easyseo/');
  });

  it('rewrites a nested path for a known subdomain', () => {
    expect(rewritePathForHost('easyseo.easyleads.es', '/blog/post-1', SLUGS)).toBe(
      '/easyseo/blog/post-1'
    );
  });

  it('does not rewrite the root domain', () => {
    expect(rewritePathForHost('easyleads.es', '/', SLUGS)).toBeNull();
  });

  it('does not rewrite an unknown subdomain', () => {
    expect(rewritePathForHost('unknown.easyleads.es', '/', SLUGS)).toBeNull();
  });

  it('does not double-prefix an already-prefixed path', () => {
    expect(rewritePathForHost('easyseo.easyleads.es', '/easyseo/blog', SLUGS)).toBeNull();
  });
});
