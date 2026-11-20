import sys
from pathlib import Path

# permite "import simulador" ao rodar pytest a partir de qualquer pasta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
