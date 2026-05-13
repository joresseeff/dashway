"""
paths.py
--------
Résolution des chemins compatible développement et PyInstaller.
"""

import sys
import os


def resource(relative_path: str) -> str:
    """Retourne le chemin absolu vers une ressource.

    En mode PyInstaller (exe), les fichiers sont extraits dans un
    dossier temporaire accessible via sys._MEIPASS.
    En mode développement, on remonte d'un niveau depuis scr/.

    Args:
        relative_path: Chemin relatif depuis la racine du projet
                       (ex: 'assets/lambo.png', 'sounds/mainMusic.mp3').

    Returns:
        Chemin absolu utilisable par pygame et open().
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)
