import { rewritePathForHost } from '../src/lib/rewriteHost';
import { getAllSlugs } from '../src/lib/projects';

interface PagesEnv {
  ASSETS: { fetch: typeof fetch };
}

interface PagesContext {
  request: Request;
  env: PagesEnv;
  next: () => Promise<Response>;
}

export const onRequest = async (context: PagesContext): Promise<Response> => {
  const url = new URL(context.request.url);
  const newPath = rewritePathForHost(url.hostname, url.pathname, getAllSlugs());

  if (newPath) {
    url.pathname = newPath;
    return context.env.ASSETS.fetch(new Request(url.toString(), context.request));
  }

  return context.next();
};
