# Règles d'utilisation des outils

## Principe fondamental : SÉQUENTIALITÉ STRICTE
- TOUJOURS exécuter UN SEUL outil à la fois
- ATTENDRE la réponse complète avant le prochain appel
- JAMAIS d'appels d'outils en parallèle

## Workflow obligatoire

### 1. PLAN (avant toute action)
- Lister les fichiers à manipuler
- Définir l'ordre des opérations
- Identifier les dépendances entre actions

### 2. ACT (exécution séquentielle)
- 1 fichier = 1 opération à la fois
- Lecture → Traitement → Écriture (jamais simultané)
- Valider chaque étape avant la suivante

## Règles par type d'opération

### Lecture de fichiers
- Lire les fichiers UN PAR UN
- Si plusieurs fichiers : les lister d'abord, puis lire séquentiellement
- Attendre le contenu complet avant toute analyse

### Modification de fichiers
- JAMAIS modifier plusieurs fichiers simultanément
- Ordre : view → str_replace OU create_file → validation
- Une seule modification par fichier à la fois

### Exécution de commandes
- Une commande bash à la fois
- Attendre le résultat avant la suivante
- Pas de commandes en background pendant d'autres opérations

### Recherche et navigation
- view (répertoire) → identifier les fichiers → view (fichiers individuels)
- Pas de view multiples simultanés

## Pattern interdit ❌
```
view file1.py
view file2.py  
str_replace file1.py
str_replace file2.py
```

## Pattern correct ✅
```
1. view file1.py
   [attendre résultat]
2. str_replace file1.py
   [attendre résultat]
3. view file2.py
   [attendre résultat]
4. str_replace file2.py
   [attendre résultat]
```

## Cas particuliers

### Projets avec multiples fichiers
- Créer une checklist des fichiers à traiter
- Traiter fichier par fichier dans l'ordre de la checklist
- Marquer chaque fichier comme "terminé" avant le suivant

### Debugging
- 1 hypothèse = 1 vérification = 1 outil
- view logs → analyser → bash (test) → view résultat

### Refactoring
- Identifier TOUS les fichiers impactés d'abord
- Les modifier UN PAR UN dans l'ordre des dépendances
- Tester après CHAQUE modification

## En cas d'erreur 400
- STOP immédiatement
- Exécuter /rewind
- Reprendre à la dernière action validée
- Décomposer encore plus finement

## Méthodologie imposée

Pour CHAQUE demande utilisateur :
1. **Analyser** : Quels fichiers ? Quelles opérations ?
2. **Planifier** : Dans quel ordre ? Combien d'étapes ?
3. **Annoncer** : "Je vais faire X étapes : 1)... 2)... 3)..."
4. **Exécuter** : Une étape à la fois, valider, passer à la suivante
5. **Confirmer** : Récapituler ce qui a été fait

## Limite de complexité
- Si la tâche nécessite > 10 appels d'outils séquentiels
- Proposer de la découper en sous-tâches
- Demander validation utilisateur entre chaque sous-tâche