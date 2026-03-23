# tool_newProject

Petit utilitaire Windows pour initialiser un nouveau projet en une action :
creation du dossier, hard link automatique vers `CLAUDE.md`, et ouverture d'un terminal dans le dossier cree.

---

## Fonctionnalites

- Cree un dossier projet au meme endroit que l'executable
- Etablit un hard link `CLAUDE.md` vers un fichier source configurable
- Ouvre automatiquement un terminal (`cmd`) dans le nouveau dossier
- Validation du nom de dossier en temps reel (caracteres interdits, noms reserves Windows)
- Configuration persistante du fichier source via interface graphique

---

## Utilisation

### Depuis l'executable

Telecharger `new_project.exe` dans les [Releases](https://github.com/e-lab-aure/tool_newProject/releases), le placer ou vous souhaitez creer vos projets, puis le lancer.

### Depuis les sources

```bash
python new_project.py
```

Ou via le batch fourni :

```bash
new_project.bat
```

---

## Configuration

Au premier lancement, l'application utilise un `CLAUDE.md` situe a cote de l'executable.
Le bouton **Modifier** permet de pointer vers n'importe quel autre fichier source.
La configuration est sauvegardee dans `launcher_config.json` a cote de l'exe.

---

## Compilation

```bash
pyinstaller new_project.spec
```

L'executable est genere dans `dist/new_project.exe`.

---

## Prerequis (sources)

- Python 3.10+
- Tkinter (inclus avec Python sur Windows)
- PyInstaller (pour la compilation uniquement)
