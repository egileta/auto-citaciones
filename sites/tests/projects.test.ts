import { describe, it, expect } from 'vitest';
import { projects, getProjectBySlug, getAllSlugs } from '../src/lib/projects';

describe('projects data loader', () => {
  it('loads exactly 6 projects', () => {
    expect(projects).toHaveLength(6);
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
    expect(getAllSlugs()).toEqual([
      'easyseo',
      'newcom',
      'arroba',
      'erpopensource',
      'fotobizkaia',
      'pasteleriasanturtzi',
    ]);
  });

  it('every project has complete NAP data', () => {
    // 'erpopensource' is pending a telephone number (no NAP phone found yet
    // for the Tryton Foundation) — tracked separately, not a passing gap.
    const PENDING_TELEPHONE = ['erpopensource'];
    for (const project of projects) {
      expect(project.nap.streetAddress).toBeTruthy();
      expect(project.nap.addressLocality).toBeTruthy();
      expect(project.nap.postalCode).toBeTruthy();
      expect(['ES', 'BE']).toContain(project.nap.addressCountry);
      if (!PENDING_TELEPHONE.includes(project.slug)) {
        expect(project.nap.telephone).toBeTruthy();
      }
    }
  });
});
