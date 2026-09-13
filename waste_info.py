"""
utils/waste_info.py
--------------------
Static knowledge base describing each of the 10 waste classes used by the
Smart Waste Classification model. This is what turns a bare label like
"plastic" into useful, actionable information for the user.

IMPORTANT: Biodegradability / recyclability of real-world waste often
depends on exact material composition and local facility capability.
Where that is true, the text below says so explicitly instead of
overclaiming.
"""

WASTE_INFO = {
    "battery": {
        "display_name": "Battery",
        "material": "Metal / chemical cells (alkaline, lithium-ion, lead-acid, etc.)",
        "biodegradable": False,
        "recyclable": "Yes — through certified e-waste/battery recycling only",
        "hazard_level": "high",
        "special_handling": True,
        "disposal": (
            "Do NOT place batteries in ordinary household or recycling bins. "
            "Batteries can leak corrosive/toxic chemicals and some types "
            "(especially lithium-ion) pose a fire risk if crushed or punctured. "
            "Take them to a designated battery/e-waste drop-off point, a "
            "retailer take-back program, or a household hazardous waste facility."
        ),
        "reuse_ideas": [
            "Rechargeable batteries can be reused many times before recycling",
            "Old battery casings are sometimes used in school science demos (dispose of cells separately)"
        ],
        "environmental_impact": (
            "Batteries contain heavy metals (lead, cadmium, mercury, lithium compounds) "
            "that can contaminate soil and groundwater if landfilled improperly. "
            "Proper recycling recovers valuable metals and prevents this contamination."
        ),
        "safety_warning": (
            "Potentially hazardous. Do not puncture, crush, burn, or expose to water. "
            "Swollen or damaged batteries should be handled with extra caution."
        ),
        "icon": "battery-full",
    },
    "biological": {
        "display_name": "Biological / Organic Waste",
        "material": "Food scraps, plant matter, other organic material",
        "biodegradable": True,
        "recyclable": "Not recyclable in the traditional sense, but compostable",
        "hazard_level": "low",
        "special_handling": False,
        "disposal": (
            "Best disposed of via composting or a municipal organic/green waste bin "
            "if available. If no composting option exists, dispose of with general waste."
        ),
        "reuse_ideas": [
            "Home composting to produce nutrient-rich soil",
            "Vermicomposting (worm bins) for small households",
            "Community/municipal green-waste collection where available"
        ],
        "environmental_impact": (
            "Organic waste decomposes naturally, but in landfills (where oxygen is limited) "
            "it produces methane, a potent greenhouse gas. Composting instead produces "
            "far fewer emissions and returns nutrients to soil."
        ),
        "safety_warning": None,
        "icon": "leaf",
    },
    "cardboard": {
        "display_name": "Cardboard",
        "material": "Corrugated or flat paperboard",
        "biodegradable": True,
        "recyclable": "Yes — widely recyclable if clean and dry",
        "hazard_level": "low",
        "special_handling": False,
        "disposal": (
            "Flatten and place in the paper/cardboard recycling stream. Remove tape, "
            "labels, and any food residue first — greasy or food-contaminated cardboard "
            "(e.g. pizza boxes) is often not recyclable and should go to general/organic waste."
        ),
        "reuse_ideas": [
            "Storage boxes and packing material",
            "Craft projects, DIY furniture, or drawer organizers",
            "Garden mulch / weed suppression sheeting"
        ],
        "environmental_impact": (
            "Recycling cardboard saves trees, water, and energy compared to producing "
            "virgin paperboard. It biodegrades naturally if it ends up in a landfill, "
            "though recycling is still the better option."
        ),
        "safety_warning": None,
        "icon": "package",
    },
    "clothes": {
        "display_name": "Clothes / Textiles",
        "material": "Natural or synthetic fabric (cotton, polyester, blends)",
        "biodegradable": "Depends on fabric — natural fibers biodegrade, synthetics largely do not",
        "recyclable": "Often reusable/donatable; recyclability depends on fabric blend",
        "hazard_level": "low",
        "special_handling": False,
        "disposal": (
            "If still wearable, donate or resell. If damaged, look for a textile "
            "recycling bin/program — many regions have dedicated clothing collection points. "
            "Avoid placing textiles in standard recycling bins as they can jam sorting machinery."
        ),
        "reuse_ideas": [
            "Donate to charity or thrift stores",
            "Repurpose as cleaning rags",
            "Upcycle into bags, quilts, or other craft projects"
        ],
        "environmental_impact": (
            "Textile production is resource-intensive (water, dyes, energy). Synthetic "
            "fabrics like polyester are essentially plastic and can take decades to "
            "break down, while shedding microplastics. Reuse and donation have the "
            "lowest environmental cost."
        ),
        "safety_warning": None,
        "icon": "shirt",
    },
    "glass": {
        "display_name": "Glass",
        "material": "Silica-based glass (bottles, jars, containers)",
        "biodegradable": False,
        "recyclable": "Yes — infinitely recyclable without quality loss, if not contaminated",
        "hazard_level": "medium",
        "special_handling": False,
        "disposal": (
            "Rinse and place in the glass recycling stream, separated by color where "
            "required locally. Broken glass should be wrapped safely before disposal "
            "to avoid injury to waste handlers."
        ),
        "reuse_ideas": [
            "Reuse jars for storage",
            "Decorative or craft purposes",
            "Repurpose bottles as vases or containers"
        ],
        "environmental_impact": (
            "Glass does not biodegrade but is one of the most recyclable materials — "
            "it can be recycled indefinitely with no loss in quality, saving raw "
            "materials and significant energy versus producing new glass."
        ),
        "safety_warning": "Broken glass is a cut hazard — handle and wrap carefully before disposal.",
        "icon": "wine",
    },
    "metal": {
        "display_name": "Metal",
        "material": "Ferrous or non-ferrous metal (cans, foil, scrap metal)",
        "biodegradable": False,
        "recyclable": "Yes — highly recyclable, especially aluminum and steel",
        "hazard_level": "low",
        "special_handling": False,
        "disposal": (
            "Rinse food residue off cans and place in the metal recycling stream. "
            "Sharp metal edges should be handled carefully and wrapped if disposed of."
        ),
        "reuse_ideas": [
            "Repurpose cans as containers or planters",
            "Scrap metal can often be sold to scrap dealers",
            "Craft and DIY projects"
        ],
        "environmental_impact": (
            "Metal recycling (particularly aluminum) saves a large amount of energy "
            "compared to mining and refining virgin ore, and metals can be recycled "
            "repeatedly without significant quality loss."
        ),
        "safety_warning": "Watch for sharp edges on cut or crushed metal.",
        "icon": "cog",
    },
    "paper": {
        "display_name": "Paper",
        "material": "Paper, newspaper, office paper, magazines",
        "biodegradable": True,
        "recyclable": "Yes — widely recyclable if clean and dry",
        "hazard_level": "low",
        "special_handling": False,
        "disposal": (
            "Place clean, dry paper in the paper recycling stream. Shredded paper, "
            "wet paper, or paper contaminated with food/oil is usually not recyclable "
            "and should go to general or organic waste."
        ),
        "reuse_ideas": [
            "Note-taking or scrap paper",
            "Packing/cushioning material",
            "Composting (in small amounts, uncoated paper only)"
        ],
        "environmental_impact": (
            "Recycling paper reduces deforestation, water use, and energy consumption "
            "compared to producing virgin paper. It also biodegrades relatively quickly "
            "if landfilled."
        ),
        "safety_warning": None,
        "icon": "file-text",
    },
    "plastic": {
        "display_name": "Plastic",
        "material": "Varies — PET, HDPE, PVC, LDPE, PP, PS, and others",
        "biodegradable": False,
        "recyclable": "Usually recyclable depending on the exact plastic type (check resin code)",
        "hazard_level": "low",
        "special_handling": False,
        "disposal": (
            "Check the resin identification code (the number inside the recycling "
            "triangle, if visible) and place in the correct plastics recycling stream "
            "per local guidelines. Rinse containers to remove residue."
        ),
        "reuse_ideas": [
            "Storage containers",
            "Craft materials or DIY projects",
            "Plant pots"
        ],
        "environmental_impact": (
            "Most plastics do not biodegrade and can persist in the environment for "
            "centuries, breaking down into microplastics. Recyclability varies "
            "significantly by plastic type and local facility capability — not all "
            "plastics marked 'recyclable' are accepted everywhere."
        ),
        "safety_warning": None,
        "icon": "flask-conical",
    },
    "shoes": {
        "display_name": "Shoes",
        "material": "Mixed materials — leather, fabric, rubber, foam, adhesives",
        "biodegradable": "Depends heavily on materials used (mixed-material item)",
        "recyclable": "Limited — some brands/programs accept shoes for recycling or donation",
        "hazard_level": "low",
        "special_handling": False,
        "disposal": (
            "If wearable, donate. If not, look for a shoe take-back/recycling program "
            "(some athletic brands run these). Because shoes combine many bonded "
            "materials, they are difficult for standard recycling facilities to process."
        ),
        "reuse_ideas": [
            "Donate to charity",
            "Repurpose as gardening shoes or craft material",
            "Some organizations repurpose old shoes for playground surfacing"
        ],
        "environmental_impact": (
            "Because shoes mix rubber, foam, textile, and adhesives, they are hard to "
            "recycle and mostly end up in landfill, where synthetic components can "
            "persist for a very long time."
        ),
        "safety_warning": None,
        "icon": "footprints",
    },
    "trash": {
        "display_name": "General Trash",
        "material": "Mixed / non-recyclable waste",
        "biodegradable": False,
        "recyclable": "No — not recyclable through standard streams",
        "hazard_level": "low",
        "special_handling": False,
        "disposal": (
            "Dispose of in general (residual) waste. Before doing so, double check "
            "the item isn't actually a recyclable material that's simply dirty or "
            "hard to identify — cleaning it may allow it to be recycled instead."
        ),
        "reuse_ideas": [
            "Consider whether the item can be repaired or reused before discarding",
        ],
        "environmental_impact": (
            "Items in this category typically end up in landfill or incineration. "
            "Reducing consumption and reusing items where possible are the most "
            "effective ways to minimize this category."
        ),
        "safety_warning": None,
        "icon": "trash-2",
    },
}

CLASS_NAMES = [
    "battery", "biological", "cardboard", "clothes", "glass",
    "metal", "paper", "plastic", "shoes", "trash",
]

# Confidence thresholds — configurable in one place
CONFIDENCE_THRESHOLDS = {
    "high": 0.75,     # >= 75%  -> "High confidence prediction"
    "medium": 0.45,   # 45-75%  -> "Moderate confidence — consider verifying the material"
                       # < 45%   -> "Low confidence — please upload a clearer image"
}


def get_confidence_label(confidence: float) -> dict:
    """Return a human-readable confidence label + message for a given probability (0-1)."""
    if confidence >= CONFIDENCE_THRESHOLDS["high"]:
        return {"level": "high", "message": "High confidence prediction"}
    elif confidence >= CONFIDENCE_THRESHOLDS["medium"]:
        return {"level": "medium", "message": "Moderate confidence — consider verifying the material"}
    else:
        return {"level": "low", "message": "Low confidence — please upload a clearer image"}


def get_waste_info(class_name: str) -> dict:
    """Look up the metadata dictionary for a predicted class name."""
    return WASTE_INFO.get(class_name, WASTE_INFO["trash"])
