import { describe, it, expect } from 'vitest';
import { resolveHostRouting } from '../src/lib/rewriteHost';

const SLUGS = ['easyseo', 'newcom', 'arroba'];

describe('resolveHostRouting', () => {
  it('rewrites the root path for a known subdomain', () => {
    expect(resolveHostRouting('easyseo.easyleads.es', '/', SLUGS)).toEqual({
      action: 'rewrite',
      path: '/easyseo/',
    });
  });

  it('rewrites a nested path for a known subdomain', () => {
    expect(resolveHostRouting('easyseo.easyleads.es', '/01-post/', SLUGS)).toEqual({
      action: 'rewrite',
      path: '/easyseo/01-post/',
    });
  });

  it('does not rewrite the root domain', () => {
    expect(resolveHostRouting('easyleads.es', '/', SLUGS)).toBeNull();
  });

  it('does not rewrite an unknown subdomain', () => {
    expect(resolveHostRouting('unknown.easyleads.es', '/', SLUGS)).toBeNull();
  });

  it('redirects an already-prefixed path to its clean equivalent', () => {
    expect(resolveHostRouting('easyseo.easyleads.es', '/easyseo/01-post/', SLUGS)).toEqual({
      action: 'redirect',
      path: '/01-post/',
    });
  });

  it('redirects the bare prefixed slug to the subdomain root', () => {
    expect(resolveHostRouting('easyseo.easyleads.es', '/easyseo', SLUGS)).toEqual({
      action: 'redirect',
      path: '/',
    });
  });
});
