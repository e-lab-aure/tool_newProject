#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lanceur de nouveaux projets.
Cree le dossier, etablit un hard link vers CLAUDE.md et ouvre un terminal.
"""

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import logging

# --- Chemins ---
# Quand l'application est compilee avec PyInstaller, __file__ pointe vers le
# dossier temporaire d'extraction. On utilise sys.executable pour obtenir
# le vrai emplacement de l'exe.
if getattr(sys, "frozen", False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "launcher_config.json")
LOG_FILE    = os.path.join(SCRIPT_DIR, "launcher.log")

# --- Palette ---
C = {
    "bg":        "#111827",
    "surface":   "#1f2937",
    "border":    "#374151",
    "primary":   "#6366f1",
    "primary_h": "#4f46e5",
    "text":      "#f9fafb",
    "text_dim":  "#9ca3af",
    "success":   "#22c55e",
    "error":     "#ef4444",
    "warning":   "#f59e0b",
    "btn_mod":   "#1e3a5f",
    "btn_mod_h": "#1e4a7a",
}


# --------------------------------------------------------------------------- #
#  Configuration                                                                #
# --------------------------------------------------------------------------- #

def _default_config() -> dict:
    """Retourne la configuration par defaut avec le chemin CLAUDE.md local."""
    return {
        "claude_md_source": os.path.join(SCRIPT_DIR, "CLAUDE.md"),
        "projects_dir":     SCRIPT_DIR,
    }


def load_config() -> dict:
    """Charge la configuration JSON, ou retourne les valeurs par defaut."""
    default = _default_config()
    if not os.path.exists(CONFIG_FILE):
        return default
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key, val in default.items():
            data.setdefault(key, val)
        return data
    except (json.JSONDecodeError, IOError) as e:
        logging.error("Erreur lecture config: %s", e)
        return default


def save_config(config: dict) -> None:
    """Persiste la configuration dans le fichier JSON."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logging.info("Configuration sauvegardee")
    except IOError as e:
        logging.error("Erreur sauvegarde config: %s", e)
        raise


# --------------------------------------------------------------------------- #
#  Validation                                                                   #
# --------------------------------------------------------------------------- #

# Noms reserves par Windows pour les noms de fichiers/dossiers
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

# Caracteres interdits dans les noms de dossiers Windows
_FORBIDDEN_CHARS = r'\/:*?"<>|'


def validate_project_name(name: str) -> tuple:
    """
    Verifie que le nom est acceptable comme nom de dossier Windows.
    Retourne (True, "") si valide, (False, message) sinon.
    """
    if not name:
        return False, "Le nom ne peut pas etre vide."
    for c in _FORBIDDEN_CHARS:
        if c in name:
            return False, f"Caractere interdit : '{c}'"
    if name.upper() in _WINDOWS_RESERVED:
        return False, f"Nom reserve par Windows : {name}"
    if name[-1] in (".", " "):
        return False, "Le nom ne peut pas se terminer par un point ou un espace."
    return True, ""


# --------------------------------------------------------------------------- #
#  Helpers UI                                                                   #
# --------------------------------------------------------------------------- #

def _truncate(path: str, max_len: int = 52) -> str:
    """Tronque un chemin long pour l'affichage."""
    return path if len(path) <= max_len else f"...{path[-(max_len - 3):]}"


def _bind_hover(widget, normal_bg: str, hover_bg: str) -> None:
    """Ajoute un effet de survol sur un bouton."""
    widget.bind("<Enter>", lambda _: widget.config(bg=hover_bg))
    widget.bind("<Leave>", lambda _: widget.config(bg=normal_bg))


# --------------------------------------------------------------------------- #
#  Fenetre principale                                                            #
# --------------------------------------------------------------------------- #

class ProjectLauncher(tk.Tk):
    """Interface principale du lanceur de projets."""

    def __init__(self):
        super().__init__()
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format="[%(levelname)s] %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.cfg = load_config()
        self._build_ui()
        self._refresh_source_status()
        # Alerte differee pour laisser la fenetre s'afficher
        self.after(150, self._startup_check)
        logging.info("Lanceur demarre")

    # ---------------------------------------------------------------------- #
    #  Construction de l'interface                                             #
    # ---------------------------------------------------------------------- #

    def _build_ui(self) -> None:
        """Assemble tous les widgets de la fenetre."""
        self.title("Nouveau Projet")
        self.configure(bg=C["bg"])
        self.resizable(False, False)

        w, h = 460, 290
        self.geometry(f"{w}x{h}")
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        pad_x = 28

        # Titre
        tk.Label(
            self, text="Nouveau Projet",
            bg=C["bg"], fg=C["text"],
            font=("Segoe UI", 15, "bold"),
        ).pack(pady=(28, 2))

        tk.Label(
            self, text="Entrez le nom du dossier projet",
            bg=C["bg"], fg=C["text_dim"],
            font=("Segoe UI", 9),
        ).pack()

        # Champ de saisie du nom
        self.name_var = tk.StringVar()
        self.name_var.trace_add("write", self._on_name_change)

        entry_wrap = tk.Frame(self, bg=C["bg"])
        entry_wrap.pack(fill="x", padx=pad_x, pady=(10, 0))

        self.name_entry = tk.Entry(
            entry_wrap,
            textvariable=self.name_var,
            bg=C["surface"], fg=C["text"],
            insertbackground=C["text"],
            relief="flat", font=("Segoe UI", 12),
            highlightthickness=1,
            highlightbackground=C["border"],
            highlightcolor=C["primary"],
        )
        self.name_entry.pack(fill="x", ipady=9, ipadx=8)
        self.name_entry.bind("<Return>", lambda _e: self._create_project())
        self.name_entry.focus_set()

        # Label d'erreur inline sous le champ
        self.err_var = tk.StringVar()
        tk.Label(
            self, textvariable=self.err_var,
            bg=C["bg"], fg=C["error"],
            font=("Segoe UI", 8), anchor="w",
        ).pack(fill="x", padx=pad_x, pady=(3, 0))

        # Bouton principal
        self.create_btn = tk.Button(
            self, text="Creer le projet",
            bg=C["primary"], fg="white",
            activebackground=C["primary_h"], activeforeground="white",
            relief="flat", bd=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            command=self._create_project,
            padx=20, pady=9,
        )
        self.create_btn.pack(fill="x", padx=pad_x, pady=(10, 0))
        _bind_hover(self.create_btn, C["primary"], C["primary_h"])

        # Separateur
        tk.Frame(self, bg=C["border"], height=1).pack(
            fill="x", padx=pad_x, pady=(20, 0)
        )

        # Section source CLAUDE.md
        src_frame = tk.Frame(self, bg=C["bg"])
        src_frame.pack(fill="x", padx=pad_x, pady=(10, 0))

        self.dot_label = tk.Label(
            src_frame, text="●",
            bg=C["bg"], fg=C["text_dim"],
            font=("Segoe UI", 10),
        )
        self.dot_label.pack(side="left")

        self.src_label = tk.Label(
            src_frame, text="",
            bg=C["bg"], fg=C["text_dim"],
            font=("Segoe UI", 8), anchor="w",
        )
        # Le bouton est packe en premier (side="right") pour qu'il reserve son
        # espace avant que le label ne s'etende, evitant ainsi que le label
        # long ne le fasse disparaitre.
        mod_btn = tk.Button(
            src_frame, text="Modifier",
            bg=C["btn_mod"], fg=C["text"],
            activebackground=C["btn_mod_h"], activeforeground=C["text"],
            relief="flat", bd=0,
            font=("Segoe UI", 8),
            cursor="hand2",
            command=self._modify_source,
            padx=10, pady=4,
        )
        mod_btn.pack(side="right")

        self.src_label.pack(side="left", fill="x", expand=True, padx=(6, 0))
        _bind_hover(mod_btn, C["btn_mod"], C["btn_mod_h"])

    # ---------------------------------------------------------------------- #
    #  Logique metier                                                           #
    # ---------------------------------------------------------------------- #

    def _on_name_change(self, *_args) -> None:
        """Validation en temps reel du nom saisi."""
        name = self.name_var.get().strip()
        valid, msg = validate_project_name(name)
        self.err_var.set(msg if (name and not valid) else "")

    def _refresh_source_status(self) -> bool:
        """Met a jour le voyant de statut du fichier source."""
        source = self.cfg.get("claude_md_source", "")
        exists = bool(source) and os.path.isfile(source)

        if not source:
            self.dot_label.config(fg=C["warning"])
            self.src_label.config(text="Aucune source configuree", fg=C["warning"])
        elif exists:
            self.dot_label.config(fg=C["success"])
            self.src_label.config(text=_truncate(source), fg=C["text_dim"])
        else:
            self.dot_label.config(fg=C["error"])
            self.src_label.config(text=_truncate(source) + "  [INTROUVABLE]", fg=C["error"])

        return exists

    def _startup_check(self) -> None:
        """Alerte non bloquante si la source est manquante au demarrage."""
        source = self.cfg.get("claude_md_source", "")
        if source and not os.path.isfile(source):
            messagebox.showwarning(
                "Source introuvable",
                f"Le fichier source du hard link est introuvable :\n\n{source}\n\n"
                "Utilisez le bouton 'Modifier' pour corriger le chemin.",
            )
            logging.warning("Source introuvable au demarrage : %s", source)

    def _create_project(self) -> None:
        """Valide, cree le dossier, etablit le hard link et ouvre un terminal."""
        name = self.name_var.get().strip()

        # Validation du nom
        valid, msg = validate_project_name(name)
        if not valid:
            self.err_var.set(msg)
            self.name_entry.focus_set()
            return

        # Verification de la source avant toute action
        source = self.cfg.get("claude_md_source", "")
        if not os.path.isfile(source):
            messagebox.showerror(
                "Source introuvable",
                f"Le fichier CLAUDE.md source n'existe plus :\n\n{source}\n\n"
                "Corrigez le chemin via le bouton 'Modifier'.",
            )
            logging.error("Creation annulee, source introuvable : %s", source)
            self._refresh_source_status()
            return

        project_path = os.path.join(self.cfg["projects_dir"], name)

        # Verification de l'existence prealable du dossier
        if os.path.exists(project_path):
            messagebox.showwarning(
                "Dossier existant",
                f"Le dossier '{name}' existe deja dans :\n{self.cfg['projects_dir']}",
            )
            return

        # Creation du dossier
        try:
            os.makedirs(project_path)
            logging.info("Dossier cree : %s", project_path)
        except OSError as e:
            logging.error("Erreur creation dossier '%s' : %s", project_path, e)
            messagebox.showerror("Erreur", f"Impossible de creer le dossier :\n{e}")
            return

        # Creation du hard link CLAUDE.md
        dest   = os.path.join(project_path, "CLAUDE.md")
        result = subprocess.run(
            f'mklink /H "{dest}" "{source}"',
            shell=True,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Nettoyage : on supprime le dossier vide si le hard link a echoue
            try:
                os.rmdir(project_path)
            except OSError:
                pass
            err_msg = result.stderr.strip() or result.stdout.strip()
            logging.error("Echec mklink pour '%s' : %s", dest, err_msg)
            messagebox.showerror(
                "Erreur hard link",
                f"Le hard link CLAUDE.md n'a pas pu etre cree :\n\n{err_msg}",
            )
            return

        logging.info("Hard link cree : %s -> %s", dest, source)

        # Ouverture d'un terminal dans le nouveau dossier
        try:
            subprocess.Popen(
                "cmd",
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=project_path,
            )
            logging.info("Terminal ouvert dans : %s", project_path)
        except OSError as e:
            logging.error("Impossible d'ouvrir le terminal : %s", e)
            messagebox.showwarning(
                "Avertissement",
                f"Projet cree, mais impossible d'ouvrir le terminal :\n{e}",
            )

        # Reinitialisation du champ pour le prochain projet
        self.name_var.set("")
        self.err_var.set("")
        self.name_entry.focus_set()

    def _modify_source(self) -> None:
        """Ouvre un selecteur de fichier pour changer la source du hard link."""
        current    = self.cfg.get("claude_md_source", "")
        initial_dir = (
            os.path.dirname(current)
            if current and os.path.isdir(os.path.dirname(current))
            else SCRIPT_DIR
        )

        path = filedialog.askopenfilename(
            title="Selectionner le fichier source du hard link",
            filetypes=[("Markdown", "*.md"), ("Tous les fichiers", "*.*")],
            initialdir=initial_dir,
        )

        if not path:
            return  # Annule par l'utilisateur

        path = os.path.normpath(path)
        self.cfg["claude_md_source"] = path

        try:
            save_config(self.cfg)
        except IOError as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de sauvegarder la configuration :\n{e}",
            )
            return

        self._refresh_source_status()
        logging.info("Source modifiee : %s", path)


# --------------------------------------------------------------------------- #
#  Point d'entree                                                               #
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    app = ProjectLauncher()
    app.mainloop()
