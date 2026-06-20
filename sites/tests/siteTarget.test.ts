import { describe, it, expect } from 'vitest';
import { getHubBaseUrl, getProjectBaseUrl } from '../src/lib/siteTarget';

describe('siteTarget base URLs', () => {
  it('cloudflare hub root', () => {
    expect(getHubBaseUrl('cloudflare')).toBe('https://easyleads.es');
  });

  it('github hub root', () => {
    expect(getHubBaseUrl('github')).toBe('https://gh.easyleads.es');
  });

  it('cloudflare project uses a subdomain', () => {
    expect(getProjectBaseUrl('easyseo', 'cloudflare')).toBe('https://easyseo.easyleads.es');
  });

  it('github project uses a path', () => {
    expect(getProjectBaseUrl('easyseo', 'github')).toBe('https://gh.easyleads.es/easyseo');
  });
});
