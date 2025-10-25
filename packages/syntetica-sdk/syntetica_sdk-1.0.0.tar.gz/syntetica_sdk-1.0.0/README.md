# Syntetica Python SDK

SDK **Python** pour interagir avec l’API **Syntetica** et piloter vos générations de jeux de données synthétiques : **soumission**, **validation** de configuration et **suivi** d’avancement.

> Basé sur `syntetica_sdk/dataset_config.py`.  
> Version Python recommandée : **3.9+**.

---

## ✨ Fonctionnalités

- Générer un dataset depuis un **fichier YAML** *ou* un **`dict` Python**
- **Valider** une configuration sans lancer de génération
- **Suivre** l’état d’un job (waiting / generating / success / error + pourcentage & lignes)
- Gestion dédiée des erreurs de **conversion YAML → JSON** (`YamlToJsonError`)
- Paramétrage d’**environnement** via `base_url` (dev / prod)

---

## 📦 Installation

Depuis PyPI :

```bash
pip install syntetica-sdk