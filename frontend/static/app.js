// Save Eat - Modern Frontend JavaScript
// Handles all user interactions and API calls

// ============================================================================
// USER MANAGER - Gestion de l'authentification simple
// ============================================================================

class UserManager {
    constructor() {
        this.currentUserId = null;
        this.currentUsername = null;
        this.init();
    }

    init() {
        // Charger l'utilisateur depuis localStorage
        const savedUserId = localStorage.getItem('saveeat_user_id');
        const savedUsername = localStorage.getItem('saveeat_username');

        if (savedUserId && savedUsername) {
            this.currentUserId = parseInt(savedUserId);
            this.currentUsername = savedUsername;
            console.log(`✅ User logged in: ${this.currentUsername} (ID: ${this.currentUserId})`);
        } else {
            // Nouveau utilisateur - demander un pseudo
            this.promptForUsername();
        }
    }

    promptForUsername() {
        const username = prompt("👋 Bienvenue sur Save Eat!\n\nEntrez votre pseudo pour commencer:");

        if (username && username.trim()) {
            // Générer un ID utilisateur aléatoire
            this.currentUserId = Math.floor(Math.random() * 900000) + 100000; // ID entre 100000 et 999999
            this.currentUsername = username.trim();

            // Sauvegarder dans localStorage
            localStorage.setItem('saveeat_user_id', this.currentUserId);
            localStorage.setItem('saveeat_username', this.currentUsername);

            console.log(`✅ New user created: ${this.currentUsername} (ID: ${this.currentUserId})`);

            // Afficher un message de bienvenue
            this.showWelcomeMessage();
        } else {
            // L'utilisateur a annulé ou entré un pseudo vide, réessayer
            alert("⚠️ Vous devez entrer un pseudo pour utiliser Save Eat");
            this.promptForUsername();
        }
    }

    showWelcomeMessage() {
        // Message de bienvenue simple
        console.log(`🎉 Bienvenue ${this.currentUsername}! Vous pouvez maintenant configurer votre profil.`);
    }

    getUserId() {
        return this.currentUserId;
    }

    getUsername() {
        return this.currentUsername;
    }

    logout() {
        if (confirm(`Êtes-vous sûr de vouloir vous déconnecter (${this.currentUsername}) ?`)) {
            localStorage.removeItem('saveeat_user_id');
            localStorage.removeItem('saveeat_username');
            this.currentUserId = null;
            this.currentUsername = null;
            console.log('👋 User logged out');

            // Recharger la page pour réinitialiser
            window.location.reload();
        }
    }

    isLoggedIn() {
        return this.currentUserId !== null && this.currentUsername !== null;
    }
}

// ============================================================================
// USER PROFILE MANAGER - Gestion des profils utilisateurs via API
// ============================================================================

class UserProfileManager {
    constructor() {
        this.currentProfile = null;
        this.apiBaseUrl = '/api/v1';
    }

    /**
     * Charge le profil utilisateur depuis l'API
     * @param {number} userId - ID de l'utilisateur
     * @returns {Promise<Object|null>} Le profil ou null si non trouvé
     */
    async loadProfile(userId) {
        try {
            console.log(`📥 Loading profile for user ${userId}...`);
            const response = await fetch(`${this.apiBaseUrl}/user/${userId}/profile`);

            if (response.ok) {
                this.currentProfile = await response.json();
                console.log('✅ Profile loaded successfully:', this.currentProfile);
                return this.currentProfile;
            } else if (response.status === 404) {
                console.log('ℹ️ No profile found for this user');
                this.currentProfile = null;
                return null;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('❌ Error loading profile:', error);
            return null;
        }
    }

    /**
     * Sauvegarde un nouveau profil utilisateur
     * @param {number} userId - ID de l'utilisateur
     * @param {Object} profileData - Données du profil
     * @returns {Promise<boolean>} true si succès
     */
    async saveProfile(userId, profileData) {
        try {
            console.log(`💾 Saving profile for user ${userId}...`, profileData);

            const response = await fetch(`${this.apiBaseUrl}/user/${userId}/profile`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(profileData)
            });

            if (response.ok) {
                this.currentProfile = await response.json();
                console.log('✅ Profile saved successfully');
                return true;
            } else {
                const errorData = await response.json();
                console.error('❌ Error saving profile:', errorData);
                return false;
            }
        } catch (error) {
            console.error('❌ Network error saving profile:', error);
            return false;
        }
    }

    /**
     * Met à jour partiellement le profil existant
     * @param {number} userId - ID de l'utilisateur
     * @param {Object} changes - Champs à mettre à jour
     * @returns {Promise<boolean>} true si succès
     */
    async updateProfile(userId, changes) {
        try {
            console.log(`🔄 Updating profile for user ${userId}...`, changes);

            const response = await fetch(`${this.apiBaseUrl}/user/${userId}/profile`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(changes)
            });

            if (response.ok) {
                this.currentProfile = await response.json();
                console.log('✅ Profile updated successfully');
                return true;
            } else {
                const errorData = await response.json();
                console.error('❌ Error updating profile:', errorData);
                return false;
            }
        } catch (error) {
            console.error('❌ Network error updating profile:', error);
            return false;
        }
    }

    /**
     * Supprime le profil utilisateur
     * @param {number} userId - ID de l'utilisateur
     * @returns {Promise<boolean>} true si succès
     */
    async deleteProfile(userId) {
        try {
            console.log(`🗑️ Deleting profile for user ${userId}...`);

            const response = await fetch(`${this.apiBaseUrl}/user/${userId}/profile`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.currentProfile = null;
                console.log('✅ Profile deleted successfully');
                return true;
            } else {
                console.error('❌ Error deleting profile');
                return false;
            }
        } catch (error) {
            console.error('❌ Network error deleting profile:', error);
            return false;
        }
    }

    /**
     * Retourne le profil en cache
     * @returns {Object|null} Le profil actuel ou null
     */
    getProfile() {
        return this.currentProfile;
    }

    /**
     * Vérifie si un profil est chargé
     * @returns {boolean} true si un profil existe
     */
    hasProfile() {
        return this.currentProfile !== null;
    }

    /**
     * Réinitialise le cache du profil
     */
    clearCache() {
        this.currentProfile = null;
        console.log('🧹 Profile cache cleared');
    }
}

// ============================================================================
// SAVE EAT APP - Application principale
// ============================================================================

class SaveEatApp {
    constructor() {
        this.selectedIngredients = new Set();
        this.selectedDietaryPrefs = new Set();
        this.ingredients = [];
        this.filteredIngredients = [];
        // Stockage des positions fixes de chaque ingrédient
        this.ingredientPositions = new Map(); // Map<ingredient, {x, y, shelf}>
        // Configuration des zones d'étagères (en % du haut du conteneur)
        // Calculées automatiquement pour 6 étagères équidistantes
        this.numShelves = 6;
        this.shelfMarginLeft = 3; // Marge gauche en %
        this.shelfMarginRight = 3; // Marge droite en %
        
        // Zones calibrées sauvegardées
        this.calibratedZones = null; // Zones calibrées sauvegardées

        // Initialize user management
        this.userManager = new UserManager();
        this.profileManager = new UserProfileManager();

        this.init();
    }

    async init() {
        console.log('🚀 Initializing Save Eat App...');

        // Display user info in UI
        this.updateUserDisplay();

        // Load user profile if logged in
        if (this.userManager.isLoggedIn()) {
            await this.loadUserProfile();
        }

        await this.loadIngredients();
        this.setupEventListeners();
        
        // Charger les zones calibrées si elles existent
        this.loadCalibratedZones();
    }
    
    populateAutocompleteLists() {
        // Populate allergies and disliked ingredients datalists
        const allergiesList = document.getElementById('allergiesList');
        const dislikedList = document.getElementById('dislikedList');
        
        if (allergiesList && dislikedList && this.ingredients && this.ingredients.length > 0) {
            // Clear existing options
            allergiesList.innerHTML = '';
            dislikedList.innerHTML = '';
            
            // Add all ingredients as options
            this.ingredients.forEach(ingredient => {
                const option1 = document.createElement('option');
                option1.value = ingredient;
                allergiesList.appendChild(option1);
                
                const option2 = document.createElement('option');
                option2.value = ingredient;
                dislikedList.appendChild(option2);
            });
            
            console.log(`✅ Populated autocomplete lists with ${this.ingredients.length} ingredients`);
        }
    }
    
    loadCalibratedZones() {
        const saved = localStorage.getItem('shelfZones');
        if (saved) {
            try {
                const zones = JSON.parse(saved);
                if (zones && zones.length === this.numShelves) {
                    // Utiliser les zones calibrées avec les marges ajustées (3% à gauche et droite)
                    this.calibratedZones = zones.map(zone => ({
                        top: zone.top,
                        bottom: zone.bottom,
                        left: 3, // Marge gauche fixe à 3%
                        right: 3  // Marge droite fixe à 3%
                    }));
                    console.log('✅ Zones calibrées chargées depuis localStorage (marges: 3% gauche/droite)');
                }
            } catch (e) {
                console.warn('Erreur lors du chargement de la calibration:', e);
            }
        }
    }

    updateUserDisplay() {
        // Update profile modal with user info
        const username = this.userManager.getUsername();
        const userId = this.userManager.getUserId();

        if (username && userId) {
            document.getElementById('profileUsername').textContent = username;
            document.getElementById('profileUserId').textContent = `ID: ${userId}`;
        }
    }

    async loadUserProfile() {
        try {
            const userId = this.userManager.getUserId();
            const profile = await this.profileManager.loadProfile(userId);

            if (profile) {
                console.log('✅ User profile loaded');
                this.populateProfileForm(profile);
                this.updateProfileIndicator();
                // Pré-remplir les filtres de la page principale
                this.populateMainPageFilters(profile);
            } else {
                console.log('ℹ️ No profile found - user can create one');
                this.updateProfileIndicator(false);
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
            this.updateProfileIndicator(false);
        }
    }
    
    populateMainPageFilters(profile) {
        // Pré-remplir les filtres de la page principale avec le profil
        if (!profile) return;
        
        // Temps maximum
        if (profile.max_prep_time) {
            const maxTimeInput = document.getElementById('maxTime');
            if (maxTimeInput) {
                maxTimeInput.value = profile.max_prep_time;
            }
        }
        
        // Calories maximum
        if (profile.max_calories) {
            const maxCaloriesInput = document.getElementById('maxCalories');
            if (maxCaloriesInput) {
                maxCaloriesInput.value = profile.max_calories;
            }
        }
        
        // Préférences alimentaires (boutons de la page principale)
        if (profile.dietary_restrictions && profile.dietary_restrictions.length > 0) {
            // Si "none" est dans les restrictions, ne pas cocher les autres
            if (!profile.dietary_restrictions.includes('none')) {
                // Cocher les boutons correspondants
                profile.dietary_restrictions.forEach(restriction => {
                    const btn = document.querySelector(`[data-pref="${restriction}"]`);
                    if (btn) {
                        btn.classList.remove('border-slate-200', 'text-slate-800', 'border-gray-300', 'text-gray-700');
                        btn.classList.add('bg-green-500', 'text-white', 'border-green-500');
                        this.selectedDietaryPrefs.add(restriction);
                    }
                });
            }
        }
        
        console.log('✅ Main page filters populated from profile');
    }
    
    updateProfileIndicator(hasProfile = null) {
        // Update profile button to show if profile is active
        const profileButton = document.getElementById('profileButton');
        if (!profileButton) return;
        
        // If hasProfile is null, check if profile exists
        if (hasProfile === null) {
            hasProfile = this.profileManager.hasProfile();
        }
        
        if (hasProfile) {
            // Add visual indicator that profile is active
            profileButton.classList.add('relative');
            if (!profileButton.querySelector('.profile-indicator')) {
                const indicator = document.createElement('span');
                indicator.className = 'profile-indicator absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white';
                indicator.title = 'Profil actif';
                profileButton.appendChild(indicator);
            }
            profileButton.title = 'Mon Profil (actif)';
        } else {
            // Remove indicator
            const indicator = profileButton.querySelector('.profile-indicator');
            if (indicator) {
                indicator.remove();
            }
            profileButton.title = 'Mon Profil';
        }
    }

    populateProfileForm(profile) {
        // SECTION 1: SÉCURITÉ - Allergies
        if (profile.allergies) {
            document.getElementById('profileAllergies').value = profile.allergies.join(', ');
        }

        // SECTION 2: RÉGIME ALIMENTAIRE - Dietary restrictions
        if (profile.dietary_restrictions) {
            // Si "none" est dans les restrictions, cocher uniquement "Aucun"
            if (profile.dietary_restrictions.includes('none')) {
                const noneCheckbox = document.getElementById('dietary-none');
                if (noneCheckbox) {
                    noneCheckbox.checked = true;
                }
                // Décocher tous les autres
                document.querySelectorAll('.dietary-checkbox:not(#dietary-none)').forEach(checkbox => {
                    checkbox.checked = false;
                });
            } else {
                // Cocher les restrictions spécifiées
                document.querySelectorAll('.dietary-checkbox').forEach(checkbox => {
                    checkbox.checked = profile.dietary_restrictions.includes(checkbox.value);
                });
                // S'assurer que "Aucun" n'est pas coché
                const noneCheckbox = document.getElementById('dietary-none');
                if (noneCheckbox) {
                    noneCheckbox.checked = false;
                }
            }
        }

        // SECTION 3: NUTRITION - Nutritional values
        if (profile.max_calories) {
            document.getElementById('profileMaxCalories').value = profile.max_calories;
        }
        if (profile.min_protein) {
            document.getElementById('profileMinProtein').value = profile.min_protein;
        }
        if (profile.max_carbs) {
            document.getElementById('profileMaxCarbs').value = profile.max_carbs;
        }
        if (profile.max_fat) {
            document.getElementById('profileMaxFat').value = profile.max_fat;
        }

        // SECTION 4: PRÉFÉRENCES - Disliked ingredients
        if (profile.disliked_ingredients) {
            document.getElementById('profileDisliked').value = profile.disliked_ingredients.join(', ');
        }

        // SECTION 4: PRÉFÉRENCES - Max prep time
        if (profile.max_prep_time) {
            document.getElementById('profileMaxPrepTime').value = profile.max_prep_time;
        }

        // Update profile summary
        this.updateProfileSummary(profile);

        console.log('✅ Profile form populated');
    }
    
    updateProfileSummary(profile) {
        const summaryDiv = document.getElementById('profileSummary');
        const summaryContent = document.getElementById('profileSummaryContent');
        
        if (!summaryDiv || !summaryContent) return;
        
        if (!profile) {
            summaryDiv.classList.add('hidden');
            return;
        }
        
        const summaryItems = [];
        
        // SECTION 1: SÉCURITÉ
        if (profile.allergies && profile.allergies.length > 0) {
            summaryItems.push(`🚨 Allergies: ${profile.allergies.join(', ')}`);
        }
        
        // SECTION 2: RÉGIME ALIMENTAIRE
        if (profile.dietary_restrictions && profile.dietary_restrictions.length > 0) {
            const restrictionLabels = {
                'vegetarian': 'Végétarien',
                'vegan': 'Végan',
                'gluten-free': 'Sans gluten',
                'dairy-free': 'Sans lactose'
            };
            const labels = profile.dietary_restrictions.map(r => restrictionLabels[r] || r);
            summaryItems.push(`🥗 Régime: ${labels.join(', ')}`);
        }
        
        // SECTION 3: NUTRITION
        const nutritionItems = [];
        if (profile.max_calories) nutritionItems.push(`Calories ≤ ${profile.max_calories}`);
        if (profile.min_protein) nutritionItems.push(`Protéines ≥ ${profile.min_protein}g`);
        if (profile.max_carbs) nutritionItems.push(`Glucides ≤ ${profile.max_carbs}g`);
        if (profile.max_fat) nutritionItems.push(`Lipides ≤ ${profile.max_fat}g`);
        if (nutritionItems.length > 0) {
            summaryItems.push(`🔥 Nutrition: ${nutritionItems.join(', ')}`);
        }
        
        // SECTION 4: PRÉFÉRENCES
        if (profile.disliked_ingredients && profile.disliked_ingredients.length > 0) {
            summaryItems.push(`👎 Évite: ${profile.disliked_ingredients.slice(0, 3).join(', ')}${profile.disliked_ingredients.length > 3 ? '...' : ''}`);
        }
        
        if (profile.max_prep_time) {
            summaryItems.push(`⏱️ Temps max: ${profile.max_prep_time} min`);
        }
        
        if (summaryItems.length > 0) {
            summaryContent.innerHTML = summaryItems.map(item => `<p>${item}</p>`).join('');
            summaryDiv.classList.remove('hidden');
        } else {
            summaryDiv.classList.add('hidden');
        }
    }

    async loadIngredients(retryCount = 0) {
        try {
            const response = await fetch('/api/v1/ingredients?limit=500');
            
            // Check if response is OK
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.ingredients && data.ingredients.length > 0) {
                this.ingredients = data.ingredients;
                this.filteredIngredients = [...this.ingredients];
                this.renderIngredients();
                this.renderSelectedIngredients();
                // Populate autocomplete lists after ingredients are loaded
                this.populateAutocompleteLists();
                console.log(`✅ Loaded ${this.ingredients.length} ingredients`);
            } else if (data.status === 'loading' && retryCount < 10) {
                // Cache still loading - show message and retry
                console.log(`⏳ Ingredients loading... (retry ${retryCount + 1}/10)`);
                document.getElementById('ingredientsContainer').innerHTML = `
                    <div class="text-center w-full py-8">
                        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mb-4"></div>
                        <p class="font-medium text-gray-700">Chargement des ingrédients...</p>
                        <p class="text-sm text-gray-500 mt-2">${data.message || 'Première initialisation en cours'}</p>
                    </div>
                `;
                // Retry after 2 seconds
                setTimeout(() => this.loadIngredients(retryCount + 1), 2000);
            } else {
                console.warn('No ingredients found');
                document.getElementById('ingredientsContainer').innerHTML = `
                    <div class="text-center w-full py-4 text-gray-500">
                        <p class="font-medium">Aucun ingrédient disponible</p>
                        <p class="text-sm">Rechargez la page ou vérifiez la base de données</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading ingredients:', error);
            document.getElementById('ingredientsContainer').innerHTML = `
                <div class="text-center w-full py-4 text-red-500">
                    <p class="font-medium">Erreur de chargement</p>
                    <p class="text-sm">${error.message}</p>
                    <button onclick="location.reload()" class="mt-4 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600">
                        Recharger la page
                    </button>
                </div>
            `;
        }
    }

    renderIngredients() {
        const container = document.getElementById('ingredientsContainer');
        const list = this.filteredIngredients && this.filteredIngredients.length > 0
            ? this.filteredIngredients
            : this.ingredients;

        if (!list || list.length === 0) {
            container.innerHTML = `
                <div class="w-full text-center text-sm text-gray-500 py-2">
                    Aucun ingrédient ne correspond à votre recherche
                </div>
            `;
            return;
        }

        container.innerHTML = list.map(ing => {
            const isSelected = this.selectedIngredients.has(ing);
            const baseClasses = 'ingredient-chip px-4 py-2 rounded-full text-sm font-medium transition-all';
            const unselectedClasses = 'bg-white border-2 border-gray-300 text-gray-700 hover:border-green-500 hover:bg-green-50';
            const selectedClasses = 'bg-green-500 border-green-500 text-white hover:bg-green-600';
            const classes = `${baseClasses} ${isSelected ? selectedClasses : unselectedClasses}`;

            return `
                <button 
                    data-ingredient="${ing}"
                    class="${classes}">
                    ${this.capitalize(ing)}
                </button>
            `;
        }).join('');

        // Add click listeners
        container.querySelectorAll('.ingredient-chip').forEach(btn => {
            btn.addEventListener('click', (e) => this.toggleIngredient(e.target));
        });
    }

    toggleIngredient(btn) {
        const ingredient = btn.dataset.ingredient;
        
        if (this.selectedIngredients.has(ingredient)) {
            this.selectedIngredients.delete(ingredient);
            btn.classList.remove('bg-green-500', 'text-white', 'border-green-500');
            btn.classList.add('bg-white', 'text-gray-700', 'border-gray-300');
        } else {
            this.selectedIngredients.add(ingredient);
            btn.classList.remove('bg-white', 'text-gray-700', 'border-gray-300');
            btn.classList.add('bg-green-500', 'text-white', 'border-green-500');
        }

        console.log(`Selected ingredients: ${Array.from(this.selectedIngredients).join(', ')}`);
        this.renderSelectedIngredients();
    }

    renderSelectedIngredients() {
        const overlay = document.getElementById('ingredientsOverlay');
        if (!overlay) {
            console.error('❌ ingredientsOverlay not found');
            return;
        }

        const selected = Array.from(this.selectedIngredients);
        console.log(`📦 Rendering ${selected.length} selected ingredients`);

        if (selected.length === 0) {
            overlay.innerHTML = '';
            this.ingredientPositions.clear();
            return;
        }

        // Attendre que le conteneur soit rendu pour avoir ses dimensions
        setTimeout(() => {
            const container = document.getElementById('selectedIngredientsContainer');
            if (!container) {
                console.error('❌ selectedIngredientsContainer not found');
                return;
            }
            
            const containerWidth = container.offsetWidth;
            const containerHeight = container.offsetHeight;
            
            if (containerWidth === 0 || containerHeight === 0) {
                console.warn('⚠️ Container has zero dimensions, retrying...');
                setTimeout(() => this.renderSelectedIngredients(), 100);
                return;
            }
            
            console.log(`📐 Container dimensions: ${containerWidth}x${containerHeight}`);
            
            // Configuration des chips
            const chipWidth = 65; // Largeur réduite en px
            const chipHeight = 20; // Hauteur réduite en px
            const chipSpacing = 2; // Espacement vertical entre les chips empilés
            
            // Utiliser les zones calibrées si disponibles, sinon calculer automatiquement
            let shelfZones;
            if (this.calibratedZones && this.calibratedZones.length === this.numShelves) {
                console.log('✅ Using calibrated zones:', this.calibratedZones);
                shelfZones = this.calibratedZones.map(zone => ({
                    top: zone.top,
                    bottom: zone.bottom,
                    height: zone.bottom - zone.top,
                    left: zone.left || this.shelfMarginLeft,
                    right: zone.right || this.shelfMarginRight
                }));
            } else {
                console.log('📊 Using auto-calculated zones');
                // Calculer automatiquement les zones d'étagères (6 étagères équidistantes)
                const shelfHeightPercent = 100 / this.numShelves; // Hauteur de chaque étagère en %
                shelfZones = [];
                for (let i = 0; i < this.numShelves; i++) {
                    const top = (i * shelfHeightPercent) + 2; // +2% pour éviter le bord supérieur
                    const bottom = ((i + 1) * shelfHeightPercent) - 2; // -2% pour éviter le bord inférieur
                    shelfZones.push({
                        top: top,
                        bottom: bottom,
                        height: bottom - top,
                        left: this.shelfMarginLeft,
                        right: this.shelfMarginRight
                    });
                }
            }
            
            // Pour chaque ingrédient, utiliser sa position existante ou en créer une nouvelle
            const placedItems = [];
            // Structure pour suivre les positions occupées par étagère : {x, width, y, stackHeight}
            const shelfOccupancy = Array(shelfZones.length).fill(0).map(() => []);
            
            // D'abord, reconstruire les positions existantes dans shelfOccupancy
            const chipHeightPercent = (chipHeight / containerHeight) * 100;
            selected.forEach((ing) => {
                if (this.ingredientPositions.has(ing)) {
                    const pos = this.ingredientPositions.get(ing);
                    shelfOccupancy[pos.shelf].push({
                        x: pos.x,
                        width: chipWidth,
                        y: pos.y,
                        height: chipHeightPercent
                    });
                }
            });
            
            // Ensuite, placer les ingrédients (existants ou nouveaux)
            selected.forEach((ing) => {
                let position;
                
                // Si l'ingrédient a déjà une position, la réutiliser
                if (this.ingredientPositions.has(ing)) {
                    position = this.ingredientPositions.get(ing);
                } else {
                    // Nouvel ingrédient : trouver une place en suivant la gravité
                    position = this.findPositionForNewIngredient(
                        ing, 
                        shelfZones, 
                        shelfOccupancy, 
                        containerWidth, 
                        containerHeight,
                        chipWidth,
                        chipHeight,
                        chipSpacing
                    );
                    // Sauvegarder la position
                    this.ingredientPositions.set(ing, position);
                }
                
                placedItems.push({
                    ingredient: ing,
                    x: position.x,
                    y: position.y,
                    shelf: position.shelf
                });
            });

            // Générer le HTML avec positions absolues
            console.log(`🎯 Placing ${placedItems.length} items on shelves`);
            overlay.innerHTML = placedItems.map(item => {
                const zone = shelfZones[item.shelf];
                // item.y est le TOP de l'ingrédient en % depuis le haut
                // Convertir en pixels pour le positionnement CSS
                const topPx = (item.y / 100) * containerHeight;
                
                console.log(`  - ${item.ingredient}: shelf ${item.shelf}, x=${item.x}px, y=${item.y}% (${topPx}px from top)`);
                
                return `
                <button 
                    data-ingredient="${item.ingredient}"
                    style="position: absolute; left: ${item.x}px; top: ${topPx}px; width: ${chipWidth}px; height: ${chipHeight}px;"
                    class="flex items-center justify-center gap-0.5 rounded-full bg-emerald-100 text-emerald-900 text-[9px] font-medium border border-emerald-300 hover:bg-emerald-200 transition-all shadow-sm z-10 pointer-events-auto">
                    <span class="truncate px-1 text-[9px]">${this.capitalize(item.ingredient)}</span>
                    <span class="text-emerald-700 text-[9px] font-bold flex-shrink-0">×</span>
                </button>
            `;
            }).join('');

            // Clicking on a selected chip removes it and updates both lists
            overlay.querySelectorAll('button[data-ingredient]').forEach(btn => {
                btn.addEventListener('click', () => {
                    const ing = btn.dataset.ingredient;
                    if (this.selectedIngredients.has(ing)) {
                        this.selectedIngredients.delete(ing);
                        this.ingredientPositions.delete(ing); // Supprimer la position aussi
                        this.renderIngredients();
                        this.renderSelectedIngredients();
                    }
                });
            });
        }, 10);
    }


    findPositionForNewIngredient(ingredient, shelfZones, shelfOccupancy, containerWidth, containerHeight, chipWidth, chipHeight, chipSpacing) {
        const numShelves = shelfZones.length;
        const chipHeightPercent = (chipHeight / containerHeight) * 100;
        const spacingPercent = (chipSpacing / containerHeight) * 100;
        
        // Créer une liste d'étagères dans un ordre aléatoire pour distribuer les ingrédients
        const shelfOrder = Array.from({length: numShelves}, (_, i) => i);
        // Mélanger l'ordre
        for (let i = shelfOrder.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shelfOrder[i], shelfOrder[j]] = [shelfOrder[j], shelfOrder[i]];
        }
        
        // Essayer chaque étagère dans l'ordre aléatoire
        for (const shelfIndex of shelfOrder) {
            const zone = shelfZones[shelfIndex];
            const leftMargin = containerWidth * (zone.left / 100);
            const rightMargin = containerWidth * (zone.right / 100);
            const minX = Math.max(0, leftMargin);
            const maxX = Math.min(containerWidth - chipWidth, containerWidth - rightMargin - chipWidth);
            const occupied = shelfOccupancy[shelfIndex];
            
            // Calculer la position Y au bas de l'étagère (en % depuis le haut)
            const bottomYPercent = zone.bottom - chipHeightPercent;
            
            // ÉTAPE 1 : Essayer de placer au bottom de l'étagère sans chevauchement
            for (let attempt = 0; attempt < 30; attempt++) {
                const testX = minX + Math.random() * Math.max(0, maxX - minX);
                const testXEnd = testX + chipWidth;
                
                // Vérifier qu'il n'y a pas de chevauchement
                let canPlace = true;
                for (const occ of occupied) {
                    const horizontalOverlap = !(testXEnd <= occ.x || testX >= occ.x + occ.width);
                    const verticalOverlap = !(bottomYPercent + chipHeightPercent <= occ.y || bottomYPercent >= occ.y + (occ.height || chipHeightPercent));
                    
                    if (horizontalOverlap && verticalOverlap) {
                        canPlace = false;
                        break;
                    }
                }
                
                if (canPlace && bottomYPercent >= zone.top) {
                    occupied.push({
                        x: testX,
                        width: chipWidth,
                        y: bottomYPercent,
                        height: chipHeightPercent
                    });
                    
                    return {
                        x: testX,
                        y: bottomYPercent,
                        shelf: shelfIndex
                    };
                }
            }
            
            // ÉTAPE 2 : Si pas de place au bottom, essayer d'empiler au-dessus des ingrédients existants
            for (let attempt = 0; attempt < 30; attempt++) {
                const testX = minX + Math.random() * Math.max(0, maxX - minX);
                const testXEnd = testX + chipWidth;
                
                // Trouver les ingrédients qui chevauchent horizontalement
                const overlappingItems = occupied.filter(occ => 
                    !(testXEnd <= occ.x || testX >= occ.x + occ.width)
                );
                
                if (overlappingItems.length > 0) {
                    // Trouver l'item le plus haut pour empiler au-dessus
                    const topmostItem = overlappingItems.reduce((min, item) => 
                        item.y < min.y ? item : min
                    );
                    
                    // Empiler au-dessus avec espacement
                    const y = topmostItem.y - chipHeightPercent - spacingPercent;
                    
                    // Vérifier qu'on reste dans la zone
                    if (y >= zone.top) {
                        // Vérifier qu'on ne chevauche pas d'autres items
                        let canStack = true;
                        for (const occ of occupied) {
                            if (occ === topmostItem) continue;
                            
                            const horizontalOverlap = !(testXEnd <= occ.x || testX >= occ.x + occ.width);
                            const verticalOverlap = !(y + chipHeightPercent <= occ.y || y >= occ.y + (occ.height || chipHeightPercent));
                            
                            if (horizontalOverlap && verticalOverlap) {
                                canStack = false;
                                break;
                            }
                        }
                        
                        if (canStack) {
                            occupied.push({
                                x: testX,
                                width: chipWidth,
                                y: y,
                                height: chipHeightPercent
                            });
                            
                            return {
                                x: testX,
                                y: y,
                                shelf: shelfIndex
                            };
                        }
                    }
                }
            }
        }
        
        // Si aucune place trouvée, placer dans la première étagère disponible (même avec chevauchement)
        const firstShelf = shelfOrder[0];
        const zone = shelfZones[firstShelf];
        const leftMargin = containerWidth * (zone.left / 100);
        const rightMargin = containerWidth * (zone.right / 100);
        const maxX = Math.min(containerWidth - chipWidth, containerWidth - rightMargin - chipWidth);
        const minX = Math.max(0, leftMargin);
        const randomX = minX + Math.random() * Math.max(0, maxX - minX);
        const y = zone.bottom - chipHeightPercent;
        
        const position = {
            x: Math.max(minX, Math.min(randomX, maxX)),
            y: Math.max(zone.top, y),
            shelf: firstShelf
        };
        
        shelfOccupancy[firstShelf].push({
            x: position.x,
            width: chipWidth,
            y: position.y,
            height: chipHeightPercent
        });
        
        return position;
    }

    setupEventListeners() {
        // Ingredient search
        const ingredientSearch = document.getElementById('ingredientSearch');
        if (ingredientSearch) {
            ingredientSearch.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase().trim();
                if (!query) {
                    this.filteredIngredients = [...this.ingredients];
                } else {
                    this.filteredIngredients = this.ingredients.filter(ing =>
                        ing.toLowerCase().includes(query)
                    );
                }
                this.renderIngredients();
            });
        }

        // Profile button - Open modal
        document.getElementById('profileButton').addEventListener('click', () => {
            this.openProfileModal();
        });

        // Close modal buttons
        document.getElementById('closeProfileModal').addEventListener('click', () => {
            this.closeProfileModal();
        });

        document.getElementById('cancelProfileButton').addEventListener('click', () => {
            this.closeProfileModal();
        });

        // Save profile button
        document.getElementById('saveProfileButton').addEventListener('click', () => {
            this.saveProfile();
        });

        // Delete profile button
        document.getElementById('deleteProfileButton').addEventListener('click', () => {
            this.deleteProfile();
        });

        // Close modal on backdrop click
        document.getElementById('profileModal').addEventListener('click', (e) => {
            if (e.target.id === 'profileModal') {
                this.closeProfileModal();
            }
        });
        
        // Gérer l'option "Aucun" pour le régime alimentaire
        const dietaryNoneCheckbox = document.getElementById('dietary-none');
        if (dietaryNoneCheckbox) {
            dietaryNoneCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    // Si "Aucun" est coché, décocher tous les autres
                    document.querySelectorAll('.dietary-checkbox:not(#dietary-none)').forEach(checkbox => {
                        checkbox.checked = false;
                    });
                }
            });
        }
        
        // Si une autre option est cochée, décocher "Aucun"
        document.querySelectorAll('.dietary-checkbox:not(#dietary-none)').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    const noneCheckbox = document.getElementById('dietary-none');
                    if (noneCheckbox) {
                        noneCheckbox.checked = false;
                    }
                }
            });
        });

        // Dietary preferences
        document.querySelectorAll('.dietary-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const pref = e.target.dataset.pref;
                if (this.selectedDietaryPrefs.has(pref)) {
                    this.selectedDietaryPrefs.delete(pref);
                    e.target.classList.remove('bg-green-500', 'text-white', 'border-green-500');
                    e.target.classList.add('border-gray-300', 'text-gray-700');
                } else {
                    this.selectedDietaryPrefs.add(pref);
                    e.target.classList.remove('border-gray-300', 'text-gray-700');
                    e.target.classList.add('bg-green-500', 'text-white', 'border-green-500');
                }
            });
        });

        // Search button
        document.getElementById('searchBtn').addEventListener('click', () => this.searchRecipes());
        
        // Shopping button - Load popular recipes
        document.getElementById('shoppingBtn').addEventListener('click', () => this.loadPopularRecipes());

        // Enter key on inputs
        ['maxTime', 'maxCalories', 'topK'].forEach(id => {
            document.getElementById(id).addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.searchRecipes();
            });
        });
    }

    // ========================================================================
    // PROFILE MODAL METHODS
    // ========================================================================

    openProfileModal() {
        document.getElementById('profileModal').classList.remove('hidden');
        console.log('📖 Profile modal opened');
    }

    closeProfileModal() {
        document.getElementById('profileModal').classList.add('hidden');
        console.log('📕 Profile modal closed');
    }

    async saveProfile() {
        try {
            const userId = this.userManager.getUserId();

            // Collect form data
            const profileData = this.collectProfileData();

            console.log('💾 Saving profile...', profileData);

            // Save or update profile
            const success = await this.profileManager.saveProfile(userId, profileData);

            if (success) {
                // Reload profile to get updated data
                await this.loadUserProfile();
                
                // Update UI to show profile is active
                this.updateProfileIndicator();
                
                alert('✅ Profil enregistré avec succès ! Vos préférences seront appliquées aux recommandations.');
                this.closeProfileModal();
            } else {
                alert('❌ Erreur lors de l\'enregistrement du profil');
            }
        } catch (error) {
            console.error('Error saving profile:', error);
            alert('❌ Erreur: ' + error.message);
        }
    }

    collectProfileData() {
        const data = {};

        // SECTION 1: SÉCURITÉ - Allergies
        const allergies = document.getElementById('profileAllergies').value.trim();
        if (allergies) {
            data.allergies = allergies.split(',').map(a => a.trim()).filter(a => a);
        }

        // SECTION 2: RÉGIME ALIMENTAIRE - Dietary restrictions (checkboxes)
        const restrictions = [];
        document.querySelectorAll('.dietary-checkbox:checked').forEach(checkbox => {
            const value = checkbox.value;
            // Si "none" est coché, ne pas inclure les autres
            if (value === 'none') {
                restrictions.length = 0; // Clear array
                restrictions.push('none');
            } else {
                // Ne pas ajouter si "none" est déjà dans la liste
                if (!restrictions.includes('none')) {
                    restrictions.push(value);
                }
            }
        });
        // Si aucune restriction n'est cochée, ajouter "none"
        if (restrictions.length === 0) {
            restrictions.push('none');
        }
        data.dietary_restrictions = restrictions;

        // SECTION 3: NUTRITION - Nutritional constraints
        const maxCalories = document.getElementById('profileMaxCalories').value;
        if (maxCalories) data.max_calories = parseFloat(maxCalories);

        const minProtein = document.getElementById('profileMinProtein').value;
        if (minProtein) data.min_protein = parseFloat(minProtein);

        const maxCarbs = document.getElementById('profileMaxCarbs').value;
        if (maxCarbs) data.max_carbs = parseFloat(maxCarbs);

        const maxFat = document.getElementById('profileMaxFat').value;
        if (maxFat) data.max_fat = parseFloat(maxFat);

        // SECTION 4: PRÉFÉRENCES - Disliked ingredients
        const disliked = document.getElementById('profileDisliked').value.trim();
        if (disliked) {
            data.disliked_ingredients = disliked.split(',').map(d => d.trim()).filter(d => d);
        }

        // SECTION 4: PRÉFÉRENCES - Max prep time
        const maxPrepTime = document.getElementById('profileMaxPrepTime').value;
        if (maxPrepTime) data.max_prep_time = parseFloat(maxPrepTime);

        return data;
    }

    async deleteProfile() {
        if (!confirm('⚠️ Êtes-vous sûr de vouloir supprimer votre profil alimentaire ?')) {
            return;
        }

        try {
            const userId = this.userManager.getUserId();
            const success = await this.profileManager.deleteProfile(userId);

            if (success) {
                // Update UI to show profile is no longer active
                this.updateProfileIndicator(false);
                this.updateProfileSummary(null);
                
                alert('✅ Profil supprimé avec succès');
                this.clearProfileForm();
                this.closeProfileModal();
            } else {
                alert('❌ Erreur lors de la suppression');
            }
        } catch (error) {
            console.error('Error deleting profile:', error);
            alert('❌ Erreur: ' + error.message);
        }
    }

    clearProfileForm() {
        // SECTION 1: SÉCURITÉ
        document.getElementById('profileAllergies').value = '';
        
        // SECTION 2: RÉGIME ALIMENTAIRE
        document.querySelectorAll('.dietary-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        // Cocher "Aucun" par défaut
        const noneCheckbox = document.getElementById('dietary-none');
        if (noneCheckbox) {
            noneCheckbox.checked = true;
        }
        
        // SECTION 3: NUTRITION
        document.getElementById('profileMaxCalories').value = '';
        document.getElementById('profileMinProtein').value = '';
        document.getElementById('profileMaxCarbs').value = '';
        document.getElementById('profileMaxFat').value = '';
        
        // SECTION 4: PRÉFÉRENCES
        document.getElementById('profileDisliked').value = '';
        document.getElementById('profileMaxPrepTime').value = '';

        console.log('🧹 Profile form cleared');
    }

    async loadPopularRecipes() {
        // Show loading
        document.getElementById('resultsSection').classList.add('hidden');
        document.getElementById('emptyState').classList.add('hidden');
        document.getElementById('loadingState').classList.remove('hidden');
        
        // Scroll to results
        document.getElementById('loadingState').scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        try {
            console.log('🛒 Loading popular recipes...');
            
            const response = await fetch('/api/v1/popular-recipes?limit=50');
            const data = await response.json();
            
            console.log('✅ Received popular recipes:', data);
            
            // Debug: log first recipe's reviews
            if (data.recipes && data.recipes.length > 0) {
                const firstRecipe = data.recipes[0];
                console.log(`📊 First recipe (ID: ${firstRecipe.recipe_id}):`, {
                    name: firstRecipe.name,
                    avg_rating: firstRecipe.avg_rating,
                    review_count: firstRecipe.review_count,
                    reviews: firstRecipe.reviews,
                    reviews_count: firstRecipe.reviews ? firstRecipe.reviews.length : 0
                });
                if (firstRecipe.reviews && firstRecipe.reviews.length > 0) {
                    console.log('📝 First review sample:', firstRecipe.reviews[0]);
                }
            }
            
            // Hide loading
            document.getElementById('loadingState').classList.add('hidden');
            
            if (data.recipes && data.recipes.length > 0) {
                // Display recipes with reviews
                await this.displayPopularRecipes(data.recipes);
            } else {
                document.getElementById('emptyState').classList.remove('hidden');
            }
            
        } catch (error) {
            console.error('Error loading popular recipes:', error);
            document.getElementById('loadingState').classList.add('hidden');
            alert(`❌ Erreur: ${error.message}`);
        }
    }
    
    async displayPopularRecipes(recipes) {
        // Update count
        document.getElementById('resultsCount').textContent = recipes.length;
        
        // Render recipes with reviews
        const grid = document.getElementById('recipesGrid');
        grid.innerHTML = recipes.map(recipe => this.createRecipeCardWithReviews(recipe)).join('');
        
        // Show results
        document.getElementById('resultsSection').classList.remove('hidden');
        document.getElementById('resultsSection').classList.add('fade-in');
        
        // Smooth scroll
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    createRecipeCardWithReviews(recipe) {
        const {
            recipe_id,
            name,
            description,
            image_url,
            minutes,
            calories,
            protein,
            carbohydrates,
            total_fat,
            ingredients_list,
            n_ingredients,
            avg_rating,
            review_count,
            reviews
        } = recipe;
        
        // Nutrition info
        const nutritionHTML = this.createNutritionBars(calories, protein, carbohydrates, total_fat);
        
        // Rating display
        const ratingHTML = avg_rating ? `
            <div class="flex items-center space-x-2 mb-2">
                <div class="flex items-center">
                    ${this.renderStars(avg_rating)}
                </div>
                <span class="text-sm font-semibold text-gray-700">${avg_rating.toFixed(1)}</span>
                <span class="text-xs text-gray-500">(${review_count} avis)</span>
            </div>
        ` : '';
        
        // Reviews display (3-4 reviews)
        // Filter out reviews with no rating
        const validReviews = reviews ? reviews.filter(r => r.rating !== null && r.rating !== undefined) : [];
        const reviewsHTML = validReviews && validReviews.length > 0 ? `
            <div class="mt-3 border-t pt-3">
                <h4 class="text-sm font-semibold text-gray-700 mb-2">💬 Avis récents</h4>
                <div class="space-y-2 max-h-48 overflow-y-auto">
                    ${validReviews.slice(0, 4).map(review => {
                        const rating = review.rating !== null && review.rating !== undefined ? review.rating : 0;
                        const reviewText = review.review ? review.review.trim() : '';
                        return `
                        <div class="bg-gray-50 rounded-lg p-2">
                            <div class="flex items-center justify-between mb-1">
                                <div class="flex items-center space-x-1">
                                    ${this.renderStars(rating)}
                                </div>
                                <span class="text-xs text-gray-500">User ${review.user_id}</span>
                            </div>
                            ${reviewText ? `<p class="text-xs text-gray-700 line-clamp-2">${reviewText}</p>` : '<p class="text-xs text-gray-400 italic">Aucun commentaire</p>'}
                        </div>
                    `;
                    }).join('')}
                </div>
            </div>
        ` : '';
        
        // Image with fallback
        const imageHTML = image_url ? 
            `<img src="${image_url}" alt="${name}" class="w-full h-48 object-cover" onerror="this.src='https://via.placeholder.com/400x300?text=Save+Eat'">` :
            `<div class="w-full h-48 bg-green-100 flex items-center justify-center">
                <svg class="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"></path>
                </svg>
            </div>`;
        
        return `
            <div class="recipe-card bg-white rounded-xl shadow-lg overflow-hidden relative" data-recipe-id="${recipe_id}">
                <!-- Close button (top right) -->
                <button onclick="app.removeRecipe(${recipe_id})" 
                        class="absolute top-2 right-2 bg-white rounded-full p-1.5 shadow-lg hover:bg-gray-100 z-10 transition-all opacity-80 hover:opacity-100">
                    <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
                
                <!-- Image -->
                ${imageHTML}
                
                <!-- Content -->
                <div class="p-5">
                    <!-- Header -->
                    <div class="flex items-start justify-between mb-3">
                        <h3 class="text-lg font-bold text-gray-900 line-clamp-2 flex-1">
                            ${name || 'Recette sans titre'}
                        </h3>
                    </div>
                    
                    <!-- Rating -->
                    ${ratingHTML}
                    
                    <!-- Description -->
                    ${description ? `<p class="text-sm text-gray-600 line-clamp-2 mb-3">${description}</p>` : ''}
                    
                    <!-- Stats -->
                    <div class="flex items-center justify-between mb-3 text-sm text-gray-600">
                        <div class="flex items-center space-x-4">
                            ${minutes ? `
                                <span class="flex items-center">
                                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                    ${Math.round(minutes)} min
                                </span>
                            ` : ''}
                            ${calories ? `
                                <span class="flex items-center">
                                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"></path>
                                    </svg>
                                    ${Math.round(calories)} cal
                                </span>
                            ` : ''}
                        </div>
                        ${n_ingredients ? `
                            <span class="text-xs font-medium text-gray-500">
                                ${n_ingredients} ingrédients
                            </span>
                        ` : ''}
                    </div>
                    
                    <!-- Nutrition Bars -->
                    ${nutritionHTML}
                    
                    <!-- Reviews -->
                    ${reviewsHTML}
                    
                    <!-- Actions -->
                    <button onclick="app.viewRecipe(${recipe_id})" 
                            class="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition-all transform hover:scale-[1.02] mt-3">
                        Voir la recette
                    </button>
                </div>
            </div>
        `;
    }
    
    renderStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
        
        let starsHTML = '';
        
        // Full stars
        for (let i = 0; i < fullStars; i++) {
            starsHTML += '<svg class="w-4 h-4 text-yellow-400 fill-current" viewBox="0 0 20 20"><path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/></svg>';
        }
        
        // Half star
        if (hasHalfStar) {
            starsHTML += '<svg class="w-4 h-4 text-yellow-400 fill-current" viewBox="0 0 20 20"><path d="M10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545L10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0z" fill-opacity="0.5"/></svg>';
        }
        
        // Empty stars
        for (let i = 0; i < emptyStars; i++) {
            starsHTML += '<svg class="w-4 h-4 text-gray-300 fill-current" viewBox="0 0 20 20"><path d="M10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545L10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0z"/></svg>';
        }
        
        return starsHTML;
    }

    async searchRecipes() {
        if (this.selectedIngredients.size === 0) {
            alert('⚠️ Veuillez sélectionner au moins un ingrédient');
            return;
        }

        // Show loading
        document.getElementById('resultsSection').classList.add('hidden');
        document.getElementById('emptyState').classList.add('hidden');
        document.getElementById('loadingState').classList.remove('hidden');

        // Scroll to results
        document.getElementById('loadingState').scrollIntoView({ behavior: 'smooth', block: 'start' });

        try {
            const maxTime = document.getElementById('maxTime').value;
            const maxCalories = document.getElementById('maxCalories').value;
            const topK = parseInt(document.getElementById('topK').value) || 10;

            // Use actual user ID from UserManager
            const userId = this.userManager.getUserId() || 1;

            const requestBody = {
                user_id: userId,
                available_ingredients: Array.from(this.selectedIngredients),
                top_k: topK,
                use_profile: true  // Enable profile-based filtering
            };

            if (maxTime) requestBody.max_time = parseFloat(maxTime);
            if (maxCalories) requestBody.max_calories = parseFloat(maxCalories);
            if (this.selectedDietaryPrefs.size > 0) {
                requestBody.dietary_preferences = Array.from(this.selectedDietaryPrefs);
            }

            console.log('🔍 Searching recipes with:', requestBody);
            console.log(`👤 Using profile filtering for user ${userId}`);

            const response = await fetch('/api/v1/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            console.log('✅ Received recommendations:', data);

            // Hide loading
            document.getElementById('loadingState').classList.add('hidden');

            if (data.recipe_ids && data.recipe_ids.length > 0) {
                await this.displayRecipes(data);
            } else {
                document.getElementById('emptyState').classList.remove('hidden');
            }

        } catch (error) {
            console.error('Error searching recipes:', error);
            document.getElementById('loadingState').classList.add('hidden');
            alert(`❌ Erreur: ${error.message}`);
        }
    }

    async displayRecipes(data) {
        const { recipe_ids, scores, explanations } = data;
        
        // Fetch full recipe details
        const recipes = await Promise.all(
            recipe_ids.map(async (id, idx) => {
                try {
                    const response = await fetch(`/api/v1/recipe/${id}`);
                    const recipe = await response.json();
                    recipe.score = scores[idx];
                    recipe.explanation = explanations ? explanations[idx] : '';
                    return recipe;
                } catch (error) {
                    console.error(`Error fetching recipe ${id}:`, error);
                    return null;
                }
            })
        );

        const validRecipes = recipes.filter(r => r !== null);

        if (validRecipes.length === 0) {
            document.getElementById('emptyState').classList.remove('hidden');
            return;
        }

        // Update count
        document.getElementById('resultsCount').textContent = validRecipes.length;

        // Render recipes
        const grid = document.getElementById('recipesGrid');
        grid.innerHTML = validRecipes.map(recipe => this.createRecipeCard(recipe)).join('');

        // Show results
        document.getElementById('resultsSection').classList.remove('hidden');
        document.getElementById('resultsSection').classList.add('fade-in');

        // Smooth scroll
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    removeRecipe(recipeId) {
        // Find the recipe card element
        const recipeCard = document.querySelector(`[data-recipe-id="${recipeId}"]`);
        if (!recipeCard) {
            console.warn(`Recipe card with ID ${recipeId} not found`);
            return;
        }

        // Remove with animation
        recipeCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        recipeCard.style.opacity = '0';
        recipeCard.style.transform = 'scale(0.9)';

        setTimeout(() => {
            recipeCard.remove();

            // Update count
            const remainingCards = document.querySelectorAll('[data-recipe-id]').length;
            document.getElementById('resultsCount').textContent = remainingCards;

            // If no recipes left, show empty state
            if (remainingCards === 0) {
                document.getElementById('resultsSection').classList.add('hidden');
                document.getElementById('emptyState').classList.remove('hidden');
            }
        }, 300);
    }

    createRecipeCard(recipe) {
        const {
            recipe_id,
            name,
            description,
            image_url,
            minutes,
            calories,
            protein,
            carbohydrates,
            total_fat,
            ingredients_list,
            n_ingredients,
            tags,
            score,
            explanation
        } = recipe;

        // Nutrition info
        const nutritionHTML = this.createNutritionBars(calories, protein, carbohydrates, total_fat);

        // Tags (first 3)
        const displayTags = tags && tags.length > 0 ? tags.slice(0, 3) : [];
        const tagsHTML = displayTags.map(tag => 
            `<span class="badge px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">${tag}</span>`
        ).join('');

        // Match score badge
        const matchPercent = Math.round(score * 100);
        const matchColor = matchPercent >= 80 ? 'bg-green-500' : matchPercent >= 60 ? 'bg-yellow-500' : 'bg-gray-500';

        // Image with fallback
        const imageHTML = image_url ? 
            `<img src="${image_url}" alt="${name}" class="w-full h-48 object-cover" onerror="this.src='https://via.placeholder.com/400x300?text=Save+Eat'">` :
            `<div class="w-full h-48 bg-green-100 flex items-center justify-center">
                <svg class="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"></path>
                </svg>
            </div>`;

        return `
            <div class="recipe-card bg-white rounded-xl shadow-lg overflow-hidden relative" data-recipe-id="${recipe_id}">
                <!-- Close button (top right) -->
                <button onclick="app.removeRecipe(${recipe_id})" 
                        class="absolute top-2 right-2 bg-white rounded-full p-1.5 shadow-lg hover:bg-gray-100 z-10 transition-all opacity-80 hover:opacity-100">
                    <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
                
                <!-- Image -->
                ${imageHTML}
                
                <!-- Content -->
                <div class="p-5">
                    <!-- Header -->
                    <div class="flex items-start justify-between mb-3">
                        <h3 class="text-lg font-bold text-gray-900 line-clamp-2 flex-1">
                            ${name || 'Recette sans titre'}
                        </h3>
                        <div class="${matchColor} text-white px-2 py-1 rounded-lg text-xs font-bold ml-2">
                            ${matchPercent}%
                        </div>
                    </div>

                    <!-- Description -->
                    ${description ? `<p class="text-sm text-gray-600 line-clamp-2 mb-3">${description}</p>` : ''}

                    <!-- Stats -->
                    <div class="flex items-center justify-between mb-3 text-sm text-gray-600">
                        <div class="flex items-center space-x-4">
                            ${minutes ? `
                                <span class="flex items-center">
                                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                    ${Math.round(minutes)} min
                                </span>
                            ` : ''}
                            ${calories ? `
                                <span class="flex items-center">
                                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"></path>
                                    </svg>
                                    ${Math.round(calories)} cal
                                </span>
                            ` : ''}
                        </div>
                        ${n_ingredients ? `
                            <span class="text-xs font-medium text-gray-500">
                                ${n_ingredients} ingrédients
                            </span>
                        ` : ''}
                    </div>

                    <!-- Nutrition Bars -->
                    ${nutritionHTML}

                    <!-- Tags -->
                    ${tagsHTML ? `
                        <div class="flex flex-wrap gap-1 mb-3">
                            ${tagsHTML}
                        </div>
                    ` : ''}

                    <!-- Explanation -->
                    ${explanation ? `
                        <div class="text-xs text-gray-600 bg-gray-50 rounded-lg p-2 mb-3">
                            ${explanation}
                        </div>
                    ` : ''}

                    <!-- Actions -->
                    <button onclick="app.viewRecipe(${recipe_id})" 
                            class="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition-all transform hover:scale-[1.02]">
                        Voir la recette
                    </button>
                </div>
            </div>
        `;
    }

    createNutritionBars(calories, protein, carbs, fat) {
        if (!calories && !protein && !carbs && !fat) return '';

        // Calculate percentages (based on daily values)
        const dailyValues = {
            calories: 2000,
            protein: 50,
            carbs: 300,
            fat: 70
        };

        const items = [];
        
        if (calories) {
            const percent = Math.min((calories / dailyValues.calories) * 100, 100);
            items.push({ label: 'Calories', value: Math.round(calories), percent, color: 'bg-red-500' });
        }
        if (protein) {
            const percent = Math.min((protein / dailyValues.protein) * 100, 100);
            items.push({ label: 'Protéines', value: Math.round(protein), percent, color: 'bg-blue-500' });
        }
        if (carbs) {
            const percent = Math.min((carbs / dailyValues.carbs) * 100, 100);
            items.push({ label: 'Glucides', value: Math.round(carbs), percent, color: 'bg-yellow-500' });
        }
        if (fat) {
            const percent = Math.min((fat / dailyValues.fat) * 100, 100);
            items.push({ label: 'Lipides', value: Math.round(fat), percent, color: 'bg-purple-500' });
        }

        return `
            <div class="space-y-2 mb-3">
                ${items.map(item => `
                    <div>
                        <div class="flex justify-between text-xs text-gray-600 mb-1">
                            <span>${item.label}</span>
                            <span class="font-semibold">${item.value}${item.label === 'Calories' ? '' : 'g'}</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-1.5">
                            <div class="nutrition-bar ${item.color} h-1.5 rounded-full" style="width: ${item.percent}%"></div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async viewRecipe(recipeId) {
        try {
            const response = await fetch(`/api/v1/recipe/${recipeId}`);
            const recipe = await response.json();

            // Create modal
            const modal = this.createRecipeModal(recipe);
            document.body.insertAdjacentHTML('beforeend', modal);

            // Add close listener
            document.getElementById('recipeModal').addEventListener('click', (e) => {
                if (e.target.id === 'recipeModal' || e.target.id === 'closeModal') {
                    document.getElementById('recipeModal').remove();
                }
            });

            // Log interaction
            await fetch('/api/v1/log_interaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: 1,
                    recipe_id: recipeId,
                    interaction_type: 'view',
                    available_ingredients: Array.from(this.selectedIngredients)
                })
            });

        } catch (error) {
            console.error('Error viewing recipe:', error);
            alert(`Erreur: ${error.message}`);
        }
    }

    createRecipeModal(recipe) {
        const {
            name,
            description,
            image_url,
            ingredients_list,
            steps_list,
            minutes,
            calories,
            protein,
            carbohydrates,
            total_fat,
            tags
        } = recipe;

        const ingredientsHTML = ingredients_list && ingredients_list.length > 0 ?
            ingredients_list.map(ing => `<li class="flex items-start"><span class="text-green-500 mr-2">•</span> ${this.capitalize(ing)}</li>`).join('') :
            '<li class="text-gray-500">Aucun ingrédient disponible</li>';

        const stepsHTML = steps_list && steps_list.length > 0 ?
            steps_list.map((step, idx) => `
                <div class="flex items-start mb-3">
                    <div class="flex-shrink-0 w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center font-bold mr-3">
                        ${idx + 1}
                    </div>
                    <p class="text-gray-700 flex-1 pt-1">${step}</p>
                </div>
            `).join('') :
            '<p class="text-gray-500">Aucune instruction disponible</p>';

        return `
            <div id="recipeModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto">
                <div class="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto relative">
                    <!-- Close button -->
                    <button id="closeModal" class="absolute top-4 right-4 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 z-10">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>

                    <!-- Image -->
                    ${image_url ? `
                        <img src="${image_url}" alt="${name}" class="w-full h-64 object-cover rounded-t-2xl" 
                             onerror="this.style.display='none'">
                    ` : ''}

                    <!-- Content -->
                    <div class="p-8">
                        <h2 class="text-3xl font-bold text-gray-900 mb-2">${name || 'Recette'}</h2>
                        ${description ? `<p class="text-gray-600 mb-4">${description}</p>` : ''}

                        <!-- Stats -->
                        <div class="flex flex-wrap gap-4 mb-6">
                            ${minutes ? `
                                <div class="flex items-center text-gray-700">
                                    <svg class="w-5 h-5 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                    <span class="font-semibold">${Math.round(minutes)} min</span>
                                </div>
                            ` : ''}
                            ${calories ? `
                                <div class="flex items-center text-gray-700">
                                    <svg class="w-5 h-5 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"></path>
                                    </svg>
                                    <span class="font-semibold">${Math.round(calories)} cal</span>
                                </div>
                            ` : ''}
                            ${protein ? `<span class="text-sm text-gray-600">Protéines: ${Math.round(protein)}g</span>` : ''}
                            ${carbohydrates ? `<span class="text-sm text-gray-600">Glucides: ${Math.round(carbohydrates)}g</span>` : ''}
                            ${total_fat ? `<span class="text-sm text-gray-600">Lipides: ${Math.round(total_fat)}g</span>` : ''}
                        </div>

                        <!-- Ingredients -->
                        <div class="mb-6">
                            <h3 class="text-xl font-bold text-gray-900 mb-3">🥕 Ingrédients</h3>
                            <ul class="space-y-2 text-gray-700">${ingredientsHTML}</ul>
                        </div>

                        <!-- Steps -->
                        <div>
                            <h3 class="text-xl font-bold text-gray-900 mb-3">👨‍🍳 Instructions</h3>
                            <div>${stepsHTML}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

}

// Initialize app
const app = new SaveEatApp();
console.log('✅ Save Eat App initialized');
