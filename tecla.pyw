#! python3.12
import os, sys, json, yaml, random, subprocess, threading
from pathlib import Path
from pynput.keyboard import Listener, Key, KeyCode

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

from PIL import Image, ImageDraw, ImageTk
import pystray


if getattr(sys, 'frozen', False):
    _BASE = Path(sys.executable).parent
    _MEI = Path(sys._MEIPASS)
else:
    _BASE = Path(__file__).parent
    _MEI = _BASE

def _res(name):
    p = _MEI / name
    return p if p.exists() else _BASE / name

PERFILES_DIR = _res("keyboardsounds") / "profiles"
CONFIG_PATH = _BASE / "config.json"
LNK_NAME = "TecladoSounds.lnk"
LOGO_PATH = _res("Logo.png")
_SCRIPT = _BASE / "TecladoSounds.exe" if getattr(sys, 'frozen', False) else Path(__file__).resolve()


class Perfil:
    def __init__(self, ruta):
        with open(ruta / "profile.yaml") as f:
            cfg = yaml.safe_load(f)
        self.nombre = cfg.get("profile", {}).get("name", ruta.name)
        self.autor = cfg.get("profile", {}).get("author", "")
        self.desc = cfg.get("profile", {}).get("description", "")
        self.device = cfg.get("profile", {}).get("device", "keyboard")
        self._sounds = {}
        self._key_map = {}
        self._defaults = []
        self._cargar_audio(ruta, cfg)
        self._cargar_mappings(cfg)

    def _cargar_audio(self, ruta, cfg):
        for src in cfg.get("sources", []):
            sid = src["id"]
            s = src["source"]
            if isinstance(s, dict):
                archivo = s.get("press")
                if not archivo:
                    continue
                self._sounds[(sid, "press")] = pygame.mixer.Sound(file=str(ruta / archivo))
            else:
                self._sounds[(sid, "press")] = pygame.mixer.Sound(file=str(ruta / s))

    def _cargar_mappings(self, cfg):
        keys = cfg.get("keys", {})
        d = keys.get("default", [])
        self._defaults = d if isinstance(d, list) else [d]
        for m in keys.get("other", []):
            snd = m["sound"]
            ids = snd if isinstance(snd, list) else [snd]
            for k in m["keys"]:
                self._key_map.setdefault(k, []).extend(ids)

    def obtener_sonido(self, tecla, accion="press"):
        if self.device != "keyboard":
            return None
        nombre = None
        if isinstance(tecla, Key):
            nombre = tecla.name
        elif isinstance(tecla, KeyCode) and tecla.char is not None:
            nombre = tecla.char
        else:
            nombre = str(tecla)
        sids = self._key_map.get(nombre, self._defaults)
        if not sids:
            return None
        sid = random.choice(sids)
        return self._sounds.get((sid, accion)) or self._sounds.get((sid, "press"))


def perfiles_disponibles():
    res = []
    for d in sorted(PERFILES_DIR.iterdir()):
        if not d.is_dir():
            continue
        try:
            with open(d / "profile.yaml") as f:
                cfg = yaml.safe_load(f)
            if cfg.get("profile", {}).get("device", "keyboard") != "keyboard":
                continue
            nombre = cfg.get("profile", {}).get("name", d.name)
            autor = cfg.get("profile", {}).get("author", "")
            desc = cfg.get("profile", {}).get("description", "")
            res.append((d.name, nombre, autor, desc))
        except Exception:
            pass
    return res


def cargar_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text("utf-8"))
        except Exception:
            pass
    return {"auto_start": False, "default_volume": 70, "last_profile": None, "auto_start_motor": False}


def guardar_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), "utf-8")


def acceso_inicio_path():
    startup = os.path.join(os.getenv("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    return os.path.join(startup, LNK_NAME)


def acceso_inicio_existe():
    return os.path.isfile(acceso_inicio_path())


def crear_acceso_inicio():
    if getattr(sys, 'frozen', False):
        ps = (
            '$ws = New-Object -ComObject WScript.Shell;'
            '$s = $ws.CreateShortcut(' + json.dumps(acceso_inicio_path()) + ');'
            '$s.TargetPath = ' + json.dumps(str(_SCRIPT)) + ';'
            '$s.WorkingDirectory = ' + json.dumps(str(_BASE)) + ';'
            '$s.Description = "TecladoSounds";'
            '$s.Save()'
        )
    else:
        ps = (
            '$ws = New-Object -ComObject WScript.Shell;'
            '$s = $ws.CreateShortcut(' + json.dumps(acceso_inicio_path()) + ');'
            '$s.TargetPath = "C:\\Windows\\pyw.exe";'
            '$s.Arguments = "-3.12 " + ' + json.dumps(str(_SCRIPT)) + ';'
            '$s.WorkingDirectory = ' + json.dumps(str(_SCRIPT.parent)) + ';'
            '$s.Description = "TecladoSounds";'
            '$s.Save()'
        )
    subprocess.run(["powershell", "-Command", ps], capture_output=True)


def eliminar_acceso_inicio():
    p = acceso_inicio_path()
    if os.path.isfile(p):
        os.remove(p)


def abrir_gui():
    import customtkinter as ctk

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    config = cargar_config()
    perfiles = perfiles_disponibles()
    motor = None
    listener_obj = None
    activo = False
    tray_icon = None
    perfil_seleccionado = None

    C = {
        "base": "#1a1b26", "surface": "#24252f", "overlay": "#2f3040",
        "text": "#c0caf5", "sub": "#565f89", "accent": "#7aa2f7",
        "green": "#9ece6a", "red": "#f7768e",
    }

    root = ctk.CTk()
    root.title("TecladoSounds")
    root.resizable(False, False)
    root.configure(fg_color=C["base"])

    try:
        logo_img = ctk.CTkImage(Image.open(LOGO_PATH), size=(32, 32))
        icon_tk = ImageTk.PhotoImage(Image.open(LOGO_PATH))
        root.iconphoto(True, icon_tk)
    except Exception:
        logo_img = None

    main = ctk.CTkFrame(root, fg_color=C["base"], corner_radius=0)
    main.pack(fill="both", expand=True, padx=20, pady=16)

    def abrir_settings():
        ventana = ctk.CTkToplevel(root)
        ventana.title("Configuración")
        ventana.resizable(False, False)
        ventana.configure(fg_color=C["base"])
        ventana.transient(root)
        ventana.grab_set()
        try:
            from ctypes import windll, byref, sizeof, c_int
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            windll.dwmapi.DwmSetWindowAttribute(
                windll.user32.GetParent(ventana.winfo_id()),
                DWMWA_USE_IMMERSIVE_DARK_MODE, byref(c_int(2)), sizeof(c_int))
        except Exception:
            pass

        cfg = cargar_config()
        f = ctk.CTkFrame(ventana, fg_color=C["base"], corner_radius=0)
        f.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(f, text="Configuración", font=("Segoe UI", 18, "bold"),
                     text_color=C["accent"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        var_auto = ctk.BooleanVar(value=acceso_inicio_existe())
        ctk.CTkCheckBox(f, text="Iniciar con Windows", variable=var_auto,
                        fg_color=C["accent"], hover_color=C["accent"],
                        font=("Segoe UI", 13), text_color=C["text"],
                        border_color=C["sub"]).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

        var_motor = ctk.BooleanVar(value=cfg.get("auto_start_motor", False))
        ctk.CTkCheckBox(f, text="Iniciar sonido automáticamente al abrir",
                        variable=var_motor, fg_color=C["accent"],
                        hover_color=C["accent"], font=("Segoe UI", 13),
                        text_color=C["text"], border_color=C["sub"]).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(0, 16))

        ctk.CTkLabel(f, text="Volumen predeterminado:", font=("Segoe UI", 13),
                     text_color=C["text"]).grid(row=3, column=0, sticky="w")

        vol_row = ctk.CTkFrame(f, fg_color="transparent")
        vol_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6, 22))

        slider_s = ctk.CTkSlider(vol_row, from_=0, to=100, number_of_steps=100,
                                 progress_color=C["accent"], button_color=C["accent"],
                                 button_hover_color=C["accent"], width=220)
        slider_s.set(cfg.get("default_volume", 70))
        slider_s.pack(side="left")

        lbl_pct_s = ctk.CTkLabel(vol_row, text=f"{int(slider_s.get())}%",
                                 font=("Segoe UI", 13, "bold"),
                                 text_color=C["accent"], width=40)
        lbl_pct_s.pack(side="left", padx=(8, 0))
        slider_s.configure(command=lambda v: lbl_pct_s.configure(text=f"{int(v)}%"))

        def guardar():
            c = cargar_config()
            c["default_volume"] = slider_s.get()
            c["auto_start_motor"] = var_motor.get()
            c["auto_start"] = var_auto.get()
            guardar_config(c)
            if var_auto.get():
                crear_acceso_inicio()
            else:
                eliminar_acceso_inicio()
            slider_vol.set(slider_s.get())
            ventana.destroy()

        btn_row = ctk.CTkFrame(f, fg_color="transparent")
        btn_row.grid(row=5, column=0, columnspan=2, pady=(4, 0))
        ctk.CTkButton(btn_row, text="Guardar", font=("Segoe UI", 12, "bold"),
                      fg_color=C["green"], hover_color="#8bc86a",
                      text_color=C["base"], corner_radius=8,
                      command=guardar, width=90, cursor="hand2").pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Cancelar", font=("Segoe UI", 12),
                      fg_color=C["overlay"], hover_color="#3a3d50",
                      text_color=C["text"], corner_radius=8,
                      command=ventana.destroy, width=90, cursor="hand2").pack(side="left")

    # === HEADER ===
    header = ctk.CTkFrame(main, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
    header.columnconfigure(0, weight=1)

    hdr_left = ctk.CTkFrame(header, fg_color="transparent")
    hdr_left.pack(side="left")
    if logo_img:
        ctk.CTkLabel(hdr_left, image=logo_img, text="").pack(side="left", padx=(0, 10))
    lbl_titulo = ctk.CTkLabel(hdr_left, text="TecladoSounds",
                              font=("Segoe UI", 20, "bold"), text_color=C["text"])
    lbl_titulo.pack(side="left")

    btn_header = ctk.CTkButton(header, text="\u2699", font=("Segoe UI", 16),
                               fg_color="transparent", hover_color=C["overlay"],
                               text_color=C["sub"], width=36, height=36,
                               corner_radius=8, cursor="hand2")
    btn_header.pack(side="right")

    # === CONTENEDOR DE VISTAS ===
    content = ctk.CTkFrame(main, fg_color="transparent")
    content.grid(row=1, column=0, sticky="nsew")
    main.columnconfigure(0, weight=1)
    main.rowconfigure(1, weight=1)

    # --- VISTA PRINCIPAL ---
    view_main = ctk.CTkFrame(content, fg_color="transparent")

    body = ctk.CTkFrame(view_main, fg_color="transparent")
    body.pack(fill="both", expand=True)
    body.columnconfigure(1, weight=1)

    card_lista = ctk.CTkFrame(body, fg_color=C["surface"], corner_radius=12)
    card_lista.grid(row=0, column=0, sticky="ns", padx=(0, 12))

    ctk.CTkLabel(card_lista, text="PERFILES", font=("Segoe UI", 12, "bold"),
                 text_color=C["sub"]).pack(anchor="nw", padx=16, pady=(14, 6))

    scroll_frame = ctk.CTkScrollableFrame(
        card_lista, fg_color="transparent", corner_radius=0,
        scrollbar_button_hover_color=C["accent"], width=200
    )
    scroll_frame.pack(fill="both", expand=True, padx=6, pady=(0, 10))

    profile_buttons = []
    profile_dirs = []

    def on_profile_click(dir_name):
        nonlocal perfil_seleccionado
        perfil_seleccionado = dir_name
        for dn, btn in zip(profile_dirs, profile_buttons):
            if dn == dir_name:
                btn.configure(fg_color=C["accent"], text_color=C["base"],
                              hover_color=C["accent"])
            else:
                btn.configure(fg_color="transparent", text_color=C["text"],
                              hover_color=C["overlay"])
        d = next(p for p in perfiles if p[0] == dir_name)
        lbl_nombre.configure(text=d[1])
        lbl_autor.configure(text=d[2])
        lbl_desc.configure(text=d[3])
        if activo:
            detener_motor()
            iniciar_motor_por_perfil(dir_name)

    for dir_name, nombre, autor, desc in perfiles:
        btn = ctk.CTkButton(
            scroll_frame, text=nombre, anchor="w",
            fg_color="transparent", text_color=C["text"],
            hover_color=C["overlay"], corner_radius=8, height=36,
            command=lambda dn=dir_name: on_profile_click(dn)
        )
        btn.pack(fill="x", padx=4, pady=2)
        profile_buttons.append(btn)
        profile_dirs.append(dir_name)

    card_info = ctk.CTkFrame(body, fg_color=C["surface"], corner_radius=12)
    card_info.grid(row=0, column=1, sticky="nsew")

    info_padx = 16
    ctk.CTkLabel(card_info, text="INFORMACIÓN", font=("Segoe UI", 12, "bold"),
                 text_color=C["sub"]).pack(anchor="nw", padx=info_padx, pady=(14, 10))

    lbl_nombre = ctk.CTkLabel(card_info, text="", font=("Segoe UI", 16, "bold"),
                              text_color=C["text"], anchor="w", justify="left")
    lbl_nombre.pack(fill="x", padx=info_padx)

    lbl_autor = ctk.CTkLabel(card_info, text="", font=("Segoe UI", 12),
                             text_color=C["sub"], anchor="w", justify="left")
    lbl_autor.pack(fill="x", padx=info_padx, pady=(2, 0))

    lbl_desc = ctk.CTkLabel(card_info, text="", font=("Segoe UI", 13),
                            text_color=C["text"], anchor="w", justify="left",
                            wraplength=260)
    lbl_desc.pack(fill="x", padx=info_padx, pady=(10, 16))

    ctrl = ctk.CTkFrame(view_main, fg_color="transparent")
    ctrl.pack(fill="x", pady=(14, 0))

    ctrl_inner = ctk.CTkFrame(ctrl, fg_color=C["surface"], corner_radius=12)
    ctrl_inner.pack(fill="x")

    top_row = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
    top_row.pack(fill="x", padx=16, pady=(12, 4))

    ctk.CTkLabel(top_row, text="Volumen", font=("Segoe UI", 12, "bold"),
                 text_color=C["sub"]).pack(side="left", padx=(0, 12))

    slider_vol = ctk.CTkSlider(top_row, from_=0, to=100, number_of_steps=100,
                               progress_color=C["accent"], button_color=C["accent"],
                               button_hover_color=C["accent"], width=180)
    slider_vol.set(config.get("default_volume", 70))
    slider_vol.pack(side="left", padx=(0, 8))

    lbl_vol = ctk.CTkLabel(top_row, text=f"{int(slider_vol.get())}%",
                           font=("Segoe UI", 13, "bold"),
                           text_color=C["accent"], width=36)
    lbl_vol.pack(side="left")
    slider_vol.configure(command=lambda v: lbl_vol.configure(text=f"{int(v)}%"))

    bot_row = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
    bot_row.pack(fill="x", padx=16, pady=(4, 12))

    btn_toggle = ctk.CTkButton(bot_row, text="Iniciar", font=("Segoe UI", 13, "bold"),
                               fg_color=C["green"], hover_color="#8bc86a",
                               text_color=C["base"], corner_radius=8,
                               height=38, width=110, cursor="hand2")
    btn_toggle.pack(side="left")

    lbl_estado = ctk.CTkLabel(bot_row, text="Detenido", font=("Segoe UI", 12),
                              text_color=C["sub"])
    lbl_estado.pack(side="right")
    view_main.pack(fill="both", expand=True)

    # --- VISTA AJUSTES (en-panel) ---
    view_settings = ctk.CTkFrame(content, fg_color=C["surface"], corner_radius=12)

    settings_content = ctk.CTkFrame(view_settings, fg_color="transparent")
    settings_content.pack(fill="both", expand=True, padx=28, pady=24)

    ctk.CTkLabel(settings_content, text="Configuración", font=("Segoe UI", 18, "bold"),
                 text_color=C["accent"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

    cfg = cargar_config()
    var_auto = ctk.BooleanVar(value=acceso_inicio_existe())
    ctk.CTkCheckBox(settings_content, text="Iniciar con Windows", variable=var_auto,
                    fg_color=C["accent"], hover_color=C["accent"],
                    font=("Segoe UI", 13), text_color=C["text"],
                    border_color=C["sub"]).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

    var_motor = ctk.BooleanVar(value=cfg.get("auto_start_motor", False))
    ctk.CTkCheckBox(settings_content, text="Iniciar sonido automáticamente al abrir",
                    variable=var_motor, fg_color=C["accent"],
                    hover_color=C["accent"], font=("Segoe UI", 13),
                    text_color=C["text"], border_color=C["sub"]).grid(
        row=2, column=0, columnspan=2, sticky="w", pady=(0, 16))

    ctk.CTkLabel(settings_content, text="Volumen predeterminado:", font=("Segoe UI", 13),
                 text_color=C["text"]).grid(row=3, column=0, sticky="w")

    vol_row = ctk.CTkFrame(settings_content, fg_color="transparent")
    vol_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6, 22))

    slider_s = ctk.CTkSlider(vol_row, from_=0, to=100, number_of_steps=100,
                             progress_color=C["accent"], button_color=C["accent"],
                             button_hover_color=C["accent"], width=220)
    slider_s.set(cfg.get("default_volume", 70))
    slider_s.pack(side="left")

    lbl_pct_s = ctk.CTkLabel(vol_row, text=f"{int(slider_s.get())}%",
                             font=("Segoe UI", 13, "bold"),
                             text_color=C["accent"], width=40)
    lbl_pct_s.pack(side="left", padx=(8, 0))
    slider_s.configure(command=lambda v: lbl_pct_s.configure(text=f"{int(v)}%"))

    def guardar_settings():
        c = cargar_config()
        c["default_volume"] = slider_s.get()
        c["auto_start_motor"] = var_motor.get()
        c["auto_start"] = var_auto.get()
        guardar_config(c)
        if var_auto.get():
            crear_acceso_inicio()
        else:
            eliminar_acceso_inicio()
        slider_vol.set(slider_s.get())
        volver_main()

    btn_row_s = ctk.CTkFrame(settings_content, fg_color="transparent")
    btn_row_s.grid(row=5, column=0, columnspan=2, pady=(4, 0))
    ctk.CTkButton(btn_row_s, text="Guardar", font=("Segoe UI", 12, "bold"),
                  fg_color=C["green"], hover_color="#8bc86a",
                  text_color=C["base"], corner_radius=8,
                  command=guardar_settings, width=90, cursor="hand2").pack(side="left", padx=(0, 8))
    ctk.CTkButton(btn_row_s, text="Volver", font=("Segoe UI", 12),
                  fg_color=C["overlay"], hover_color="#3a3d50",
                  text_color=C["text"], corner_radius=8,
                  command=lambda: volver_main(), width=90, cursor="hand2").pack(side="left")

    def mostrar_settings():
        view_main.pack_forget()
        view_settings.pack(fill="both", expand=True)
        btn_header.configure(text="\u2190", command=volver_main)

    def volver_main():
        view_settings.pack_forget()
        view_main.pack(fill="both", expand=True)
        btn_header.configure(text="\u2699", command=mostrar_settings)

    btn_header.configure(command=mostrar_settings)

    # === LÓGICA DE PERFIL ===
    ultimo = config.get("last_profile")
    idx_inicial = 0
    for i, (dn, _, _, _) in enumerate(perfiles):
        if ultimo and dn == ultimo:
            idx_inicial = i
            break

    root.after(50, lambda: on_profile_click(perfiles[idx_inicial][0]))

    def iniciar_motor_por_perfil(dir_name):
        nonlocal motor, listener_obj, activo
        ruta = PERFILES_DIR / dir_name
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=2048)
            pygame.mixer.set_num_channels(24)
            motor = Perfil(ruta)
        except Exception as e:
            lbl_estado.configure(text=f"Error: {e}", text_color=C["red"])
            return

        def on_press(key):
            try:
                s = motor.obtener_sonido(key)
                if s:
                    s.set_volume(slider_vol.get() / 100.0)
                    s.play()
            except Exception:
                pass

        listener_obj = Listener(on_press=on_press)
        listener_obj.start()
        activo = True
        lbl_estado.configure(text=f"Activo  \u2022  {motor.nombre}", text_color=C["green"])
        btn_toggle.configure(text="Detener", fg_color=C["red"], hover_color="#e06a8a")
        slider_vol.configure(state="disabled")
        for b in profile_buttons:
            b.configure(state="disabled")

        c = cargar_config()
        c["last_profile"] = dir_name
        guardar_config(c)

    def detener_motor():
        nonlocal motor, listener_obj, activo
        if listener_obj:
            listener_obj.stop()
            listener_obj = None
        if motor:
            try:
                pygame.mixer.quit()
            except Exception:
                pass
            motor = None
        activo = False
        lbl_estado.configure(text="Detenido", text_color=C["sub"])
        btn_toggle.configure(text="Iniciar", fg_color=C["green"], hover_color="#8bc86a")
        slider_vol.configure(state="normal")
        for b in profile_buttons:
            b.configure(state="normal")

    def toggle_motor():
        if activo:
            detener_motor()
        else:
            if not perfil_seleccionado:
                return
            iniciar_motor_por_perfil(perfil_seleccionado)

    btn_toggle.configure(command=toggle_motor)

    def mostrar_ventana():
        root.deiconify()

    def salir():
        detener_motor()
        if tray_icon:
            tray_icon.stop()
        root.destroy()

    def init_tray():
        nonlocal tray_icon
        try:
            img = Image.open(LOGO_PATH).resize((64, 64), Image.LANCZOS)
        except Exception:
            img = Image.new("RGBA", (64, 64), (0x7A, 0xA2, 0xF7, 255))
        menu = pystray.Menu(
            pystray.MenuItem("Abrir", lambda: root.after(0, mostrar_ventana)),
            pystray.MenuItem("Ajustes", lambda: root.after(0, abrir_settings)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Cerrar", lambda: root.after(0, salir)),
        )
        tray_icon = pystray.Icon("tecladosounds", img, "TecladoSounds", menu)
        threading.Thread(target=tray_icon.run, daemon=True).start()

    root.after(100, init_tray)

    def on_cerrar():
        root.withdraw()

    root.protocol("WM_DELETE_WINDOW", on_cerrar)

    if config.get("auto_start_motor"):
        root.after(500, toggle_motor)

    root.mainloop()


if __name__ == "__main__":
    abrir_gui()
