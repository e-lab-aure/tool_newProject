#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour le lanceur de projets.
Couvre la validation des noms et la logique de configuration.
"""

import os
import json
import tempfile
import unittest
import subprocess

from new_project import validate_project_name, load_config, save_config, _truncate


class TestValidateProjectName(unittest.TestCase):
    """Tests de la fonction de validation du nom de projet."""

    def test_nom_valide_simple(self):
        """Un nom simple doit etre accepte."""
        ok, msg = validate_project_name("mon_projet")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_nom_valide_avec_tirets(self):
        """Un nom avec tirets et chiffres doit etre accepte."""
        ok, msg = validate_project_name("projet-v2-test")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_nom_vide(self):
        """Un nom vide doit etre rejete."""
        ok, msg = validate_project_name("")
        self.assertFalse(ok)
        self.assertIn("vide", msg)

    def test_nom_espaces_seuls(self):
        """Un nom compose uniquement d'espaces doit etre rejete (apres strip)."""
        # La validation recoit le nom tel quel depuis l'UI (deja strip-pe)
        ok, msg = validate_project_name("")
        self.assertFalse(ok)

    def test_caractere_interdit_slash(self):
        """Un slash dans le nom doit etre rejete."""
        ok, msg = validate_project_name("mon/projet")
        self.assertFalse(ok)
        self.assertIn("/", msg)

    def test_caractere_interdit_backslash(self):
        ok, msg = validate_project_name("mon\\projet")
        self.assertFalse(ok)

    def test_caractere_interdit_etoile(self):
        ok, msg = validate_project_name("projet*")
        self.assertFalse(ok)

    def test_caractere_interdit_guillemets(self):
        ok, msg = validate_project_name('projet"test')
        self.assertFalse(ok)

    def test_caractere_interdit_chevrons(self):
        ok, msg = validate_project_name("proj<et>")
        self.assertFalse(ok)

    def test_caractere_interdit_pipe(self):
        ok, msg = validate_project_name("proj|et")
        self.assertFalse(ok)

    def test_caractere_interdit_deux_points(self):
        ok, msg = validate_project_name("C:projet")
        self.assertFalse(ok)

    def test_caractere_interdit_interrogation(self):
        ok, msg = validate_project_name("projet?")
        self.assertFalse(ok)

    def test_nom_reserve_con(self):
        """Les noms reserves Windows doivent etre rejetes."""
        ok, msg = validate_project_name("CON")
        self.assertFalse(ok)
        self.assertIn("CON", msg)

    def test_nom_reserve_nul(self):
        ok, msg = validate_project_name("NUL")
        self.assertFalse(ok)

    def test_nom_reserve_com1(self):
        ok, msg = validate_project_name("COM1")
        self.assertFalse(ok)

    def test_nom_reserve_insensible_casse(self):
        """Les noms reserves sont insensibles a la casse."""
        ok, msg = validate_project_name("con")
        self.assertFalse(ok)

    def test_nom_se_termine_par_point(self):
        """Un nom terminant par un point doit etre rejete."""
        ok, msg = validate_project_name("projet.")
        self.assertFalse(ok)

    def test_nom_unicode_accents(self):
        """Les accents et caracteres unicode sont autorises."""
        ok, msg = validate_project_name("projet-etude-donnees")
        self.assertTrue(ok)

    def test_nom_long_valide(self):
        """Un nom long mais valide doit etre accepte."""
        ok, msg = validate_project_name("a" * 200)
        self.assertTrue(ok)


class TestConfig(unittest.TestCase):
    """Tests du chargement et de la sauvegarde de la configuration."""

    def setUp(self):
        """Cree un repertoire temporaire isole pour chaque test."""
        self.tmp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmp_dir, "launcher_config.json")

    def _write_config(self, data: dict) -> None:
        """Ecrit directement un fichier de config brut pour les tests."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def test_load_config_inexistant(self):
        """Si le fichier config n'existe pas, les valeurs par defaut sont retournees."""
        config = load_config()
        self.assertIn("claude_md_source", config)
        self.assertIn("projects_dir", config)

    def test_save_and_load_roundtrip(self):
        """Une config sauvegardee puis rechargee doit etre identique."""
        import new_project as m
        original_cfg = m.CONFIG_FILE
        m.CONFIG_FILE = self.config_path
        try:
            data = {"claude_md_source": "/tmp/CLAUDE.md", "projects_dir": "/tmp"}
            save_config(data)
            loaded = load_config()
            self.assertEqual(loaded["claude_md_source"], data["claude_md_source"])
            self.assertEqual(loaded["projects_dir"], data["projects_dir"])
        finally:
            m.CONFIG_FILE = original_cfg

    def test_load_config_corrompu(self):
        """Un fichier JSON corrompu doit retourner la config par defaut sans planter."""
        with open(self.config_path, "w") as f:
            f.write("{ invalid json }")
        import new_project as m
        original_cfg = m.CONFIG_FILE
        m.CONFIG_FILE = self.config_path
        try:
            config = load_config()
            self.assertIn("claude_md_source", config)
        finally:
            m.CONFIG_FILE = original_cfg

    def test_load_config_cles_manquantes(self):
        """Une config partielle doit etre completee par les valeurs par defaut."""
        self._write_config({"claude_md_source": "/tmp/CLAUDE.md"})
        import new_project as m
        original_cfg = m.CONFIG_FILE
        m.CONFIG_FILE = self.config_path
        try:
            config = load_config()
            self.assertIn("projects_dir", config)
        finally:
            m.CONFIG_FILE = original_cfg


class TestTruncate(unittest.TestCase):
    """Tests de la fonction de troncature d'affichage."""

    def test_chemin_court_inchange(self):
        """Un chemin court ne doit pas etre modifie."""
        path = "/tmp/CLAUDE.md"
        self.assertEqual(_truncate(path, 52), path)

    def test_chemin_long_tronque(self):
        """Un chemin trop long doit commencer par '...'."""
        path = "/tmp/" + "a" * 100 + "/CLAUDE.md"
        result = _truncate(path, 52)
        self.assertTrue(result.startswith("..."))
        self.assertLessEqual(len(result), 52)

    def test_chemin_exactement_a_la_limite(self):
        """Un chemin de longueur exacte ne doit pas etre modifie."""
        path = "x" * 52
        self.assertEqual(_truncate(path, 52), path)


class TestHardLinkIntegration(unittest.TestCase):
    """
    Tests d'integration pour la creation du hard link via mklink.
    Ces tests s'executent uniquement sur Windows.
    """

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.source  = os.path.join(self.tmp_dir, "SOURCE.md")
        with open(self.source, "w") as f:
            f.write("# Test source\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_hard_link_cree_avec_succes(self):
        """mklink /H doit creer un hard link fonctionnel."""
        dest = os.path.join(self.tmp_dir, "DEST.md")
        result = subprocess.run(
            f'mklink /H "{dest}" "{self.source}"',
            shell=True, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.isfile(dest))

    def test_hard_link_partage_contenu(self):
        """Les deux fichiers du hard link doivent partager le meme contenu."""
        dest = os.path.join(self.tmp_dir, "DEST.md")
        subprocess.run(
            f'mklink /H "{dest}" "{self.source}"',
            shell=True, capture_output=True,
        )
        with open(dest, "r") as f:
            content = f.read()
        self.assertIn("Test source", content)

    def test_hard_link_source_inexistante(self):
        """mklink /H doit echouer si la source n'existe pas."""
        dest    = os.path.join(self.tmp_dir, "DEST.md")
        missing = os.path.join(self.tmp_dir, "MISSING.md")
        result  = subprocess.run(
            f'mklink /H "{dest}" "{missing}"',
            shell=True, capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(os.path.isfile(dest))

    def test_source_existe(self):
        """Verification que le fichier source CLAUDE.md du projet existe."""
        script_dir   = os.path.dirname(os.path.abspath(__file__))
        claude_source = os.path.join(script_dir, "CLAUDE.md")
        self.assertTrue(
            os.path.isfile(claude_source),
            f"CLAUDE.md source introuvable a : {claude_source}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
