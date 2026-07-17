# v1.0 — TecladoSounds

## 🚀 Novedades

### Interfaz gráfica (CustomTkinter)
- Ventana moderna con modo oscuro (#1a1b26)
- Logo en cabecera y en icono de bandeja
- Lista de perfiles con scroll, tarjeta de información
- Control de volumen con slider
- Botón único Iniciar/Detener (verde ↔ rojo)
- Ajustes en la misma ventana (sin popups), con acceso desde engranaje
- Vista de ajustes inline: iniciar con Windows, auto-start motor, volumen predeterminado

### Bandeja del sistema (pystray)
- Minimizar al cerrar la ventana
- Menú contextual: Abrir, Ajustes, Cerrar
- Logo personalizado como icono de bandeja

### Sonido
- 17+ perfiles de switches reales (MX Blue, Brown, Holy Panda, Alpaca, NK Cream, etc.)
- Audio a 44100 Hz con pygame
- Cambio de perfil en tiempo real sin detener el sonido
- Volumen ajustable incluso con sonido activo

### Sistema
- Compilado con PyInstaller --onefile (26.5 MB, sin dependencias)
- Auto-inicio con Windows (acceso directo en Startup)
- Inicio automático de sonido al abrir la app
- Configuración persistente en config.json

### Correcciones de bugs
- Perfiles ahora cambian en tiempo real al hacer clic (no requería reiniciar)
- Icono de ventana y barra de tareas ahora usa Logo.png
- Ventana de ajustes desde bandeja con título oscuro (DWM API)
- Paths corregidos para soporte PyInstaller (frozen + dev)
- Eliminada función de cambio de perfil desde bandeja (solo desde interfaz)

## 📦 Descarga

- **TecladoSounds.exe** — Portable, solo ejecutar (Windows)
