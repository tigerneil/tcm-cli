"""
Meridian tools: meridian/channel tropism analysis, acupoint reference.
"""

import logging
from tcm.tools import registry

logger = logging.getLogger("tcm.tools.meridians")

MERIDIAN_DB = {
    "肝经": {"pinyin": "Gān Jīng", "english": "Liver Meridian", "element": "木 (Wood)", "yin_yang": "Yin", "paired": "胆经"},
    "心经": {"pinyin": "Xīn Jīng", "english": "Heart Meridian", "element": "火 (Fire)", "yin_yang": "Yin", "paired": "小肠经"},
    "脾经": {"pinyin": "Pí Jīng", "english": "Spleen Meridian", "element": "土 (Earth)", "yin_yang": "Yin", "paired": "胃经"},
    "肺经": {"pinyin": "Fèi Jīng", "english": "Lung Meridian", "element": "金 (Metal)", "yin_yang": "Yin", "paired": "大肠经"},
    "肾经": {"pinyin": "Shèn Jīng", "english": "Kidney Meridian", "element": "水 (Water)", "yin_yang": "Yin", "paired": "膀胱经"},
    "胆经": {"pinyin": "Dǎn Jīng", "english": "Gallbladder Meridian", "element": "木 (Wood)", "yin_yang": "Yang", "paired": "肝经"},
    "小肠经": {"pinyin": "Xiǎo Cháng Jīng", "english": "Small Intestine Meridian", "element": "火 (Fire)", "yin_yang": "Yang", "paired": "心经"},
    "胃经": {"pinyin": "Wèi Jīng", "english": "Stomach Meridian", "element": "土 (Earth)", "yin_yang": "Yang", "paired": "脾经"},
    "大肠经": {"pinyin": "Dà Cháng Jīng", "english": "Large Intestine Meridian", "element": "金 (Metal)", "yin_yang": "Yang", "paired": "肺经"},
    "膀胱经": {"pinyin": "Páng Guāng Jīng", "english": "Bladder Meridian", "element": "水 (Water)", "yin_yang": "Yang", "paired": "肾经"},
    "心包经": {"pinyin": "Xīn Bāo Jīng", "english": "Pericardium Meridian", "element": "火 (Fire)", "yin_yang": "Yin", "paired": "三焦经"},
    "三焦经": {"pinyin": "Sān Jiāo Jīng", "english": "Triple Burner Meridian", "element": "火 (Fire)", "yin_yang": "Yang", "paired": "心包经"},
}


@registry.register(
    name="meridians.lookup",
    description="Look up meridian information by name. Returns Five Element association, Yin/Yang, and paired meridian.",
    category="meridians",
    parameters={"meridian": "Meridian name (Chinese or English)"},
    usage_guide="When analyzing meridian tropism for herbs or treatment planning.",
)
def meridians_lookup(meridian: str) -> dict:
    """Look up meridian information."""
    query = meridian.lower().strip()
    for name, data in MERIDIAN_DB.items():
        if query in name.lower() or query in data["english"].lower():
            return {"status": "found", "meridian": {"name": name, **data}}
    return {"status": "not_found", "message": f"Meridian '{meridian}' not found."}


@registry.register(
    name="meridians.list_all",
    description="List all 12 primary meridians with their Five Element associations.",
    category="meridians",
    parameters={},
    usage_guide="When providing an overview of the meridian system.",
)
def meridians_list_all() -> dict:
    """List all meridians."""
    meridians = []
    for name, data in MERIDIAN_DB.items():
        meridians.append({"name": name, **data})
    return {"status": "found", "count": len(meridians), "meridians": meridians}


@registry.register(
    name="meridians.by_element",
    description="Find meridians associated with a specific Five Element (五行): Wood, Fire, Earth, Metal, Water.",
    category="meridians",
    parameters={"element": "Five Element name (Chinese or English)"},
    usage_guide="When analyzing Five Element relationships in treatment.",
)
def meridians_by_element(element: str) -> dict:
    """Find meridians by Five Element."""
    query = element.lower().strip()
    matches = []
    for name, data in MERIDIAN_DB.items():
        if query in data["element"].lower():
            matches.append({"name": name, **data})
    if matches:
        return {"status": "found", "element": element, "meridians": matches}
    return {"status": "not_found", "message": f"No meridians found for element '{element}'."}
