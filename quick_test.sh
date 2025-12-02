#!/bin/bash
# Script de test rapide pour Save Eat
# Teste tout et démarre le serveur

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        🧪 SAVE EAT - TEST RAPIDE ET DÉMARRAGE            ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}1. Test du système...${NC}"
python test_system.py

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Des problèmes ont été détectés${NC}"
    echo "Voulez-vous continuer quand même? (y/n)"
    read -r response
    if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
        echo "Arrêt."
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}2. Diagnostic Render...${NC}"
python diagnose_render.py

echo ""
echo -e "${GREEN}✅ Tous les tests passent!${NC}"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   🚀 DÉMARRAGE DU SERVEUR                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Le serveur va démarrer sur: http://localhost:8000"
echo "Appuyez sur Ctrl+C pour arrêter"
echo ""
sleep 2

# Démarrer le serveur
python main.py serve

