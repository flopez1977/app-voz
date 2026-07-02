# Voces

Cada perfil de voz es una carpeta con:

```
voices/<nombre>/
├── reference.wav   # muestra mono 24kHz de la voz a clonar (≥20s recomendado)
└── reference.txt   # transcripción exacta de reference.wav
```

## Voces por defecto (sintéticas)

`es-female/` y `es-male/` son voces **sintéticas** generadas con la variante
VoiceDesign del modelo (ver `scripts/make_default_voices.py`). Sirven para probar la
herramienta sin grabar nada. **No son personas reales.**

La **calidad real** la consigues con tu propia voz: ejecuta `/voz` en Claude Code y
graba el guion de `ref/guion-referencia.txt` (≥20s, entorno silencioso).

## Tus voces

Las que crees con `/voz` se guardan como `voices/user-<nombre>/` y git las ignora
(no se comparten). Cada persona genera las suyas en su propia máquina.
