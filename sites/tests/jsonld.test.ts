import { describe, it, expect } from 'vitest';
import { buildLocalBusinessJsonLd } from '../src/lib/jsonld';
import { getProjectBySlug } from '../src/lib/projects';

describe('buildLocalBusinessJsonLd', () => {
  it('builds a LocalBusiness JSON-LD with the project NAP', () => {
    const project = getProjectBySlug('easyseo')!;
    const jsonLd = buildLocalBusinessJsonLd(project, 'https://easyseo.easyleads.es');

    expect(jsonLd['@type']).toBe('LocalBusiness');
    expect(jsonLd.name).toBe('Agencia Easy SEO Local Vizcaya');
    expect(jsonLd.telephone).toBe('+34 695 50 19 79');
    expect((jsonLd.address as Record<string, unknown>).addressCountry).toBe('ES');
    expect(jsonLd.sameAs as string[]).toContain('https://www.linkedin.com/company/easy-seo-vizcaya');
  });
});
