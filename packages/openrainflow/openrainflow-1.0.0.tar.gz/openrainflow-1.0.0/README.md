# OpenRainflow

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Un package Python haute performance pour l'analyse de fatigue avec la méthode rainflow, les courbes d'endurance de l'Eurocode, et le calcul de dommage selon la règle de cumul linéaire de Miner.

## Caractéristiques

- ✨ **Implémentation optimisée** de l'algorithme rainflow avec Numba JIT compilation
- 🚀 **Haute performance** : traitement rapide avec gestion mémoire optimale
- 🔄 **Parallélisation** : support multi-threading pour grandes données
- 📊 **Courbes Eurocode** : implémentation complète des courbes d'endurance EN 1993-1-9
- 🔬 **Calcul de dommage** : règle de Miner pour évaluation de durée de vie
- 🧪 **Testé** : couverture complète avec tests unitaires

## Installation

```bash
pip install -e .
```

Pour le support de parallélisation :
```bash
pip install -e ".[parallel]"
```

Pour le développement :
```bash
pip install -e ".[dev]"
```

## Utilisation rapide

```python
import numpy as np
from openrainflow import rainflow_count, calculate_damage
from openrainflow.eurocode import EurocodeCategory

# Données de contrainte temporelle
stress_history = np.random.randn(10000) * 100 + 200

# Comptage rainflow
cycles = rainflow_count(stress_history)

# Définir la courbe d'endurance (catégorie 36 de l'Eurocode)
fatigue_curve = EurocodeCategory.get_curve('36')

# Calculer le dommage cumulé
damage = calculate_damage(cycles, fatigue_curve)

print(f"Dommage cumulé : {damage:.6f}")
print(f"Durée de vie estimée : {1/damage:.2f} répétitions" if damage > 0 else "Infini")
```

## Algorithme Rainflow

L'algorithme rainflow est une méthode de comptage de cycles utilisée pour analyser les historiques de contraintes variables. Cette implémentation utilise :

- **ASTM E1049-85** : Standard de comptage rainflow
- **Numba JIT** : compilation Just-In-Time pour performances optimales
- **NumPy** : opérations vectorisées sur tableaux

## Courbes d'endurance Eurocode

Implémentation des courbes S-N selon EN 1993-1-9 :

- Catégories : 160, 125, 112, 100, 90, 80, 71, 63, 56, 50, 45, 40, 36
- Support de la limite d'endurance
- Correction pour contrainte moyenne (option)

## Règle de Miner

Calcul du dommage cumulé selon :

\[D = \sum_{i=1}^{k} \frac{n_i}{N_i}\]

où :
- \(n_i\) : nombre de cycles à l'amplitude \(\Delta\sigma_i\)
- \(N_i\) : nombre de cycles à rupture pour \(\Delta\sigma_i\)

## Structure du package

```
openrainflow/
├── __init__.py           # API principale
├── rainflow.py           # Algorithme rainflow
├── eurocode.py           # Courbes d'endurance Eurocode
├── damage.py             # Calcul de dommage Miner
├── parallel.py           # Traitement parallèle
└── utils.py              # Utilitaires
```

## Performance

Benchmarks sur Intel Core i7 (8 threads) :

- **Rainflow counting** : ~1M points/seconde (mode JIT)
- **Damage calculation** : ~100k cycles/seconde
- **Memory usage** : optimisé pour grandes séries (>10M points)

## Contribution

Les contributions sont bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT License - voir [LICENSE](LICENSE) pour détails.

## Benchmarks

Des benchmarks comparatifs avec d'autres packages (`fatpack`, `rainflow`) sont disponibles dans le dossier `benchmarks/`.

```bash
# Installer les packages de comparaison
pip install fatpack rainflow matplotlib

# Exécuter tous les benchmarks
python benchmarks/run_all_benchmarks.py

# Ou individuellement
python benchmarks/benchmark_speed.py      # Vitesse
python benchmarks/benchmark_accuracy.py   # Précision
python benchmarks/benchmark_memory.py     # Mémoire
python benchmarks/benchmark_features.py   # Fonctionnalités
```

Résultats typiques : OpenRainflow est **3-4x plus rapide** après compilation JIT.

## Références

1. ASTM E1049-85, "Standard Practices for Cycle Counting in Fatigue Analysis"
2. EN 1993-1-9:2005, "Eurocode 3: Design of steel structures - Part 1-9: Fatigue"
3. Miner, M. A. (1945), "Cumulative damage in fatigue"

