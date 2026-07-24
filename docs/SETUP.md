# Configurar el proyecto en un equipo nuevo

Esta guía cubre cómo dejar el repo operativo en una máquina distinta a la
que se usó originalmente: clonar, instalar el stack local, y (si vas a
ejecutar los scripts de Python en local en vez de dejar que lo haga CI)
rellenar las credenciales. Para el "por qué" de cada pieza de
infraestructura y cómo se montó desde cero, ver
[`docs/DEPLOYMENT.md`](DEPLOYMENT.md) — este documento es solo el "cómo
arranco en un sitio nuevo".

## 0. Lo que ya vive en GitHub (no hace falta migrar nada)

El despliegue real ocurre en GitHub Actions con los secrets ya configurados
en el repo (`Settings > Secrets and variables > Actions`). Eso **no se
mueve a la máquina nueva** ni depende de ella: en cuanto clones el repo y
hagas push a `main`, el workflow `.github/workflows/deploy.yml` despliega
igual que siempre, desde los runners de GitHub. La máquina nueva solo
necesita credenciales locales si quieres:

- ejecutar `scripts/blogger_publish.py`, `scripts/submit_indexnow.py` o
  `scripts/cf_create_subdomain.py` manualmente, fuera de CI;
- o construir/previsualizar el sitio Astro en local.

## 1. Prerrequisitos de stack

| Herramienta | Versión | Para qué |
|---|---|---|
| Node.js | 20.x | Build de Astro (`sites/`), tests con Vitest |
| Python | 3.12 | Scripts de `scripts/` (validación, Blogger, IndexNow) |
| Git | cualquiera reciente | Clonar y trabajar con el repo |
| GitHub CLI (`gh`) | cualquiera reciente | Operaciones manuales sobre Pages/Actions (opcional) |

Estas versiones son las mismas que usa `.github/workflows/deploy.yml` en
CI — no están fijadas en ningún `engines` de `package.json`, así que usa
exactamente estas para evitar diferencias de comportamiento.

Verificar lo instalado:

```bash
node --version    # debe ser v20.x
python3 --version # debe ser 3.12.x
git --version
gh --version      # opcional
```

## 2. Clonar y preparar el repo

```bash
git clone https://github.com/egileta/auto-citaciones.git
cd auto-citaciones

# Astro (sitio)
cd sites
npm ci
npm test            # 20/20 tests deberían pasar
npm run build       # SITE_TARGET=cloudflare por defecto
SITE_TARGET=github npm run build
cd ..

# Scripts Python
pip install -r scripts/requirements.txt
```

`npm run dev` (dentro de `sites/`) levanta el servidor de desarrollo de
Astro para previsualizar el sitio en local.

## 3. Autenticar `gh` CLI (opcional, solo para operaciones manuales)

Solo necesario si vas a ejecutar comandos `gh api ...` contra Pages/Actions
como los documentados en `docs/DEPLOYMENT.md`:

```bash
gh auth login
```

## 4. Credenciales para ejecutar los scripts en local (opcional)

Si solo vas a trabajar sobre el sitio Astro o el código, **no necesitas
ninguna credencial** — todo el despliegue real lo hace CI con los secrets
que ya están en GitHub.

Si vas a ejecutar en local `scripts/blogger_publish.py`,
`scripts/tumblr_publish.py`, `scripts/submit_indexnow.py`,
`scripts/cf_create_subdomain.py` o `scripts/generate_content.py`:

```bash
cp .env.example .env.local
# Edita .env.local con los valores reales (ver instrucciones dentro del
# fichero y docs/DEPLOYMENT.md para cómo obtener cada uno)
```

**Ya existe un `.env.local` en esta máquina** (creado 2026-07-19) con
`CLOUDFLARE_DNS_TOKEN` + `CLOUDFLARE_ZONE_ID` (verificados y activos) y las
5 credenciales de Tumblr (en producción, funcionando). Antes de pedirle
estas credenciales al usuario otra vez, comprobar primero si `.env.local`
ya las tiene:

```bash
cat .env.local  # o: grep -v '^#' .env.local | grep -v '^$'
```

Los campos de Blogger y del token de Pages de Cloudflare siguen vacíos
(son secrets de GitHub Actions de solo escritura, sus valores reales nunca
se han visto en una sesión de Claude Code — solo existen dentro de GitHub).
Si hace falta ejecutarlos en local, hay que regenerarlos siguiendo
`docs/DEPLOYMENT.md` y rellenar el fichero.

`.env.local` está en `.gitignore` — nunca se commitea. Antes de ejecutar
un script, carga las variables en el shell:

```bash
set -a; source .env.local; set +a
python3 scripts/validate_projects.py
```

**Importante:** los secrets de GitHub Actions son de solo escritura. Si no
guardaste los valores reales en otro sitio (gestor de contraseñas, notas
privadas) cuando los creaste, no hay forma de recuperarlos desde GitHub —
tendrás que regenerarlos:

- Tokens de Cloudflare: se pueden revocar y crear de nuevo sin tocar nada
  más (ver `docs/DEPLOYMENT.md` 1.3) — no afecta a lo que ya está
  desplegado, solo a quién puede desplegar.
- Refresh token de Blogger: repetir el flujo OAuth manual de
  `docs/DEPLOYMENT.md` 3.2. El client ID/secret de Google Cloud sí siguen
  siendo válidos, no hace falta recrearlos.
- OAuth token/token secret de Tumblr: repetir el flujo de
  `docs/DEPLOYMENT.md` 4.1 (Explore API en la página de la app). El
  Consumer Key/Secret siguen siendo válidos, no hace falta recrear la app.
- Si decides usar tokens/refresh token nuevos, actualiza también el secret
  correspondiente en GitHub (`gh secret set NOMBRE_SECRET`) para que CI siga
  funcionando.

## 5. Verificar que todo encaja

```bash
git status                  # debe estar limpio y al día con origin/main
git log --oneline -3
gh run list -L 3            # últimos despliegues en CI (requiere gh auth)
```

Si `git status` muestra el repo limpio y sincronizado con `origin/main`, y
`npm test`/`npm run build` pasan en local, el entorno nuevo está listo —
cualquier push a `main` se desplegará exactamente igual que desde la
máquina original.
