import { resolveHostRouting } from '../src/lib/rewriteHost';
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
  const result = resolveHostRouting(url.hostname, url.pathname, getAllSlugs());

  if (result?.action === 'redirect') {
    const target = new URL(url.toString());
    target.pathname = result.path;
    return Response.redirect(target.toString(), 301);
  }

  if (result?.action === 'rewrite') {
    const target = new URL(url.toString());
    target.pathname = result.path;
    return context.env.ASSETS.fetch(new Request(target.toString(), context.request));
  }

  return context.next();
};
