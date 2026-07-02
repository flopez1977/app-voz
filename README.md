# App-voz

Herramienta local de **text-to-speech que clona tu propia voz** y convierte cualquier
guion en audio (voz sola o con música de fondo). Todo corre en tu Mac, con tu propio
Claude Code. No hay servidores, ni cuentas, ni cuotas.

> Regalo para la comunidad. Sin cobro, sin mantenimiento, sin updates. Es tuyo:
> mejóralo con tu Claude si quieres.

## Requisitos

- **Mac con Apple Silicon** (M1/M2/M3/M4). Usa MLX/Metal — no funciona en Intel ni Windows (ver abajo).
- **Claude Code** instalado, con tu cuenta.
- Conexión a internet la primera vez (descarga el modelo, ~500 MB).

## Instalación (la hace Claude por ti)

1. Clona este repo y abre la carpeta en Claude Code.
2. Escribe **`/setup`** → Claude instala todo (Homebrew, ffmpeg, entorno Python, dependencias, modelo) y hace un test. Es idempotente: si algo falla, lo arregla y vuelve a lanzarlo.
3. Escribe **`/voz`** → graba tu voz leyendo el guion de `ref/guion-referencia.txt` (≥20s), o carga un clip propio.
4. Escribe **`/tts`** → abre el panel en `http://localhost:5050`.

En el panel: elige voz → pega tu guion → previsualiza el texto normalizado → genera →
revisa chunks y ajusta silencios → descarga (voz sola o voz + música).

Si algo va mal: **`/doctor`**.

## Calidad de la voz

Las voces por defecto (`voices/es-female`, `voices/es-male`) son **sintéticas**, solo
para probar. **La calidad real la consigues grabando tu propia voz** con una muestra
limpia de ≥20 segundos (guion fijo en `ref/`). Voz limpia = mejor clon.

⚠️ Clona solo **tu propia voz** o una que tengas permiso explícito para usar.

## Música

En `music/` hay pistas de ejemplo (licencia Pixabay, redistribuibles — ver
`music/README.md`). Añade las tuyas dejándolas en esa carpeta; aparecen en el panel.

## Windows / Intel (no soportado de fábrica)

App-voz usa **MLX**, que es exclusivo de Apple Silicon. Para Windows/Linux o Mac Intel
hay que **cambiar el motor TTS**. El resto (normalizador, chunker, ensamblador, panel,
ffmpeg) es multiplataforma.

**Cómo portarlo (tu Claude puede hacerlo):**
1. Instala **XTTS v2 (Coqui TTS)** — también clona voz por muestra y va en Windows/Linux (mejor con GPU NVIDIA):
   `pip install TTS`
2. Reescribe `engine/tts_engine.py` manteniendo la **misma interfaz**:
   `speak(text, label, output_dir, voice_profile, speed=0.9, dry_run=False) -> str | None`
   y `resolve_profile(voice_profile) -> (ref_wav_path, ref_text)`.
   Dentro, en vez de MLX, llama a XTTS v2 con `speaker_wav=<reference.wav>` y `language="es"`.
3. Quita el chequeo `arm64` de `scripts/bootstrap.sh` y ajusta dependencias.
4. Todo lo demás sigue igual.

Aviso honesto: la calidad y el comportamiento no serán idénticos al MLX, y sin GPU va
más lento. Pero funciona.

## Estructura

```
engine/      normalizer · chunker · tts_engine · assembler
dashboard/   panel Flask + SSE
scripts/     bootstrap.sh
.claude/     comandos (/setup /voz /tts /doctor) + skill voz-forge
voices/      perfiles de voz (reference.wav + reference.txt)
music/       pistas Pixabay + las tuyas
ref/         guion-referencia.txt
```

## Licencia

Código: MIT (ver `LICENSE`). Música: licencias propias (ver `music/README.md`).
