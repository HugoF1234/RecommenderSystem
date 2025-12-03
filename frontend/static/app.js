// Save Eat - Modern Frontend JavaScript
// Handles all user interactions and API calls

class SaveEatApp {
    constructor() {
        this.selectedIngredients = new Set();
        this.selectedDietaryPrefs = new Set();
        this.ingredients = [];
        this.filteredIngredients = [];
        this.init();
    }

    async init() {
        console.log('🚀 Initializing Save Eat App...');
        await this.loadIngredients();
        this.setupEventListeners();
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
        const container = document.getElementById('selectedIngredientsContainer');
        if (!container) return;

        const selected = Array.from(this.selectedIngredients);

        if (selected.length === 0) {
            container.innerHTML = '';
            return;
        }

        container.innerHTML = selected.map(ing => `
            <button 
                data-ingredient="${ing}"
                class="flex items-center gap-1 px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 text-xs font-medium border border-emerald-300 hover:bg-emerald-200 transition-all">
                <span>${this.capitalize(ing)}</span>
                <span class="text-emerald-700 text-xs font-bold">×</span>
            </button>
        `).join('');

        // Clicking on a selected chip removes it and updates both lists
        container.querySelectorAll('button[data-ingredient]').forEach(btn => {
            btn.addEventListener('click', () => {
                const ing = btn.dataset.ingredient;
                if (this.selectedIngredients.has(ing)) {
                    this.selectedIngredients.delete(ing);
                    this.renderIngredients();
                    this.renderSelectedIngredients();
                }
            });
        });
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

        // Enter key on inputs
        ['maxTime', 'maxCalories', 'topK'].forEach(id => {
            document.getElementById(id).addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.searchRecipes();
            });
        });
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

            const requestBody = {
                user_id: 1,
                available_ingredients: Array.from(this.selectedIngredients),
                top_k: topK
            };

            if (maxTime) requestBody.max_time = parseFloat(maxTime);
            if (maxCalories) requestBody.max_calories = parseFloat(maxCalories);
            if (this.selectedDietaryPrefs.size > 0) {
                requestBody.dietary_preferences = Array.from(this.selectedDietaryPrefs);
            }

            console.log('🔍 Searching recipes with:', requestBody);

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
            `<div class="w-full h-48 bg-gradient-to-br from-green-100 to-blue-100 flex items-center justify-center">
                <svg class="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"></path>
                </svg>
            </div>`;

        return `
            <div class="recipe-card bg-white rounded-xl shadow-lg overflow-hidden">
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
                            class="w-full bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white font-semibold py-2 px-4 rounded-lg transition-all transform hover:scale-[1.02]">
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
