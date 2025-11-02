#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Processing Module for Portfolio
Generates responsive image versions (thumbnails, medium, web-full)
"""

from PIL import Image
from PIL.ExifTags import TAGS
import os
from pathlib import Path
from typing import Dict, List, Tuple

def exif_transpose(img):
    """Rotate image according to EXIF orientation"""
    try:
        exif = img._getexif()
        if exif is not None:
            for tag, value in exif.items():
                if TAGS.get(tag) == 'Orientation':
                    if value == 3:
                        img = img.rotate(180, expand=True)
                    elif value == 6:
                        img = img.rotate(270, expand=True)
                    elif value == 8:
                        img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # No EXIF data or orientation tag
        pass
    return img

def ensure_rgb(img):
    """Convert RGBA/LA/P images to RGB for JPEG compatibility"""
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if 'A' in img.mode:
            background.paste(img, mask=img.split()[-1])
        else:
            background.paste(img)
        return background
    elif img.mode != 'RGB':
        return img.convert('RGB')
    return img

def generate_responsive_versions(source_path: Path, output_dir: Path, project_slug: str, image_index: int) -> Dict[str, Path]:
    """
    Generate thumbnail, medium, and web-full versions of an image.
    
    Args:
        source_path: Path to original high-res image
        output_dir: Base directory for output (e.g., assets/images/ProjectName/)
        project_slug: Project slug (e.g., 'ludomancer')
        image_index: Index of image in project (1-based)
    
    Returns:
        Dict with keys: 'thumbnail', 'medium', 'full', 'original_filename'
        Each value is the relative path from en/projects/ perspective
    """
    
    # Special handling for GIFs - just copy without conversion
    if source_path.suffix.lower() == '.gif':
        import shutil
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy GIF to output directory
        filename = f"{project_slug}-{image_index}{source_path.suffix}"
        output_path = output_dir / filename
        shutil.copy2(source_path, output_path)
        
        # Return same path for all versions (no responsive versions for GIFs)
        rel_path = f"../../assets/images/{output_dir.name}/{filename}"
        
        # Try to get GIF dimensions
        try:
            with Image.open(source_path) as img:
                width, height = img.size
        except:
            width, height = 0, 0
        
        print(f"      ✓ GIF copied  {width:4d}×{height:4d}px → {filename} (animation preserved)")
        
        return {
            'thumbnail': {'path': rel_path, 'width': width, 'height': height},
            'medium': {'path': rel_path, 'width': width, 'height': height},
            'full': {'path': rel_path, 'width': width, 'height': height},
            'original_filename': source_path.name
        }
    
    # Load and prepare image (non-GIF)
    img = Image.open(source_path)
    img = exif_transpose(img)
    img = ensure_rgb(img)
    
    # Version settings: folder_name -> (max_dimension, quality)
    versions = {
        'thumbnail': {'max_size': 400, 'quality': 75},
        'medium': {'max_size': 1200, 'quality': 80},
        'full': {'max_size': 2000, 'quality': 85},
    }
    
    results = {}
    
    for version_type, settings in versions.items():
        # Create subdirectory
        version_dir = output_dir / version_type
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Resize maintaining aspect ratio
        img_copy = img.copy()
        img_copy.thumbnail((settings['max_size'], settings['max_size']), Image.Resampling.LANCZOS)
        
        # New filename format: projectname-1-thumbnail.jpg
        filename = f"{project_slug}-{image_index}-{version_type}.jpg"
        output_path = version_dir / filename
        img_copy.save(output_path, 'JPEG', quality=settings['quality'], optimize=True)
        
        # Store relative path (from en/projects/ perspective)
        rel_path = f"../../assets/images/{output_dir.name}/{version_type}/{filename}"
        results[version_type] = {
            'path': rel_path,
            'width': img_copy.size[0],
            'height': img_copy.size[1]
        }
        
        print(f"      ✓ {version_type:12s} {img_copy.size[0]:4d}×{img_copy.size[1]:4d}px → {filename}")
    
    # Store original filename for reference
    results['original_filename'] = source_path.name
    
    return results

def process_project_images(images: List[str], project_slug: str, source_dir: Path, output_base_dir: Path) -> List[Dict]:
    """
    Process all images for a project - generate responsive versions.
    
    Args:
        images: List of image filenames (from logseq assets)
        project_slug: Project slug for folder naming (lowercase, e.g., 'ludomancer')
        source_dir: Source directory (logseq-data/assets/)
        output_base_dir: Base output directory (assets/images/)
    
    Returns:
        List of dicts with responsive image data:
        [{
            'original': 'filename.jpg',
            'thumbnail': {'path': '...', 'width': 400, 'height': 300},
            'medium': {...},
            'full': {...}
        }, ...]
    """
    project_images_dir = output_base_dir / project_slug.capitalize()
    project_images_dir.mkdir(parents=True, exist_ok=True)
    
    processed_images = []
    
    for img_index, img_filename in enumerate(images, start=1):
        source = source_dir / img_filename
        
        if not source.exists():
            print(f"    ⚠️  Image not found: {source}")
            # Fallback: return original path
            processed_images.append({
                'original': img_filename,
                'full': {'path': f"../../logseq-data/assets/{img_filename}", 'width': 0, 'height': 0}
            })
            continue
        
        print(f"    Processing image {img_index}/{len(images)}: {img_filename}")
        
        # Check if versions already exist (skip regeneration for speed)
        # For GIFs, check for .gif extension; for others check .jpg
        if source.suffix.lower() == '.gif':
            full_version_path = project_images_dir / f"{project_slug}-{img_index}.gif"
        else:
            full_version_path = project_images_dir / 'full' / f"{project_slug}-{img_index}-full.jpg"
        
        if full_version_path.exists():
            print(f"      ↻ Versions exist, skipping...")
            # Return existing paths without regenerating
            if source.suffix.lower() == '.gif':
                # For GIF, all versions point to same file
                gif_path = f"../../assets/images/{project_slug.capitalize()}/{project_slug}-{img_index}.gif"
                versions = {
                    'thumbnail': {'path': gif_path, 'width': 0, 'height': 0},
                    'medium': {'path': gif_path, 'width': 0, 'height': 0},
                    'full': {'path': gif_path, 'width': 0, 'height': 0},
                    'original_filename': img_filename
                }
            else:
                # For JPG, return responsive versions
                versions = {
                    'thumbnail': {
                        'path': f"../../assets/images/{project_slug.capitalize()}/thumbnail/{project_slug}-{img_index}-thumbnail.jpg",
                        'width': 400,
                        'height': 400
                    },
                    'medium': {
                        'path': f"../../assets/images/{project_slug.capitalize()}/medium/{project_slug}-{img_index}-medium.jpg",
                        'width': 1200,
                        'height': 1200
                    },
                    'full': {
                        'path': f"../../assets/images/{project_slug.capitalize()}/full/{project_slug}-{img_index}-full.jpg",
                        'width': 2000,
                        'height': 2000
                    },
                    'original_filename': img_filename
                }
        else:
            # Generate new versions
            versions = generate_responsive_versions(source, project_images_dir, project_slug, img_index)
        
        processed_images.append({
            'original': img_filename,
            'thumbnail': versions['thumbnail'],
            'medium': versions['medium'],
            'full': versions['full']
        })
    
    return processed_images

def generate_picture_element(image_data: Dict, alt_text: str, title_attr: str = "", 
                             loading: str = "lazy", onclick: str = "") -> str:
    """
    Generate responsive <picture> element with srcset.
    
    Args:
        image_data: Dict with 'thumbnail', 'medium', 'full' keys
        alt_text: Alt text for accessibility
        title_attr: Optional title attribute (tooltip)
        loading: Loading strategy ('lazy', 'eager')
        onclick: Optional onclick handler
    
    Returns:
        HTML string for <picture> element
    """
    
    thumb = image_data['thumbnail']
    medium = image_data['medium']
    full = image_data['full']
    
    title_html = f' title="{title_attr}"' if title_attr else ''
    onclick_html = f' onclick="{onclick}"' if onclick else ''
    cursor_style = ' cursor: pointer;' if onclick else ''
    
    return f'''<picture>
  <source media="(max-width: 600px)" srcset="{thumb['path']}">
  <source media="(max-width: 1200px)" srcset="{medium['path']}">
  <img src="{full['path']}" alt="{alt_text}"{title_html} loading="{loading}"{onclick_html} style="width: 100%; height: auto; display: block;{cursor_style}">
</picture>'''

def generate_srcset_img(image_data: Dict, alt_text: str, title_attr: str = "",
                        loading: str = "lazy", onclick: str = "") -> str:
    """
    Generate <img> with srcset attribute (simpler alternative to <picture>).
    
    Args:
        image_data: Dict with 'thumbnail', 'medium', 'full' keys
        alt_text: Alt text for accessibility
        title_attr: Optional title attribute (tooltip)
        loading: Loading strategy ('lazy', 'eager')
        onclick: Optional onclick handler
    
    Returns:
        HTML string for <img> element with srcset
    """
    
    thumb = image_data['thumbnail']
    medium = image_data['medium']
    full = image_data['full']
    
    title_html = f' title="{title_attr}"' if title_attr else ''
    onclick_html = f' onclick="{onclick}"' if onclick else ''
    cursor_style = 'cursor: pointer;' if onclick else ''
    
    srcset = f"{thumb['path']} {thumb['width']}w, {medium['path']} {medium['width']}w, {full['path']} {full['width']}w"
    sizes = "(max-width: 600px) 400px, (max-width: 1200px) 1200px, 2000px"
    
    return f'<img src="{medium["path"]}" srcset="{srcset}" sizes="{sizes}" alt="{alt_text}"{title_html} loading="{loading}"{onclick_html} style="width: 100%; height: auto; display: block; {cursor_style}">'

