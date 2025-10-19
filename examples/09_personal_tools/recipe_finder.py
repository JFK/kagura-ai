"""Recipe Finder Example - AI-Powered Meal Planning

This example demonstrates how to use Kagura AI's recipe search tool to find
recipes based on ingredients you have or dietary preferences.

Usage:
    # No extra dependencies needed
    python examples/10_personal_tools/recipe_finder.py

    # Or specify ingredients
    python examples/10_personal_tools/recipe_finder.py --ingredients "chicken,rice,vegetables"
"""

import asyncio

import click
from kagura.agents import search_recipes


async def find_recipes_by_ingredients(
    ingredients: str,
    cuisine: str = "any",
    dietary: str | None = None,
) -> str:
    """
    Find recipes using available ingredients

    Args:
        ingredients: Comma-separated ingredients
        cuisine: Cuisine type (Italian, Asian, Mexican, etc.)
        dietary: Dietary restrictions (vegetarian, vegan, gluten-free, etc.)

    Returns:
        Formatted recipe suggestions
    """
    print("\n🔍 Searching recipes...")
    print(f"   Ingredients: {ingredients}")
    if cuisine != "any":
        print(f"   Cuisine: {cuisine}")
    if dietary:
        print(f"   Dietary: {dietary}")

    # Build search query
    query = f"{ingredients} recipes"
    if cuisine != "any":
        query += f" {cuisine} cuisine"
    if dietary:
        query += f", {dietary}"

    # Search recipes
    recipes = await search_recipes(query)

    # Format output
    output = f"""
{'=' * 60}
🍳 RECIPE SUGGESTIONS
{'=' * 60}

Ingredients: {ingredients}
Cuisine: {cuisine}
{f'Dietary: {dietary}' if dietary else ''}

{recipes}

{'=' * 60}
💡 Tip: Click the recipe links for full instructions!
{'=' * 60}
"""
    return output


async def meal_planner(days: int = 7) -> str:
    """
    Generate weekly meal plan

    Args:
        days: Number of days to plan (default: 7)

    Returns:
        Formatted meal plan
    """
    print(f"\n📅 Generating {days}-day meal plan...")

    # Diverse meal categories
    categories = [
        ("breakfast", "eggs, toast, fruit"),
        ("lunch", "salad, protein, grains"),
        ("dinner", "meat, vegetables, carbs"),
    ]

    meal_plan = f"""
{'=' * 60}
📅 {days}-DAY MEAL PLAN
{'=' * 60}

"""

    for day in range(1, min(days + 1, 4)):  # Sample 3 days
        meal_plan += f"\n{'─' * 60}\n"
        meal_plan += f"DAY {day}\n"
        meal_plan += f"{'─' * 60}\n"

        for meal_type, ingredients in categories:
            print(f"   Finding {meal_type} for day {day}...")
            query = f"{ingredients} recipes for {meal_type}"
            recipes = await search_recipes(query)

            # Extract first recipe title (simplified)
            meal_plan += f"\n{meal_type.upper()}:\n{recipes[:200]}...\n"

    meal_plan += f"""
{'=' * 60}
🛒 Shopping List: Generate from selected recipes
{'=' * 60}
"""

    return meal_plan


async def quick_dinner_ideas():
    """Quick dinner recipe search"""
    print("\n🍽️  Finding quick dinner ideas...")

    recipes = await search_recipes("quick dinner recipes under 30 minutes")

    print(f"""
{'=' * 60}
⚡ QUICK DINNER IDEAS (Under 30 min)
{'=' * 60}

{recipes}

{'=' * 60}
""")


@click.command()
@click.option(
    "--ingredients",
    help="Comma-separated ingredients (e.g., 'chicken,rice,broccoli')",
)
@click.option(
    "--cuisine",
    default="any",
    help="Cuisine type (Italian, Asian, Mexican, etc.)",
)
@click.option(
    "--dietary",
    help="Dietary restrictions (vegetarian, vegan, gluten-free, etc.)",
)
@click.option(
    "--meal-plan",
    is_flag=True,
    help="Generate weekly meal plan",
)
@click.option(
    "--quick",
    is_flag=True,
    help="Find quick dinner ideas (under 30 min)",
)
def main(
    ingredients: str | None,
    cuisine: str,
    dietary: str | None,
    meal_plan: bool,
    quick: bool,
):
    """Find recipes based on ingredients and preferences

    Examples:

        # Find recipes with specific ingredients
        python recipe_finder.py --ingredients "chicken,rice,vegetables"

        # Filter by cuisine
        python recipe_finder.py --ingredients "pasta,tomatoes" --cuisine Italian

        # Dietary restrictions
        python recipe_finder.py --ingredients "tofu,vegetables" --dietary vegan

        # Generate meal plan
        python recipe_finder.py --meal-plan

        # Quick dinner ideas
        python recipe_finder.py --quick
    """
    if meal_plan:
        result = asyncio.run(meal_planner(days=7))
        print(result)
    elif quick:
        asyncio.run(quick_dinner_ideas())
    elif ingredients:
        result = asyncio.run(
            find_recipes_by_ingredients(ingredients, cuisine, dietary)
        )
        print(result)
    else:
        # Interactive mode
        print("\n🍳 Recipe Finder - Interactive Mode")
        print("=" * 60)

        ingredients = input("Enter ingredients (comma-separated): ")
        cuisine = input("Cuisine preference (or 'any'): ") or "any"
        dietary = input("Dietary restrictions (or press Enter): ") or None

        result = asyncio.run(
            find_recipes_by_ingredients(ingredients, cuisine, dietary)
        )
        print(result)


if __name__ == "__main__":
    main()
