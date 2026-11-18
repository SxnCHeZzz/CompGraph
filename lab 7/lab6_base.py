"""Общий интерфейс, многогранники и преобразования из лабораторной №6."""

from pathlib import Path
import importlib.util
import sys


LAB6_DIR = Path(__file__).resolve().parent.parent / 'lab 6'
if not (LAB6_DIR / 'interface.py').is_file():
    raise RuntimeError('Рядом с папкой «lab 7» должна находиться папка «lab 6».')
if str(LAB6_DIR) not in sys.path:
    sys.path.append(str(LAB6_DIR))


from member1_models import Face, SOLIDS
from member2_transforms import Polyhedron, make_solid
import member2_transforms as matrices

spec = importlib.util.spec_from_file_location('lab6_interface', LAB6_DIR / 'interface.py')
base_interface = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_interface)
BaseApp = base_interface.App


def copy_mesh(mesh):
    return Polyhedron(mesh.coordinates().copy(), mesh.faces.copy(), mesh.name)
