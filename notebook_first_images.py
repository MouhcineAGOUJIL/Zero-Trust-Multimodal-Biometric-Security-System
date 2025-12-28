#!/usr/bin/env python3
"""
Split markdown cells to keep text but insert Python code for images.
"""

import json
import sys
import base64

def split_cells_for_images():
    notebook_path = '/home/red/Documents/S5/Biom Sec/Project/Zero_Trust_Biometric_System.ipynb'
    
    # Restore from backup first
    backup_path = notebook_path.replace('.ipynb', '_backup_first_images.ipynb')
    print(f"Restoring from backup: {backup_path}")
    with open(backup_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    # Read and encode the images
    screens_dir = '/home/red/Documents/S5/Biom Sec/Project/Screens'
    
    print("Encoding images...")
    with open(f"{screens_dir}/Arch.png", 'rb') as f:
        arch_img = base64.b64encode(f.read()).decode('utf-8')
    print("  ✓ Encoded Arch.png")
    
    with open(f"{screens_dir}/HomeScreen.png", 'rb') as f:
        home_img = base64.b64encode(f.read()).decode('utf-8')
    print("  ✓ Encoded HomeScreen.png")
    
    # Find and process cells
    cells_to_process = []
    
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'markdown':
            source = ''.join(cell.get('source', ''))
            if '![System Architecture](Screens/Arch.png)' in source:
                cells_to_process.append(('arch', i, source))
                print(f"Found Architecture image at cell {i}")
            elif '![Project Dashboard](Screens/HomeScreen.png)' in source:
                cells_to_process.append(('dashboard', i, source))
                print(f"Found Dashboard image at cell {i}")
    
    # Process cells in reverse order to maintain indices
    insertions = 0
    for section_type, idx, original_source in sorted(cells_to_process, reverse=True):
        adjusted_idx = idx + insertions
        
        if section_type == 'arch':
            # Remove image line from markdown
            new_markdown = original_source.replace('![System Architecture](Screens/Arch.png)\n', '').replace('![System Architecture](Screens/Arch.png)', '')
            
            # Update markdown cell
            nb['cells'][adjusted_idx]['source'] = new_markdown.splitlines(True)
            
            # Create Python code cell for image
            code_cell = {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Display System Architecture\n",
                    "from IPython.display import Image, display\n",
                    "import base64\n",
                    "\n",
                    f"arch_img = '{arch_img}'\n",
                    "display(Image(data=base64.b64decode(arch_img)))\n"
                ]
            }
            
            # Insert code cell right after markdown
            nb['cells'].insert(adjusted_idx + 1, code_cell)
            insertions += 1
            print(f"  ✓ Split Architecture section at cell {adjusted_idx}")
            
        elif section_type == 'dashboard':
            # Remove image line from markdown
            new_markdown = original_source.replace('![Project Dashboard](Screens/HomeScreen.png)\n', '').replace('![Project Dashboard](Screens/HomeScreen.png)', '')
            
            # Update markdown cell
            nb['cells'][adjusted_idx]['source'] = new_markdown.splitlines(True)
            
            # Create Python code cell for image
            code_cell = {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Display Dashboard Screenshot\n",
                    "from IPython.display import Image, display\n",
                    "import base64\n",
                    "\n",
                    f"home_img = '{home_img}'\n",
                    "display(Image(data=base64.b64decode(home_img)))\n"
                ]
            }
            
            # Insert code cell right after markdown
            nb['cells'].insert(adjusted_idx + 1, code_cell)
            insertions += 1
            print(f"  ✓ Split Dashboard section at cell {adjusted_idx}")
    
    # Save updated notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    print(f"\n✓ Saved updated notebook: {notebook_path}")
    print("\n" + "="*80)
    print("SUCCESS! Markdown cells split with Python image loading")
    print("="*80)
    print("\nChanges made:")
    print("  • Kept all markdown text intact")
    print("  • Removed image markdown syntax")
    print("  • Inserted Python code cells for images")
    print("  • Images load via base64 (no file paths)")
    print(f"  • Total insertions: {insertions}")
    print("\nRefresh Jupyter and run all cells!")
    print("="*80)
    
    return insertions

if __name__ == '__main__':
    try:
        count = split_cells_for_images()
        print(f"\n✅ Successfully processed {count} images!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
