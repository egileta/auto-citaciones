import type { Project } from './projects';

export function buildLocalBusinessJsonLd(project: Project, canonicalUrl: string) {
  return {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    name: project.name,
    url: project.website,
    mainEntityOfPage: canonicalUrl,
    telephone: project.nap.telephone,
    description: project.description,
    address: {
      '@type': 'PostalAddress',
      streetAddress: project.nap.streetAddress,
      addressLocality: project.nap.addressLocality,
      postalCode: project.nap.postalCode,
      addressCountry: project.nap.addressCountry,
    },
    sameAs: project.sameAs,
  };
}
