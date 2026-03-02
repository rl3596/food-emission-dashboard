"""Food categorization using Cool Food Calculator categories.

Ported from Keyword Categorization Tool notebook.
"""

import pandas as pd

# 56 food categories with include/exclude keywords
CATEGORIES = {
    "Beef & buffalo meat": {
        "include": ["BEEF", "FRANK", "STEAK", "GELATIN"],
        "exclude": ["PLANTBASED", "VEGTRN", "VEG", "VEGETARIAN", "TUNA STEAK", "POTATO", "ALTERNATE"],
    },
    "Lamb/mutton & goat meat": {
        "include": ["LAMB", "MUTTON", "GOAT", "MEAT", "MTBALLS", "MTBL", "VEAL"],
        "exclude": ["PLANTBASED", "VEGTRN", "VEG", "VEGETARIAN", "TURKEY", "PROMOTION", "DUCK", "CRAB", "PORK", "ALTERNATE"],
    },
    "Pork (pig meat)": {
        "include": ["PORK", "BACON", "HAMBURGER", "SAUSAGE", "HAM", "LARD", "PANCETTA", "ANDOUILLE", "LINGUICA", "PEPPERONCINI", "PEPPERONI", "SALAMI", "MUSHU"],
        "exclude": ["PLANTBASED", "VEGTRN", "VEG", "VEGETARIAN", "CHICKEN", "TURKEY", "COLLARD"],
    },
    "Poultry (chicken, turkey)": {
        "include": ["CHICKEN", "TURKEY", "CHKN", "BUFFALO", "DUCK", "CHICK"],
        "exclude": ["PLANTBASED", "VEGTRN", "VEG", "VEGETARIAN"],
    },
    "Butter": {
        "include": ["BUTTER", "MARGARINE"],
        "exclude": ["BUTTERMILK", "BUTTERNUT", "PUDDING", "BUTTERSCOTCH", "PEANUT"],
    },
    "Cheese": {
        "include": ["CHEESE", "CHEESECAKE"],
        "exclude": ["RAVIOLI", "TORTELLINI", "VEGAN", "NON DAIRY"],
    },
    "Ice cream": {
        "include": ["ICE CREAM", "SOFT SERVE", "SOFTSERVE"],
        "exclude": [],
    },
    "Cream": {
        "include": ["CREAM"],
        "exclude": ["MILK", "HALF", "CEREAL", "CHEESE CREAM VEGAN", "CHEESE CREAM NON DAIRY", "SAUCE", "DRESSING"],
    },
    "Milk (cow's milk)": {
        "include": ["MILK", "HALF & HALF", "HALF AND HALF"],
        "exclude": ["YOGURT", "OAT", "ALMOND", "SOY", "COCONUT", "BUTTERMILK"],
    },
    "Yogurt": {
        "include": ["YOGURT", "BUTTERMILK"],
        "exclude": [],
    },
    "Eggs": {
        "include": ["EGG"],
        "exclude": ["EGGPLANT", "PASTA", "VEGGIE"],
    },
    "Fish (finfish)": {
        "include": ["FISH", "SALMON", "COD", "LOIN", "POLLOCK", "TUNA", "HAKE", "PANGASIUS", "TILAPIA", "HADDOCK", "SNAPPER", "ANCHOVY"],
        "exclude": ["VEGETARIAN", "FISHLESS"],
    },
    "Crustaceans (shrimp/prawns)": {
        "include": ["SHRIMP", "PRAWN", "CRAB", "LOBSTER"],
        "exclude": [],
    },
    "Mollusks": {
        "include": ["MOLLUSK", "CLAM", "CHOWDER", "MUSSEL", "SCALLOP", "OCTOPUS", "CALMARI", "SQUID", "CALAMARI"],
        "exclude": ["BEAN", "VEG", "VEGETARIAN", "VEGETABLE", "PASTA", "CHICKEN", "CHCKN"],
    },
    "Animal fats": {
        "include": ["ANIMAL FAT", "SEAFOOD"],
        "exclude": ["PROMOTION"],
    },
    "Legumes (misc.)": {
        "include": ["LEGUME", "VEGETABLE", "VEG", "VEGAN", "VEGGIE", "PLANTBASED", "VEGETARIAN", "RELISH"],
        "exclude": ["BURGER", "LENTIL", "MAYONNAISE", "BEAN", "PEA", "SAMOSA", "OATS", "CHEESE"],
    },
    "Beans and pulses (dried)": {
        "include": ["BEAN", "PULSE", "SPROUT", "FALAFEL", "LENTIL", "CHICKPEA"],
        "exclude": ["SOYBEAN", "CRANBERRY"],
    },
    "Peas": {
        "include": ["PEA", "PEAS"],
        "exclude": ["PEAR", "CHICKPEA", "PEACH", "PEARL", "PEARLED"],
    },
    "Peanuts/groundnuts": {
        "include": ["PEANUT", "GROUNDNUT", "CHESTNUT"],
        "exclude": [],
    },
    "Soybeans/Tofu": {
        "include": ["SOYBEAN", "TOFU", "SOY", "PLANTBASED", "VEGAN", "CHEESE VEGAN", "SEITAN STRIP", "SEITAN", "CHEESE CREAM VEGAN", "CHEESE CREAM NON DAIRY"],
        "exclude": ["SAUCE", "MILK"],
    },
    "Grains/cereals (except rice)": {
        "include": ["CEREAL", "QUINOA", "KASHA", "FARRO", "PARSLEY", "MILLETS", "FLOUR", "GRAIN", "SUCCOTASH"],
        "exclude": ["PASTA"],
    },
    "Corn (Maize)": {
        "include": ["CORN", "MAIZE", "TACO"],
        "exclude": ["MUFFIN"],
    },
    "Oats (Oatmeal)": {
        "include": ["OAT", "OATMEAL", "GRANOLA", "BREAKFAST BAR"],
        "exclude": ["COATING", "COOKIE", "MILK"],
    },
    "Wheat/Rye (Bread, pasta, baked goods)": {
        "include": ["WHEAT", "RYE", "BUN", "BREAD", "SPANAKOPITA", "SNACK MIX", "CREPE", "BAGEL", "SAMOSA", "CROUTON", "MINESTRONE", "BKD", "PRETZEL", "PASTA", "PASTRY", "BAKED GOODS", "BURGER", "WAFFLE", "TORTELLINI", "TORTILLA", "RAVIOLI", "TOAST FRENCH", "BARLEY", "CANNOLI", "COUSCOUS", "CRACKER", "QUESADILLA", "BISCUIT", "CAKE", "PANCAKE", "PIE", "PIEROGI", "MUFFIN", "CHIP", "COOKIE", "DOUGH", "BROWNIE", "NOODLE", "PIZZA", "HOAGIE"],
        "exclude": ["SYRUP", "POLLOCK", "SAUCE", "MAYONNAISE"],
    },
    "Rice": {
        "include": ["RICE", "SUSHI", "ROLL"],
        "exclude": [],
    },
    "Tree nuts and seeds": {
        "include": ["COCONUT", "SEED", "SESAME", "MUSTARD", "COCO", "SNACK BAR", "SNACK TRAIL", "PECAN", "CASHEW", "ALMOND", "PISTCH", "WALNUT", "HAZELNUT"],
        "exclude": ["OIL", "SEEDLESS", "SEEDLS", "SEEDLSS", "MILK ALMOND"],
    },
    "Almond milk": {
        "include": ["MILK ALMOND"],
        "exclude": [],
    },
    "Oat milk": {
        "include": ["MILK ORIGINAL OAT", "MILK OAT SILK ORIGINAL", "MILK OAT"],
        "exclude": [],
    },
    "Rice milk": {
        "include": ["RICE MILK"],
        "exclude": [],
    },
    "Soy milk": {
        "include": ["MILK SOY"],
        "exclude": [],
    },
    "Fruits (misc.)": {
        "include": ["FRUIT", "CHERRY", "WATERMELON", "DATE", "PLUM", "PAPAYA", "FIG DRIED", "RAISIN", "APRICOT", "MIX SMOOTHIE", "POMEGRANATE", "MELON", "PINEAPPLE", "PNAPL", "MANGO", "PASSION", "PEAR", "AVOCADO", "GUACAMOLE", "PEACH", "GUAVA", "BUTTERNUT", "SQUASH", "SAMPLE PRODUCE MISC FRSH"],
        "exclude": ["ZUCCHINI", "ONION", "SYRUP"],
    },
    "Apples": {
        "include": ["APPLE", "APPLESAUCE"],
        "exclude": ["VINEGAR"],
    },
    "Bananas": {
        "include": ["BANANA", "PLANTAIN"],
        "exclude": [],
    },
    "Berries": {
        "include": ["BERRY", "BLUEBERRY", "RASPBERRY", "STRAWBERRY", "STWBRY", "STRWRY", "RASP", "BLUE MACH"],
        "exclude": ["TOPPINGS", "TOPPING", "SYRUP", "DESSERT"],
    },
    "Citrus Fruit": {
        "include": ["CITRUS", "MANDARIN", "ORANGE", "GRPFRT", "GRAPEFRUIT", "KUMQUAT", "CRNBRY", "MARMALADE", "LEMON", "LMN", "LMNADELEMONADE", "LIME", "GRAPE"],
        "exclude": ["TOMATO"],
    },
    "Vegetables (misc.)": {
        "include": ["MUSHROOM", "EDAMAME", "ARTICHOKE", "SAKURA", "SALAD", "PALM HEART", "ROSEMARY", "OKRA", "PMPKN", "PUMPKIN", "THYME", "RHUBARB", "SAUERKRAUT", "WASABI", "ESCAROLE"],
        "exclude": ["OIL"],
    },
    "Cabbages and other Brassicas (Broccoli)": {
        "include": ["CABBAGE", "BROCCOLI", "KALE", "SPINACH", "COLLARD", "LETTUCE", "BOK CHOY", "GREEN MICRO RNBOW", "CAULIFLOWER", "ARUGULA"],
        "exclude": [],
    },
    "Tomatoes": {
        "include": ["TOMATO", "KETCHUP"],
        "exclude": [],
    },
    "Root Vegetables": {
        "include": ["CARROT", "RADISH", "BEET", "PARNISH"],
        "exclude": [],
    },
    "Onions and Leeks": {
        "include": ["ONION", "LEEK", "SHALLOT"],
        "exclude": ["SPICE"],
    },
    "Other vegetables": {
        "include": ["CELERY", "BAMBOO", "ASPARAGUS", "GOURD", "WATERCRESS FRESH ICELS", "TOMATILLO", "ZUCHHINI", "ZUCCHINI", "CHIVE", "LEAVES PALM", "CUCUMBER", "EGGPLANT", "FLOWER", "GIARDINIERA", "OLIVE"],
        "exclude": ["OIL"],
    },
    "Roots and Tubers": {
        "include": ["ROOT", "TUBER"],
        "exclude": [],
    },
    "Potatoes": {
        "include": ["POTATO"],
        "exclude": ["POTATO SWEET"],
    },
    "Cassava and Other Roots": {
        "include": ["CASSAVA", "POTATO SWEET", "YUCCA"],
        "exclude": [],
    },
    "Sugars and sweeteners": {
        "include": ["SUGAR", "SWEETENER", "CAPER", "BAKLAVA", "TART", "CHOCOLATE WHITE", "FLAN CARAMEL", "ICING RTU", "MOLASSES", "GRENADINE", "NUTELLA", "CUSTARD", "QUICHE", "CANDY", "DESSERT", "CHURRO", "HONEY", "JAM", "PETIT FOUR", "JELLY", "MARSHMALLOW", "PUDDING", "SPREAD CHOCOLATE", "SPRINKLE CHOCOLATE", "SPRINKLE", "SYRUP"],
        "exclude": ["DRESSING", "SAUCE"],
    },
    "Vegetable oils": {
        "include": ["DRESSING", "SAUCE", "TOPPING", "HUMMUS", "PAN COATING BUTR SPRAY", "OIL VEGETABLE", "DIJON", "MAYONNAISE", "OIL TRUFFLE BLK"],
        "exclude": ["SOYBEAN", "PALM", "SUNFLOWER", "RAPESEED", "CANOLA", "OLIVE"],
    },
    "Soybeans (Oil)": {
        "include": ["OIL SOYBEAN"],
        "exclude": [],
    },
    "Palm (Oil)": {
        "include": ["OIL PALM"],
        "exclude": [],
    },
    "Sunflower (Oil)": {
        "include": ["OIL SUNFLOWER"],
        "exclude": [],
    },
    "Rapeseed/canola (Oil)": {
        "include": ["OIL RAPESEED", "OIL CANOLA", "CANOLA", "SESAME"],
        "exclude": [],
    },
    "Olives (Oil)": {
        "include": ["OIL OLIVE", "OIL TRUFFLE"],
        "exclude": [],
    },
    "Alcohol": {
        "include": ["ALCOHOL"],
        "exclude": [],
    },
    "Barley (Beer)": {
        "include": ["BEER"],
        "exclude": [],
    },
    "Wine Grapes (Wine)": {
        "include": [],
        "exclude": [],
    },
    "Stimulants": {
        "include": ["VINEGAR", "BALSAMIC", "RED BULL", "JUICE DRINK", "PASTE CURRY", "TEA", "REDBULL", "CHOC DARK PWDR", "WINE GRAPE", "WINE", "COLORING", "PASTE", "PASTE TAMARIND", "DRINK ENERGY", "CHUTNEY TAMARIND", "CHUTNEY", "POWDER BAKING", "PASTE TAHINI", "CHILI", "PICKLE", "SODA", "SALSA"],
        "exclude": [],
    },
    "Cocoa": {
        "include": ["COCOA", "BAKING CACOA", "CHOCOLATE DARK"],
        "exclude": [],
    },
    "Coffee": {
        "include": ["COFFEE"],
        "exclude": [],
    },
    "Stimulants & Spices (misc.)": {
        "include": ["SPICE", "PEPPER", "SALT", "SEAWEED", "GNGR", "BASIL", "CILANTRO", "VANILLA", "GARLIC", "MINT", "GINGER", "SEASONING", "HERB"],
        "exclude": [],
    },
}


def categorize_food_item(description: str) -> str:
    """Categorize a single food item by its description.

    Args:
        description: Food item description string.

    Returns:
        Category name, or "Uncategorized" if no match.
    """
    desc_upper = str(description).upper()
    for category, keywords in CATEGORIES.items():
        includes = keywords["include"]
        excludes = keywords["exclude"]
        if includes and any(kw in desc_upper for kw in includes):
            if not any(ex in desc_upper for ex in excludes):
                return category
    return "Uncategorized"


def add_category(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'category' column to the DataFrame based on food descriptions.

    Args:
        df: DataFrame with a 'description' column.

    Returns:
        DataFrame with added 'category' column.
    """
    df = df.copy()
    df["category"] = df["description"].apply(categorize_food_item)
    return df
