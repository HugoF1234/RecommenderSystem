/**
 * Save Eat - Frontend Application
 */

// Auto-detect API URL: use current host in production, localhost in development
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000/api/v1'
    : `${window.location.protocol}//${window.location.host}/api/v1`;

// DOM Elements
const searchBtn = document.getElementById('searchBtn');
const loadingDiv = document.getElementById('loading');
const resultsSection = document.getElementById('results');
const recipeGrid = document.getElementById('recipeGrid');
const ingredientsContainer = document.getElementById('ingredientsContainer');

// Event Listeners
searchBtn.addEventListener('click', handleSearch);
document.addEventListener('DOMContentLoaded', loadIngredients);

// Store recipe data cache
let recipeDataCache = {};

/**
 * Load available ingredients from API
 */
async function loadIngredients() {
    try {
        const response = await fetch(`${API_BASE_URL}/ingredients?limit=500`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        const ingredients = data.ingredients || [];
        
        // Check if there's a message about missing data
        if (ingredients.length === 0 && data.message) {
            ingredientsContainer.innerHTML = `<div class="col-span-full text-center text-yellow-600 text-sm py-4">${data.message}</div>`;
            return;
        }
        
        if (ingredients.length === 0) {
            ingredientsContainer.innerHTML = '<div class="col-span-full text-center text-gray-500 text-sm py-4">Aucun ingrédient disponible. Veuillez charger les données.</div>';
            return;
        }
        
        ingredientsContainer.innerHTML = '';
        
        ingredients.forEach(ingredient => {
            const label = document.createElement('label');
            label.className = 'flex items-center space-x-2 p-2 rounded hover:bg-white cursor-pointer';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = ingredient;
            checkbox.className = 'ingredient-checkbox rounded text-coral focus:ring-coral';
            
            const span = document.createElement('span');
            span.className = 'text-sm text-gray-700';
            span.textContent = ingredient.charAt(0).toUpperCase() + ingredient.slice(1);
            
            label.appendChild(checkbox);
            label.appendChild(span);
            ingredientsContainer.appendChild(label);
        });
    } catch (error) {
        console.error('Error loading ingredients:', error);
        ingredientsContainer.innerHTML = '<div class="col-span-full text-center text-red-500 text-sm py-4">Erreur lors du chargement des ingrédients</div>';
    }
}

/**
 * Handle recipe search
 */
async function handleSearch() {
    const maxTime = document.getElementById('maxTime').value ? parseFloat(document.getElementById('maxTime').value) : null;
    const topK = 10;
    
    const availableIngredients = Array.from(document.querySelectorAll('.ingredient-checkbox:checked'))
        .map(cb => cb.value);
    
    const dietaryPrefs = Array.from(document.querySelectorAll('.dietary-pref:checked'))
        .map(cb => cb.value);
    
    if (availableIngredients.length === 0) {
        alert('Veuillez sélectionner au moins un ingrédient');
        return;
    }
    
    loadingDiv.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    
    try {
        const response = await fetch(`${API_BASE_URL}/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: 1,
                available_ingredients: availableIngredients,
                max_time: maxTime,
                dietary_preferences: dietaryPrefs.length > 0 ? dietaryPrefs : null,
                top_k: topK
            })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        loadingDiv.classList.add('hidden');
        displayRecipes(data);
    } catch (error) {
        console.error('Error fetching recommendations:', error);
        loadingDiv.classList.add('hidden');
        alert('Erreur lors de la recherche. Assurez-vous que l\'API est démarrée.');
    }
}

/**
 * Display recipe recommendations
 */
function displayRecipes(data) {
    recipeGrid.innerHTML = '';
    
    if (!data.recipe_ids || data.recipe_ids.length === 0) {
        recipeGrid.innerHTML = '<div class="col-span-full bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center text-yellow-800">Aucune recette trouvée</div>';
        resultsSection.classList.remove('hidden');
        return;
    }
    
    // Fetch recipe images in parallel
    data.recipe_ids.forEach(recipeId => {
        fetch(`${API_BASE_URL}/recipe/${recipeId}`)
            .then(response => response.ok ? response.json() : null)
            .then(recipe => { if (recipe) recipeDataCache[recipeId] = recipe; })
            .catch(err => console.warn(`Could not fetch recipe ${recipeId}:`, err));
    });
    
    // Create recipe cards
    data.recipe_ids.forEach((recipeId, index) => {
        const score = data.scores ? data.scores[index] : null;
        const explanation = data.explanations ? data.explanations[index] : null;
        const card = createRecipeCard(recipeId, score, explanation);
        recipeGrid.appendChild(card);
    });
    
    resultsSection.classList.remove('hidden');
}

/**
 * Create a recipe card element
 */
function createRecipeCard(recipeId, score, explanation) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-sm p-4 hover:shadow-md transition-shadow border border-gray-100';
    
    // Extract recipe name from explanation
    let recipeName = `Recette #${recipeId}`;
    if (explanation) {
        const parts = explanation.split(':');
        if (parts.length > 1) {
            recipeName = parts[parts.length - 1].trim();
        }
    }
    
    // Get image from cache
    const imageUrl = recipeDataCache[recipeId]?.image_url || null;
    const imageHtml = imageUrl ? `
        <div class="mb-3 overflow-hidden rounded-lg">
            <img src="${imageUrl}" alt="${recipeName}" class="w-full h-40 object-cover" 
                 onerror="this.style.display='none';">
        </div>
    ` : '';
    
    // Score display
    let scoreDisplay = '';
    if (score !== null && score !== undefined) {
        const scorePercent = Math.round(score * 100);
        scoreDisplay = `
            <div class="mb-3">
                <div class="flex items-center justify-between mb-1">
                    <span class="text-xs text-gray-600">Pertinence</span>
                    <span class="text-xs font-semibold text-gray-700">${scorePercent}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-gradient-to-r from-coral to-orange h-2 rounded-full" style="width: ${scorePercent}%"></div>
                </div>
            </div>
        `;
    }
    
    card.innerHTML = `
        <div class="flex flex-col h-full">
            ${imageHtml}
            <h4 class="text-lg font-bold text-gray-800 mb-2 line-clamp-2">${recipeName}</h4>
            ${scoreDisplay}
            ${explanation ? `<p class="text-sm text-gray-600 mb-4 line-clamp-2">${explanation.replace(/^(✅|⚠️)\s*/, '')}</p>` : ''}
            <button 
                onclick="viewRecipe(${recipeId})"
                class="mt-auto bg-gradient-to-r from-coral to-orange text-white px-4 py-2 rounded-lg hover:opacity-90 transition-opacity text-sm font-semibold"
            >
                Voir la recette
            </button>
        </div>
    `;
    
    return card;
}

/**
 * View recipe details
 */
async function viewRecipe(recipeId) {
    const modal = document.getElementById('recipeModal');
    const modalName = document.getElementById('modalRecipeName');
    const modalContent = document.getElementById('modalRecipeContent');
    
    modal.classList.remove('hidden');
    modalName.textContent = 'Chargement...';
    modalContent.innerHTML = '<div class="text-center py-8"><div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-coral"></div><p class="mt-4 text-gray-600">Chargement...</p></div>';
    
    try {
        const [recipeResponse, reviewsResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/recipe/${recipeId}`),
            fetch(`${API_BASE_URL}/recipe/${recipeId}/reviews`)
        ]);
        
        if (!recipeResponse.ok) throw new Error(`HTTP error! status: ${recipeResponse.status}`);
        
        const recipe = await recipeResponse.json();
        const reviewsData = reviewsResponse.ok ? await reviewsResponse.json() : { reviews: [] };
        
        recipeDataCache[recipeId] = recipe;
        modalName.textContent = recipe.name || `Recette #${recipeId}`;
        
        let html = '';
        
        // Recipe image
        if (recipe.image_url) {
            html += `<div class="mb-6 overflow-hidden rounded-lg">
                <img src="${recipe.image_url}" alt="${recipe.name}" class="w-full h-64 object-cover" 
                     onerror="this.style.display='none';">
            </div>`;
        }
        
        // Description
        if (recipe.description && recipe.description.trim() !== '') {
            html += `<div class="mb-6 p-4 bg-gray-50 rounded-lg">
                <h3 class="text-lg font-semibold text-gray-800 mb-2">Description</h3>
                <p class="text-gray-700">${recipe.description}</p>
            </div>`;
        }
        
        // Info badges
        html += '<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">';
        if (recipe.prep_time > 0) {
            const hours = Math.floor(recipe.prep_time / 60);
            const minutes = recipe.prep_time % 60;
            const timeDisplay = hours > 0 ? `${hours}h${minutes > 0 ? minutes : ''}` : `${minutes}min`;
            html += `<div class="bg-orange-50 rounded-lg p-3 text-center border border-orange-200">
                <p class="text-xs text-gray-600 mb-1">⏱️ Temps</p>
                <p class="text-lg font-bold text-orange">${timeDisplay}</p>
            </div>`;
        }
        if (recipe.calories > 0) {
            html += `<div class="bg-rose-50 rounded-lg p-3 text-center border border-rose-200">
                <p class="text-xs text-gray-600 mb-1">🔥 Calories</p>
                <p class="text-lg font-bold text-rose">${Math.round(recipe.calories)}</p>
            </div>`;
        }
        if (recipe.protein > 0) {
            html += `<div class="bg-violet-50 rounded-lg p-3 text-center border border-violet-200">
                <p class="text-xs text-gray-600 mb-1">💪 Protéines</p>
                <p class="text-lg font-bold text-violet">${Math.round(recipe.protein)}g</p>
            </div>`;
        }
        if (recipe.carbohydrates > 0) {
            html += `<div class="bg-teal-50 rounded-lg p-3 text-center border border-teal-200">
                <p class="text-xs text-gray-600 mb-1">🌾 Glucides</p>
                <p class="text-lg font-bold text-teal">${Math.round(recipe.carbohydrates)}g</p>
            </div>`;
        }
        html += '</div>';
        
        // Ingredients
        if (recipe.ingredients && recipe.ingredients.length > 0) {
            html += `<div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-800 mb-3">Ingrédients (${recipe.ingredients.length})</h3>
                <ul class="grid grid-cols-1 md:grid-cols-2 gap-2">`;
            recipe.ingredients.forEach(ingredient => {
                const ingName = String(ingredient).charAt(0).toUpperCase() + String(ingredient).slice(1);
                html += `<li class="flex items-center space-x-2 p-2 bg-gray-50 border border-gray-200 rounded">
                    <span class="text-gray-700">${ingName}</span>
                </li>`;
            });
            html += '</ul></div>';
        }
        
        // Steps
        if (recipe.steps && recipe.steps.length > 0) {
            html += `<div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-800 mb-3">Instructions (${recipe.steps.length} étapes)</h3>
                <ol class="space-y-2">`;
            recipe.steps.forEach((step, index) => {
                html += `<li class="flex items-start space-x-3 p-3 bg-gray-50 rounded border border-gray-200">
                    <span class="flex-shrink-0 w-6 h-6 bg-coral text-white rounded-full flex items-center justify-center text-sm font-bold">${index + 1}</span>
                    <span class="text-gray-700">${step}</span>
                </li>`;
            });
            html += '</ol></div>';
        }
        
        // Reviews
        if (reviewsData.reviews && reviewsData.reviews.length > 0) {
            html += `<div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-800 mb-3">Avis (${reviewsData.reviews.length})</h3>
                <div class="space-y-3">`;
            reviewsData.reviews.forEach(review => {
                const stars = review.rating ? '⭐'.repeat(Math.round(review.rating)) : '';
                html += `<div class="p-3 bg-yellow-50 border border-yellow-200 rounded">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-semibold text-gray-800">${review.author || 'Anonymous'}</span>
                        ${review.rating ? `<span class="text-yellow-500">${stars} (${review.rating}/5)</span>` : ''}
                    </div>
                    ${review.review ? `<p class="text-gray-700 text-sm">${review.review}</p>` : ''}
                </div>`;
            });
            html += '</div></div>';
        }
        
        modalContent.innerHTML = html;
    } catch (error) {
        console.error('Error loading recipe:', error);
        modalContent.innerHTML = '<div class="text-center py-8"><p class="text-red-500 mb-4">Erreur lors du chargement</p></div>';
    }
}

/**
 * Close recipe modal
 */
function closeRecipeModal() {
    document.getElementById('recipeModal').classList.add('hidden');
}

// Make functions globally available
window.viewRecipe = viewRecipe;
window.closeRecipeModal = closeRecipeModal;
