"""
Configurazione pytest per TitoliEngine.

Imposta la precisione Decimal globale e fixture comuni.
"""
import sys
from decimal import getcontext
from pathlib import Path

# Assicura che il backend sia nel path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Precisione globale per tutti i test
getcontext().prec = 28
