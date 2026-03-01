
import os
import re
import shutil

# ----------------------------------------
# CONFIG – update this if your templates are elsewhere
# ----------------------------------------
TEMPLATE_ROOT = "members/templates"
TEMPLATE_ROOT_2 = "tips/templates"

# ----------------------------------------
# HTML entity patterns to replace
# This handles normal AND double-escaped entities
# ----------------------------------------
REPLACEMENTS = {
    "&lt;": "<",
    "&gt;": ">",
    "&amp;lt;": "<",
    "&amp;gt;": ">",
    "&amp;": "&",
    "&#60;": "<",
    "&#62;": ">",
    "&#x3C;": "<",
    "&#x3E;": ">",
}

# ----------------------------------------
# Fixer Function
# ----------------------------------------
def repair_file(path):
    print(f"Processing: {path}")

    # Backup original file
    backup = path + ".bak"
    if not os.path.exists(backup):
        shutil.copy2(path, backup)

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    new_content = content

    # Simple replacements
    for bad, good in REPLACEMENTS.items():
        new_content = new_content.replace(bad, good)

    # Catch ANY weird angle bracket encodings
    new_content = re.sub(r"&[a-zA-Z0-9#]+;", lambda m: REPLACEMENTS.get(m.group(0), m.group(0)), new_content)

    # Save repaired file
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"   ✔ Repaired and saved. Backup: {backup}")

# ----------------------------------------
# Directory Walker
# ----------------------------------------
def repair_templates_dir(root):
    if not os.path.exists(root):
        print(f"Directory not found: {root}")
        return

    for subdir, _, files in os.walk(root):
        for f in files:
            if f.endswith(".html"):
                repair_file(os.path.join(subdir, f))

# ----------------------------------------
# Run the repair on both template dirs
# ----------------------------------------
if __name__ == "__main__":
    print("🛠 Starting template repair...")
    repair_templates_dir(TEMPLATE_ROOT)
    repair_templates_dir(TEMPLATE_ROOT_2)
    print("✨ Repair complete.")
