import { describe, it, expect } from 'vitest';
import { projects, getProjectBySlug, getAllSlugs } from '../src/lib/projects';

describe('projects data loader', () => {
  it('loads exactly 3 projects', () => {
    expect(projects).toHaveLength(3);
  });

  it('finds a project by slug', () => {
    const project = getProjectBySlug('easyseo');
    expect(project?.name).toBe('Agencia Easy SEO Local Vizcaya');
    expect(project?.nap.telephone).toBe('+34 695 50 19 79');
  });

  it('returns undefined for unknown slug', () => {
    expect(getProjectBySlug('nope')).toBeUndefined();
  });

  it('returns all slugs in file order', () => {
    expect(getAllSlugs()).toEqual(['easyseo', 'newcom', 'arroba']);
  });

  it('every project has complete NAP data', () => {
    for (const project of projects) {
      expect(project.nap.streetAddress).toBeTruthy();
      expect(project.nap.addressLocality).toBeTruthy();
      expect(project.nap.postalCode).toBeTruthy();
      expect(project.nap.addressCountry).toBe('ES');
      expect(project.nap.telephone).toBeTruthy();
    }
  });
});
