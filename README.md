# TecladoSounds

Simulador ligero de sonidos de teclado mecánico. Elige entre múltiples perfiles ( switches ) y escucha el sonido de cada tecla mientras escribes.

![TecladoSounds](Logo.png)

## Características

- **17+ perfiles** de switches mecánicos y teclados reales (MX Blue, MX Brown, Holy Panda, Alpaca, etc.)
- **Interfaz gráfica moderna** con modo oscuro
- **Icono en bandeja del sistema** para acceso rápido
- **Cambio de perfil en tiempo real** sin detener la reproducción
- **Control de volumen** desde la interfaz
- **Inicio automático** con Windows (opcional)
- **Inicio automático de sonido** al abrir la aplicación (opcional)
- **Sin dependencias externas** en la versión compilada

## Descarga

### Versión compilada (recomendada)
Descarga el archivo `dist/TecladoSounds.exe`, cópialo a cualquier carpeta y ejecútalo.

### Desde código fuente
```
git clone https://github.com/NobinGJ/tecladosound.git
cd tecladosound
pip install -r requirements.txt
python tecla.pyw
```

## Compilación

Para compilar tu propio ejecutable desde el código fuente:

```bash
pip install pyinstaller
pyinstaller --onefile --name TecladoSounds --noconsole --icon Logo.png --add-data "Logo.png;." --add-data "keyboardsounds\profiles;keyboardsounds\profiles" tecla.pyw
```

El ejecutable se generará en `dist/TecladoSounds.exe`.

## Requisitos para desarrollo

- **Python 3.12+**
- Dependencias (ver `requirements.txt`):
  - `customtkinter`
  - `pygame`
  - `pynput`
  - `pystray`
  - `Pillow`
  - `PyYAML`
  - `pyinstaller` (solo para compilar)

### Instalación del entorno

```bash
python -m venv venv
.\venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## Uso

1. Ejecuta `TecladoSounds.exe` (o `python tecla.pyw`)
2. Selecciona un perfil de la lista izquierda
3. Presiona **Iniciar**
4. Escribe en cualquier programa — escucharás el sonido del switch seleccionado
5. Cambia de perfil en cualquier momento sin detener el sonido
6. Usa el deslizador de volumen para ajustar la intensidad

### Bandeja del sistema
- Al cerrar la ventana, la aplicación se minimiza a la bandeja
- Haz clic derecho en el icono para Abrir / Ajustes / Cerrar

## Añadir un perfil personalizado

1. Crea una carpeta en `keyboardsounds/profiles/mi-perfil/`
2. Agrega tus archivos de audio (`.wav` o `.ogg`)
3. Crea un archivo `profile.yaml` con la configuración:

```yaml
profile:
  name: "Mi Switch"
  author: "Tu Nombre"
  description: "Descripción del sonido"
  device: keyboard

sources:
  - id: default
    source: tecla.wav

keys:
  default: [default]
```

## Estructura del proyecto

```
tecladosound/
├── dist/
│   └── TecladoSounds.exe    # Versión compilada
├── keyboardsounds/
│   └── profiles/             # Perfiles de sonido
├── docs/                     # Sitio web (GitHub Pages)
│   ├── index.html
│   └── _config.yml
├── tecla.pyw                 # Aplicación principal
├── Logo.png                  # Logotipo
├── config.json               # Configuración (se genera solo)
├── requirements.txt
└── README.md
```

## Licencia

Este proyecto incluye perfiles de sonido basados en [keyboardsounds](https://github.com/keyboardsounds/keyboardsounds) y otros. Cada perfil puede tener su propia licencia.
