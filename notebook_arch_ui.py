#!/usr/bin/env python3
"""
Add System Architecture and UI Dashboard section to notebook with embedded images.
"""

import json
import sys
import base64

def add_architecture_ui_section():
    notebook_path = '/home/red/Documents/S5/Biom Sec/Project/Zero_Trust_Biometric_System.ipynb'
    
    print(f"Reading notebook: {notebook_path}")
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    # Read and encode all UI screenshots
    screens_dir = '/home/red/Documents/S5/Biom Sec/Project/Screens'
    
    print("Encoding images...")
    images = {}
    
    image_files = [
        'Arch.png',
        'HomeScreen.png',
        'IrisGranted.png',
        'IrisDenied.png',
        'HandGranted.png',
        'HandDenied.png',
        'MultiGranted.png',
        'MultiDenied.png',
        'ZeroTrustGranted.png',
        'ZeroTrustDenied.png',
        'Attacks.png'
    ]
    
    for img_file in image_files:
        img_path = f"{screens_dir}/{img_file}"
        try:
            with open(img_path, 'rb') as f:
                images[img_file] = base64.b64encode(f.read()).decode('utf-8')
            print(f"  ✓ Encoded {img_file}")
        except Exception as e:
            print(f"  ✗ Failed to encode {img_file}: {e}")
    
    # Create the comprehensive Architecture & UI cell
    arch_ui_cell_code = f'''
# =============================================================================
# SYSTEM ARCHITECTURE & UI DASHBOARD
# =============================================================================

from IPython.display import HTML, display
import base64

print("\\n" + "="*80)
print("SYSTEM ARCHITECTURE & UI DASHBOARD")
print("="*80)

# Images embedded as base64
images = {{
    'Arch': "{images.get('Arch.png', '')}",
    'HomeScreen': "{images.get('HomeScreen.png', '')}",
    'IrisGranted': "{images.get('IrisGranted.png', '')}",
    'IrisDenied': "{images.get('IrisDenied.png', '')}",
    'HandGranted': "{images.get('HandGranted.png', '')}",
    'HandDenied': "{images.get('HandDenied.png', '')}",
    'MultiGranted': "{images.get('MultiGranted.png', '')}",
    'MultiDenied': "{images.get('MultiDenied.png', '')}",
    'ZeroTrustGranted': "{images.get('ZeroTrustGranted.png', '')}",
    'ZeroTrustDenied': "{images.get('ZeroTrustDenied.png', '')}",
    'Attacks': "{images.get('Attacks.png', '')}"
}}

html_content = f"""
<style>
    .arch-container {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: white;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .arch-header {{
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        padding: 25px;
        border-radius: 8px;
        margin-bottom: 30px;
        text-align: center;
    }}
    .arch-section {{
        margin-bottom: 40px;
        padding: 25px;
        background: #f8f9fa;
        border-left: 4px solid #3b82f6;
        border-radius: 4px;
    }}
    .arch-image {{
        text-align: center;
        margin: 30px 0;
        padding: 20px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    .arch-image img {{
        max-width: 100%;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    .arch-image-title {{
        font-size: 18px;
        font-weight: bold;
        color: #1e40af;
        margin-top: 15px;
        margin-bottom: 5px;
    }}
    .arch-image-desc {{
        font-size: 14px;
        color: #666;
        font-style: italic;
    }}
    .ui-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: 30px;
        margin: 30px 0;
    }}
    .ui-card {{
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }}
    .ui-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }}
    .ui-card img {{
        width: 100%;
        display: block;
    }}
    .ui-card-title {{
        padding: 15px;
        background: #f8f9fa;
        text-align: center;
        font-weight: bold;
        color: #1e40af;
    }}
    .status-granted {{
        color: #22c55e;
    }}
    .status-denied {{
        color: #ef4444;
    }}
</style>

<div class="arch-container">
    <div class="arch-header">
        <h1 style="margin: 0; font-size: 2.2rem;">🏗️ System Architecture & UI Dashboard</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1rem;">
            Complete System Design and User Interface Showcase
        </p>
    </div>

    <div class="arch-section">
        <h2>📐 System Architecture</h2>
        <p>
            The system follows a layered architecture with clear separation of concerns:
        </p>
        <ul>
            <li><strong>Client Layer:</strong> React-based responsive web interface</li>
            <li><strong>Application Layer:</strong> FastAPI REST API with authentication endpoints</li>
            <li><strong>Business Logic Layer:</strong> Biometric services (Iris, Palm) and Zero Trust engine</li>
            <li><strong>Data Layer:</strong> SQLite database with 3 tables (users, templates, logs)</li>
        </ul>
        
        <div class="arch-image">
            <img src="data:image/png;base64,{{images['Arch']}}" alt="System Architecture">
            <div class="arch-image-title">Complete System Architecture</div>
            <div class="arch-image-desc">
                Multi-tier architecture showing client, application, business logic, and data layers with 
                service interactions and data flow
            </div>
        </div>
    </div>

    <div class="arch-section">
        <h2>🖥️ User Interface Dashboard</h2>
        
        <h3>Home Screen</h3>
        <div class="arch-image">
            <img src="data:image/png;base64,{{images['HomeScreen']}}" alt="Home Screen">
            <div class="arch-image-title">Landing Page</div>
            <div class="arch-image-desc">
                Modern glassmorphism design with navigation to all system features
            </div>
        </div>

        <h3>Iris Recognition Interface</h3>
        <div class="ui-grid">
            <div class="ui-card">
                <img src="data:image/png;base64,{{images['IrisGranted']}}" alt="Iris Granted">
                <div class="ui-card-title status-granted">✓ Iris - Access Granted</div>
            </div>
            <div class="ui-card">
                <img src="data:image/png;base64,{{images['IrisDenied']}}" alt="Iris Denied">
                <div class="ui-card-title status-denied">✗ Iris - Access Denied</div>
            </div>
        </div>

        <h3>Palm Recognition Interface</h3>
        <div class="ui-grid">
            <div class="ui-card">
                <img src="data:image/png;base64,{{images['HandGranted']}}" alt="Palm Granted">
                <div class="ui-card-title status-granted">✓ Palm - Access Granted</div>
            </div>
            <div class="ui-card">
                <img src="data:image/png;base64,{{images['HandDenied']}}" alt="Palm Denied">
                <div class="ui-card-title status-denied">✗ Palm - Access Denied</div>
            </div>
        </div>

        <h3>Multimodal Recognition Interface</h3>
        <div class="ui-grid">
            <div class="ui-card">
                <img src="data:image/png;base64,{{images['MultiGranted']}}" alt="Multi Granted">
                <div class="ui-card-title status-granted">✓ Multimodal - Access Granted</div>
            </div>
            <div class="ui-card">
                <img src="data:image/png;base64,{{images['MultiDenied']}}" alt="Multi Denied">
                <div class="ui-card-title status-denied">✗ Multimodal - Access Denied</div>
            </div>
        </div>

        <h3>Zero Trust Authentication Interface</h3>
        <div class="ui-grid">
            <div class="ui-card">
                <img src="data:image/png;base64,{{images['ZeroTrustGranted']}}" alt="ZT Granted">
                <div class="ui-card-title status-granted">✓ Zero Trust - Access Granted</div>
            </div>
            <div class="ui-card">
                <img src="data:image/png;base64,{{images['ZeroTrustDenied']}}" alt="ZT Denied">
                <div class="ui-card-title status-denied">✗ Zero Trust - Access Denied</div>
            </div>
        </div>

        <h3>Attack Simulation Interface</h3>
        <div class="arch-image">
            <img src="data:image/png;base64,{{images['Attacks']}}" alt="Attack Simulation">
            <div class="arch-image-title">Security Testing Dashboard</div>
            <div class="arch-image-desc">
                Real-time attack simulation with terminal-style logging and comprehensive statistics
            </div>
        </div>
    </div>

    <div class="arch-section" style="background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border-left-color: #22c55e;">
        <h3 style="color: #166534; margin-top: 0;">🎨 UI/UX Highlights</h3>
        <ul style="margin: 10px 0;">
            <li><strong>Modern Design:</strong> Glassmorphism effects with smooth animations</li>
            <li><strong>Responsive Layout:</strong> Works seamlessly on desktop, tablet, and mobile</li>
            <li><strong>Real-time Feedback:</strong> Instant visual feedback for all operations</li>
            <li><strong>Professional Aesthetics:</strong> Dark theme with vibrant accent colors</li>
            <li><strong>Accessibility:</strong> Clear status indicators (green/red) for quick recognition</li>
            <li><strong>Security First:</strong> All sensitive operations require explicit user action</li>
        </ul>
    </div>
</div>
"""

display(HTML(html_content))

print("\\n" + "="*80)
print("✓ System Architecture & UI Dashboard Loaded")
print("="*80)
print("\\nImages Displayed:")
print("  • System Architecture Diagram")
print("  • Home Screen")
print("  • Iris Recognition UI (Granted & Denied)")
print("  • Palm Recognition UI (Granted & Denied)")
print("  • Multimodal UI (Granted & Denied)")
print("  • Zero Trust UI (Granted & Denied)")
print("  • Attack Simulation Dashboard")
print("="*80)
'''

    # Find where to insert (before Conclusion)
    insert_index = None
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'markdown':
            source = ''.join(cell.get('source', ''))
            if 'Conclusion' in source and 'Part' not in source:
                insert_index = i
                print(f"Found insertion point before conclusion (cell {i})")
                break
    
    # Last resort: append before last 2 cells
    if insert_index is None:
        insert_index = len(nb['cells']) - 2
        print(f"Using position before last cells (index {insert_index})")
    
    # Create markdown intro cell
    intro_md = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "---\n",
            "\n",
            "# System Architecture & UI Dashboard\n",
            "\n",
            "Visual presentation of the complete system architecture and user interface designs with all authentication scenarios.\n"
        ]
    }
    
    # Create the code cell
    code_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": arch_ui_cell_code.splitlines(True)
    }
    
    # Insert both cells
    nb['cells'].insert(insert_index, intro_md)
    nb['cells'].insert(insert_index + 1, code_cell)
    
    print(f"\n✓ Inserted 2 new cells at index {insert_index}")
    
    # Create backup
    backup_path = notebook_path.replace('.ipynb', '_backup_arch_ui.ipynb')
    print(f"✓ Creating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    # Save updated notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    print(f"✓ Saved updated notebook: {notebook_path}")
    print("\n" + "="*80)
    print("SUCCESS! Architecture & UI section added to notebook")
    print("="*80)
    print("\nThe section includes:")
    print("  • System Architecture diagram (embedded)")
    print("  • All UI screenshots (11 total):")
    print("    - Home Screen")
    print("    - Iris Recognition (Granted/Denied)")
    print("    - Palm Recognition (Granted/Denied)")
    print("    - Multimodal (Granted/Denied)")
    print("    - Zero Trust (Granted/Denied)")
    print("    - Attack Simulation")
    print("  • All images loaded via Python (base64)")
    print("  • No file path dependencies!")
    print("\nRefresh Jupyter and run the new cell!")
    print("="*80)
    
    return len(images)

if __name__ == '__main__':
    sys.exit(add_architecture_ui_section())
