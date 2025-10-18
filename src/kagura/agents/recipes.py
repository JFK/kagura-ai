"""Recipe search agent for personal assistant use."""

from kagura import agent
from kagura.tools.brave_search import brave_web_search


@agent(model="gpt-5-mini", tools=[brave_web_search])
async def search_recipes(ingredients: str, cuisine: str = "any") -> str:
    """Find recipes with {{ ingredients }} ({{ cuisine }} cuisine)

    Search for recipes and format as helpful cooking suggestions.

    Instructions:
    1. Search for "{{ ingredients }} recipe {{ cuisine }}" or
       "how to cook {{ ingredients }}"
    2. Find recipes that use the specified ingredients
    3. Filter by cuisine type if specified (Japanese, Italian, Chinese, etc.)
    4. Format each recipe with:
       - **Recipe Title** in bold
       - Main ingredients list (brief)
       - Cooking time (if available)
       - Difficulty level (if available)
       - Link to full recipe
    5. Return 3-5 best matching recipes
    6. Prioritize: Clear instructions, high ratings, reputable sources

    Example output format:
    ```
    # Recipes with {{ ingredients|title }} ({{ cuisine|title }})

    1. **Chicken Teriyaki Bowl**
       Ingredients: Chicken breast, soy sauce, mirin, rice
       Time: 30 minutes | Difficulty: Easy
       A classic Japanese dish with sweet-savory glazed chicken
       [Recipe →](https://...)

    2. **Garlic Butter Chicken**
       Ingredients: Chicken, garlic, butter, herbs
       Time: 25 minutes | Difficulty: Easy
       Quick and flavorful weeknight dinner
       [Recipe →](https://...)

    3. **Chicken Stir-Fry**
       ...
    ```

    Be practical and focus on recipes people can actually make at home.
    Mention dietary considerations if relevant (vegetarian options, etc.).
    """
    ...
