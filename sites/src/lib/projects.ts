import projectsData from '../data/projects.json';

export interface ProjectNap {
  streetAddress: string;
  addressLocality: string;
  postalCode: string;
  addressCountry: string;
  telephone: string;
}

export interface Project {
  slug: string;
  subdomain: string;
  name: string;
  description: string;
  nap: ProjectNap;
  sameAs: string[];
}

export const projects: Project[] = projectsData as Project[];

export function getProjectBySlug(slug: string): Project | undefined {
  return projects.find((project) => project.slug === slug);
}

export function getAllSlugs(): string[] {
  return projects.map((project) => project.slug);
}
