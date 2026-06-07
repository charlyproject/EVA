# Guía de publicación en GitHub — EVA

Esta guía explica paso a paso cómo inicializar el repositorio local, subir el código a GitHub y hacer el primer push. Cada comando está documentado con lo que hace y qué esperar.

---

## Prerrequisitos

1. **Git instalado** → https://git-scm.com/downloads  
   Verifica: `git --version`

2. **GitHub CLI (opcional pero recomendado)** → https://cli.github.com  
   Permite crear el repositorio remoto sin salir de la terminal.  
   Verifica: `gh --version`

3. **Cuenta en GitHub** → https://github.com

---

## Paso 1 — Preparar el directorio limpio

Antes de inicializar Git, asegúrate de haber eliminado los archivos que no deben subirse:

```
ELIMINAR antes del primer commit:
  .venv/                     ← entorno virtual Python
  __pycache__/               ← cache de bytecode Python
  .idea/  .compass/  .junie/  .opencode/  ← carpetas de IDE/herramientas
  build/  dist/  _internal/  build_uninstall/  ← artefactos de compilación
  cache/  logs/  backups/    ← datos en tiempo de ejecución
  *.rar  main.rar  EVA.rar   ← archivos comprimidos
  *.bak  *.bak_think  *.backup ← archivos temporales
  eva_errors.log             ← log vacío
  Desktop.ini                ← metadato de Windows
  piper/  ffmpeg/  models/   ← binarios pesados (ya en .gitignore)
  restaurar_solo_eva.py      ← script interno de backup
  generar_backup_solo_app.py ← script interno de backup
  ANALISIS_MERCADO_EVA_v1.0.md ← análisis interno de mercado
  INFORME_AUDITORIA_EVA.md   ← informe interno

SPEC duplicados — conserva solo EVA.spec y elimina:
  EVA_new.spec               ← antiguo
  EVA.spec.backup            ← backup de spec

ARCHIVOS CON DATOS LOCALES (ya cubiertos por .gitignore):
  config/hardware_cache.json
  config/session.dat
  config/install_config.json.bak
  config/update_state.json
  config/paths.json              ← contiene rutas locales y API keys (usa paths.example.json como plantilla)

MOVER A docs/ (si no están ya):
  EVA_COMANDOS_COMPLETOS.md   → docs/
  GUIA_TRABAJO_BUILD_AUTOMATIZADO.md → docs/
  INFORME_DETALLADO_SETUP_EVA.md → docs/
  PROJECT_TREE.md             → docs/ (o eliminar si está desactualizado)
```

---

## Paso 2 — Inicializar el repositorio local

```bash
cd "C:\ruta\al\proyecto\EVA"
```
> Sitúa la terminal en la raíz del proyecto EVA.

```bash
git init
```
> Crea la carpeta `.git/` oculta en el directorio actual.  
> **Resultado esperado:** `Initialized empty Git repository in /ruta/al/proyecto/EVA/.git/`

```bash
git config user.name "cHArLy"
git config user.email "tu@email.com"
```
> Establece tu identidad para los commits de este repositorio.  
> (Usa `--global` si quieres aplicarlo a todos los repos.)

---

## Paso 3 — Primer commit

```bash
git add .
```
> Añade al área de staging todos los archivos **no excluidos por `.gitignore`**.  
> **Comprueba qué se va a incluir antes de hacer commit:**

```bash
git status
```
> Lista los archivos que serán incluidos (verde) y los ignorados.  
> Revisa que NO aparezcan: `.venv`, `piper/`, `models/`, `build/`, `cache/`, `logs/`, etc.  
> Si aparece algo que no debería, agrégalo a `.gitignore` y vuelve a ejecutar `git add .`.

```bash
git commit -m "feat: initial release - EVA v1.0.0"
```
> Crea el primer snapshot del proyecto con el mensaje indicado.  
> **Resultado esperado:** algo como `[main (root-commit) a1b2c3d] feat: initial release - EVA v1.0.0`

---

## Paso 4 — Crear el repositorio en GitHub

### Opción A: Con GitHub CLI (recomendado)

```bash
gh auth login
```
> Autenticación con tu cuenta GitHub. Sigue el asistente interactivo.  
> Elige: `GitHub.com` → `HTTPS` → `Login with a web browser`.

```bash
gh repo create EVA --public --description "Local voice assistant for Windows — Vosk + Piper TTS + Ollama + PySide6" --source=. --remote=origin --push
```
> **Lo que hace este comando:**
> - Crea el repositorio público `EVA` en tu cuenta de GitHub.
> - Lo vincula como `origin` al repo local.
> - Hace el primer push automáticamente.
>
> **Resultado esperado:** URL del repo, ej. `https://github.com/cHArLy/EVA`

Si prefieres crearlo **privado**: cambia `--public` por `--private`.

---

### Opción B: Sin GitHub CLI (manual)

1. Ve a https://github.com/new  
2. Nombre del repositorio: `EVA`  
3. Descripción: `Local voice assistant for Windows — Vosk + Piper TTS + Ollama + PySide6`  
4. Visibilidad: **Public**  
5. **No marques** "Add a README file" ni "Add .gitignore" (ya los tienes).  
6. Clic en **Create repository**.

Luego en tu terminal:

```bash
git remote add origin https://github.com/TU_USUARIO/EVA.git
```
> Vincula tu repositorio local con el remoto recién creado.  
> `origin` es el nombre estándar para el remoto principal.

```bash
git branch -M main
```
> Renombra la rama actual a `main` (estándar moderno de GitHub).

```bash
git push -u origin main
```
> Sube todos los commits al repositorio remoto.  
> `-u` establece `origin/main` como rama de seguimiento (los futuros `git push` no necesitarán argumentos).  
> **Resultado esperado:** progreso de subida y URL del repositorio.

---

## Paso 5 — Flujo de trabajo habitual tras la primera subida

```bash
# Ver qué has cambiado
git status

# Ver los cambios en detalle
git diff

# Añadir todos los cambios al staging
git add .

# O añadir un archivo específico
git add main.py

# Crear commit
git commit -m "fix: corregir bug en reconocimiento de voz"

# Subir al remoto
git push
```

### Convención de mensajes de commit recomendada

```
feat:     nueva funcionalidad
fix:      corrección de bug
docs:     cambios solo en documentación
refactor: refactorización de código
chore:    tareas de mantenimiento (gitignore, dependencias…)
```

---

## Paso 6 — Extras recomendados

### Añadir una captura de pantalla al README

1. Haz una captura de la interfaz de EVA con `Win+Shift+S` y guárdala como `docs/screenshot.png`.
2. En `README.md`, sustituye el comentario de screenshot por:

```markdown
![EVA - Ventana principal](docs/screenshot.png)
```

### Añadir topic tags en GitHub

Una vez subido el repo, ve a la página principal → engranaje junto a "About" → añade topics:
```
python, voice-assistant, pyside6, ollama, vosk, piper-tts, windows, offline-ai, spanish, bilingual
```

### Verificar que el .gitignore funciona correctamente

```bash
# Ver todos los archivos que Git está ignorando
git status --ignored

# Ver si un archivo específico está siendo ignorado y por qué regla
git check-ignore -v piper/piper.exe
git check-ignore -v .venv
```

---

## Resumen de archivos creados/modificados por esta guía

| Archivo | Estado | Propósito |
|---------|--------|-----------|
| `.gitignore` | ✅ Nuevo | Excluye binarios, cache, venv, logs |
| `LICENSE.txt` | ✅ Actualizado | MIT limpio sin sección comercial |
| `README.md` | ✅ Actualizado | Badges, corrección offline, guía completa |
| `README_EN.md` | ✅ Nuevo | Versión en inglés |
| `download_models.bat` | ✅ Nuevo | Descarga automática de binarios/modelos |
| `requirements_extra.md` | ✅ Nuevo | Guía manual de recursos externos |
| `docs/GITHUB_SETUP.md` | ✅ Este archivo | Guía de comandos Git |
