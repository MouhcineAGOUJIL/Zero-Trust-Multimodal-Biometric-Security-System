#!/usr/bin/env python3
"""
Update README.md to embed images as base64 instead of using file paths.
This ensures images display correctly on GitHub and in any viewer.
"""

import base64
import os
from pathlib import Path

def encode_image(image_path):
    """Encode image file to base64 string"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def update_readme_with_embedded_images():
    project_root = Path(__file__).parent
    readme_path = project_root / 'README.md'
    screens_dir = project_root / 'Screens'
    
    print("Reading README.md...")
    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()
    
    # Define images to embed
    images_to_embed = {
        'Arch.png': 'System Architecture Diagram',
        'HomeScreen.png': 'Home Screen Interface',
        'IrisGranted.png': 'Iris Recognition - Access Granted',
        'IrisDenied.png': 'Iris Recognition - Access Denied',
        'HandGranted.png': 'Palm Recognition - Access Granted',
        'HandDenied.png': 'Palm Recognition - Access Denied',
        'MultiGranted.png': 'Multimodal - Access Granted',
        'MultiDenied.png': 'Multimodal - Access Denied',
        'ZeroTrustGranted.png': 'Zero Trust - Access Granted',
        'ZeroTrustDenied.png': 'Zero Trust - Access Denied',
        'Attacks.png': 'Attack Simulation Interface'
    }
    
    print("\nEncoding images to base64...")
    embedded_images = {}
    
    for image_file, description in images_to_embed.items():
        image_path = screens_dir / image_file
        if image_path.exists():
            print(f"  ✓ Encoding {image_file}...")
            base64_data = encode_image(image_path)
            embedded_images[image_file] = {
                'data': base64_data,
                'description': description
            }
        else:
            print(f"  ✗ Warning: {image_file} not found, skipping")
    
    print("\nUpdating README with embedded images...")
    
    # Replace image references with base64 embedded versions
    replacements = {
        '![System Architecture](Screens/Arch.png)': 
            f'![System Architecture](data:image/png;base64,{embedded_images.get("Arch.png", {}).get("data", "")})' if 'Arch.png' in embedded_images else '![System Architecture](Screens/Arch.png)',
        
        '![Home](Screens/HomeScreen.png)':
            f'![Home](data:image/png;base64,{embedded_images.get("HomeScreen.png", {}).get("data", "")})' if 'HomeScreen.png' in embedded_images else '![Home](Screens/HomeScreen.png)',
        
        '![Iris Granted](Screens/IrisGranted.png)':
            f'![Iris Granted](data:image/png;base64,{embedded_images.get("IrisGranted.png", {}).get("data", "")})' if 'IrisGranted.png' in embedded_images else '![Iris Granted](Screens/IrisGranted.png)',
        
        '![Iris Denied](Screens/IrisDenied.png)':
            f'![Iris Denied](data:image/png;base64,{embedded_images.get("IrisDenied.png", {}).get("data", "")})' if 'IrisDenied.png' in embedded_images else '![Iris Denied](Screens/IrisDenied.png)',
        
        '![Palm Granted](Screens/HandGranted.png)':
            f'![Palm Granted](data:image/png;base64,{embedded_images.get("HandGranted.png", {}).get("data", "")})' if 'HandGranted.png' in embedded_images else '![Palm Granted](Screens/HandGranted.png)',
        
        '![Palm Denied](Screens/HandDenied.png)':
            f'![Palm Denied](data:image/png;base64,{embedded_images.get("HandDenied.png", {}).get("data", "")})' if 'HandDenied.png' in embedded_images else '![Palm Denied](Screens/HandDenied.png)',
        
        '![Multi Granted](Screens/MultiGranted.png)':
            f'![Multi Granted](data:image/png;base64,{embedded_images.get("MultiGranted.png", {}).get("data", "")})' if 'MultiGranted.png' in embedded_images else '![Multi Granted](Screens/MultiGranted.png)',
        
        '![Multi Denied](Screens/MultiDenied.png)':
            f'![Multi Denied](data:image/png;base64,{embedded_images.get("MultiDenied.png", {}).get("data", "")})' if 'MultiDenied.png' in embedded_images else '![Multi Denied](Screens/MultiDenied.png)',
        
        '![ZT Granted](Screens/ZeroTrustGranted.png)':
            f'![ZT Granted](data:image/png;base64,{embedded_images.get("ZeroTrustGranted.png", {}).get("data", "")})' if 'ZeroTrustGranted.png' in embedded_images else '![ZT Granted](Screens/ZeroTrustGranted.png)',
        
        '![ZT Denied](Screens/ZeroTrustDenied.png)':
            f'![ZT Denied](data:image/png;base64,{embedded_images.get("ZeroTrustDenied.png", {}).get("data", "")})' if 'ZeroTrustDenied.png' in embedded_images else '![ZT Denied](Screens/ZeroTrustDenied.png)',
        
        '![Attacks](Screens/Attacks.png)':
            f'![Attacks](data:image/png;base64,{embedded_images.get("Attacks.png", {}).get("data", "")})' if 'Attacks.png' in embedded_images else '![Attacks](Screens/Attacks.png)',
    }
    
    # Apply replacements
    updated_content = readme_content
    for old, new in replacements.items():
        if old in updated_content:
            updated_content = updated_content.replace(old, new)
            print(f"  ✓ Replaced: {old[:50]}...")
    
    # Create backup
    backup_path = readme_path.parent / 'README_backup.md'
    print(f"\nCreating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Write updated README
    print(f"Writing updated README: {readme_path}")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("\n" + "="*80)
    print("SUCCESS! README updated with embedded images")
    print("="*80)
    print(f"\nImages embedded: {len(embedded_images)}")
    print("Images are now base64-encoded and will display anywhere!")
    print("\nNote: README file size increased due to embedded images.")
    print("Original backed up to: README_backup.md")
    print("="*80)
    
    return len(embedded_images)

if __name__ == '__main__':
    try:
        count = update_readme_with_embedded_images()
        print(f"\n✅ Successfully embedded {count} images in README.md")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
