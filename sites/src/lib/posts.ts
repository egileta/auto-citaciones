export interface ParsedPostPath {
  projectSlug: string;
  postSlug: string;
  channel: 'cloudflare' | 'github' | 'blogger';
}

export function parsePostPath(path: string): ParsedPostPath | null {
  const match = path.match(/content\/posts\/([^/]+)\/([^/]+)\/(cloudflare|github|blogger)\.md$/);
  if (!match) return null;
  const [, projectSlug, postSlug, channel] = match;
  return { projectSlug, postSlug, channel: channel as ParsedPostPath['channel'] };
}

export interface PostFrontmatter {
  title: string;
  date: string;
  project: string;
}

export interface PostModule {
  frontmatter: PostFrontmatter;
  compiledContent: () => Promise<string>;
}

export interface LoadedPost {
  projectSlug: string;
  postSlug: string;
  frontmatter: PostFrontmatter;
  module: PostModule;
}

const CHANNEL_FOR_TARGET: Record<'cloudflare' | 'github', ParsedPostPath['channel']> = {
  cloudflare: 'cloudflare',
  github: 'github',
};

export function loadPostsForTarget(
  modules: Record<string, PostModule>,
  target: 'cloudflare' | 'github'
): LoadedPost[] {
  const channel = CHANNEL_FOR_TARGET[target];
  const posts: LoadedPost[] = [];

  for (const [path, module] of Object.entries(modules)) {
    const parsed = parsePostPath(path);
    if (!parsed || parsed.channel !== channel) continue;
    posts.push({
      projectSlug: parsed.projectSlug,
      postSlug: parsed.postSlug,
      frontmatter: module.frontmatter,
      module,
    });
  }

  return posts;
}
