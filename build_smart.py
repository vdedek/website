#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Portfolio Build Script
Uses ludomancer.html as template and fills it with data from markdown files
+ Taxonomy system for project tagging and related projects
"""

import re
import sys
import shutil
import argparse
import json
import urllib.parse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Import image processor
try:
    from image_processor import generate_responsive_versions
    IMAGE_PROCESSOR_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSOR_AVAILABLE = False
    print("⚠️  Warning: image_processor.py not found. Images will be copied without optimization.")

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Paths
LOGSEQ_DIR = Path('logseq-data/pages')
LOGSEQ_ASSETS = Path('logseq-data/assets')
EN_DIR = Path('en')
CZ_DIR = Path('cz')
PROJECTS_DIR = EN_DIR / 'projects'
IMAGES_DIR = Path('assets/images')
TEMPLATE_FILE = PROJECTS_DIR / 'template.html'
TAXONOMY_DIR = Path('taxonomy')
MASTER_TAGS_FILE = TAXONOMY_DIR / 'master_tags.json'
TAG_DESCRIPTIONS_FILE = TAXONOMY_DIR / 'tag_descriptions.json'
PENDING_TAGS_FILE = TAXONOMY_DIR / 'new_tags_pending.json'
TRANSLATIONS_FILE = Path('translations.json')

# ============================================================================
# LOCALIZATION FUNCTIONS
# ============================================================================

def load_translations() -> Dict:
    """Load translations from translations.json"""
    if not TRANSLATIONS_FILE.exists():
        print(f"⚠️  Warning: translations.json not found. Using English defaults.")
        return {"en": {}, "cz": {}}
    return load_json(TRANSLATIONS_FILE)

def detect_language(md_file: Path) -> str:
    """
    Detect language from markdown filename.
    Files with ___CZ suffix are Czech, others are English.
    
    Examples:
        Changeling.md → 'en'
        Changeling___CZ.md → 'cz'
    """
    if '___CZ' in md_file.stem or '___cz' in md_file.stem:
        return 'cz'
    return 'en'

def get_output_dirs(language: str) -> Tuple[Path, Path]:
    """
    Get output directories based on language.
    Returns: (language_dir, projects_dir)
    """
    if language == 'cz':
        lang_dir = CZ_DIR
        projects_dir = lang_dir / 'projects'
    else:
        lang_dir = EN_DIR
        projects_dir = lang_dir / 'projects'
    
    return lang_dir, projects_dir

def translate(key: str, language: str, translations: Dict, category: str = 'common') -> str:
    """
    Get translation for a key in specified language.
    Falls back to English if translation not found.
    
    Args:
        key: Translation key (e.g., 'documentation', 'year')
        language: Language code ('en' or 'cz')
        translations: Translations dict loaded from JSON
        category: Category in translations dict ('common', 'project_types', 'metadata')
    
    Returns:
        Translated string
    """
    try:
        return translations[language][category][key]
    except KeyError:
        # Fallback to English
        try:
            return translations['en'][category][key]
        except KeyError:
            # Last fallback: return key itself
            return key.replace('_', ' ').title()

def translate_project_type(type_string: str, language: str, translations: Dict) -> str:
    """
    Translate project type string (can be comma-separated list).
    Examples:
        'installation, audio' → 'Instalace, Audio' (CZ)
        'performance' → 'Performance' (CZ)
    
    Args:
        type_string: Type string from metadata (e.g., 'installation, audio')
        language: Language code ('en' or 'cz')
        translations: Translations dict
    
    Returns:
        Translated type string
    """
    if not type_string or language == 'en':
        # Return as-is for English or empty
        return type_string.title() if type_string else ''
    
    # Split by comma and translate each part
    types = [t.strip().lower() for t in type_string.split(',')]
    translated_parts = []
    
    for type_part in types:
        # Try to get translation
        translated = translate(type_part, language, translations, category='project_types')
        translated_parts.append(translated)
    
    return ', '.join(translated_parts)

# ============================================================================
# TAXONOMY SYSTEM FUNCTIONS
# ============================================================================

def load_json(filepath: Path) -> Dict:
    """Load JSON file, return empty dict if not found"""
    if not filepath.exists():
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath: Path, data: Dict):
    """Save dictionary to JSON file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_tags_from_metadata(metadata: Dict) -> List[str]:
    """Extract #tags from metadata['tag'] field"""
    if 'tag' not in metadata:
        return []
    
    tags_str = metadata['tag']
    # Extract all #tag patterns (including & for D&D)
    tags = re.findall(r'#([\w/\-&]+)', tags_str)
    return [f"#{tag}" for tag in tags]

def calculate_tag_idf_weights(all_projects: List[Tuple[Path, Dict]]) -> Dict[str, float]:
    """
    Calculate IDF (Inverse Document Frequency) weights for all tags.
    Rare tags get higher weights, common tags get lower weights.
    
    Returns: dict mapping tag -> IDF weight
    """
    import math
    
    tag_counts = {}
    total_projects = len(all_projects)
    
    # Count how many projects use each tag
    for md_file, metadata in all_projects:
        project_tags = extract_tags_from_metadata(metadata)
        for tag in project_tags:
            tag_clean = tag.lstrip('#')
            tag_counts[tag_clean] = tag_counts.get(tag_clean, 0) + 1
    
    # Calculate IDF weights
    idf_weights = {}
    for tag, count in tag_counts.items():
        # IDF formula: log(total_docs / docs_with_term)
        # Add 1 to smooth and avoid log(1) = 0
        idf_weights[tag] = math.log((total_projects + 1) / (count + 1)) + 1
    
    return idf_weights


def calculate_tag_similarity(tags1: List[str], tags2: List[str], master_tags: Dict, 
                             idf_weights: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate similarity between two tag sets (0.0-1.0)
    
    Args:
        tags1, tags2: Lists of tags to compare
        master_tags: Master taxonomy dict with hierarchies and clusters
        idf_weights: Optional IDF weights dict. If provided, rare tags have higher importance.
    
    Returns:
        Similarity score 0.0-1.0
    """
    if not tags1 or not tags2:
        return 0.0
    
    # Remove # prefix for comparison
    set1 = set(tag.lstrip('#') for tag in tags1)
    set2 = set(tag.lstrip('#') for tag in tags2)
    
    def get_weight(tag: str) -> float:
        """Get IDF weight for tag, or 1.0 if no IDF weights provided"""
        if idf_weights is None:
            return 1.0
        return idf_weights.get(tag, 1.0)
    
    # Exact matches with IDF weighting
    exact_matches = set1 & set2
    score = sum(get_weight(tag) for tag in exact_matches)
    
    # Hierarchical matches (e.g., 'audio' matches 'audio/spatial')
    hierarchies = master_tags.get('tag_relationships', {}).get('hierarchical', {})
    for parent, children in hierarchies.items():
        parent_clean = parent.lstrip('#')
        children_clean = [c.lstrip('#') for c in children]
        
        # Check if one has parent and other has child
        has_parent_1 = parent_clean in set1
        has_parent_2 = parent_clean in set2
        has_child_1 = any(c in set1 for c in children_clean)
        has_child_2 = any(c in set2 for c in children_clean)
        
        if (has_parent_1 and has_child_2) or (has_child_1 and has_parent_2):
            # Use average weight of parent and matching child
            matching_child = next((c for c in children_clean if c in (set1 | set2)), parent_clean)
            weight = (get_weight(parent_clean) + get_weight(matching_child)) / 2
            score += 0.7 * weight  # Hierarchical match worth 0.7x
    
    # Cluster matches (related concepts)
    clusters = master_tags.get('tag_relationships', {}).get('related_clusters', {})
    for cluster_name, cluster_tags in clusters.items():
        cluster_clean = set(t.lstrip('#') for t in cluster_tags)
        cluster_match_1 = set1 & cluster_clean
        cluster_match_2 = set2 & cluster_clean
        
        if cluster_match_1 and cluster_match_2 and not (cluster_match_1 & cluster_match_2):
            # Both projects in same cluster but different tags
            common_cluster_tags = cluster_match_1 & cluster_match_2
            cluster_weight = sum(get_weight(tag) for tag in common_cluster_tags)
            score += 0.3 * cluster_weight
    
    # Normalize by maximum possible score from set1
    # (How similar is set2 to the "ideal match" of set1?)
    max_possible = sum(get_weight(tag) for tag in set1)
    if max_possible == 0:
        return 0.0
    
    return min(score / max_possible, 1.0)

def find_related_projects(project_metadata: Dict, all_projects: List[Tuple[Path, Dict]], master_tags: Dict, max_results: int = 4) -> List[Dict]:
    """Find related projects based on tag similarity with IDF weighting"""
    
    project_tags = extract_tags_from_metadata(project_metadata)
    if not project_tags:
        return []
    
    # Calculate IDF weights for all tags across all projects
    idf_weights = calculate_tag_idf_weights(all_projects)
    
    # Calculate similarity for each project
    similarities = []
    for md_file, other_metadata in all_projects:
        # Skip self
        if other_metadata.get('name-en') == project_metadata.get('name-en'):
            continue
        
        other_tags = extract_tags_from_metadata(other_metadata)
        if not other_tags:
            continue
        
        similarity = calculate_tag_similarity(project_tags, other_tags, master_tags, idf_weights)
        
        if similarity > 0.2:  # Minimum threshold
            matching_tags = list(set(project_tags) & set(other_tags))
            similarities.append({
                'name': other_metadata.get('name-en', md_file.stem),
                'slug': slugify(other_metadata.get('name-en', md_file.stem)),
                'year': other_metadata.get('year', 'TBD'),
                'similarity': similarity,
                'matching_tags': matching_tags
            })
    
    # Sort by similarity and return top N
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    return similarities[:max_results]

def get_all_project_metadata() -> List[Tuple[Path, Dict]]:
    """Load metadata from all project markdown files"""
    projects = []
    
    for md_file in LOGSEQ_DIR.glob('*.md'):
        # Skip template and non-project files
        if md_file.stem.startswith('_') or md_file.stem in ['contents', 'Contact', 'CV', 'Projects']:
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            metadata = parse_metadata(content)
            
            # Only include projects with year (actual projects)
            if 'year' in metadata:
                projects.append((md_file, metadata))
        except Exception as e:
            print(f"Warning: Could not parse {md_file.name}: {e}")
            continue
    
    return projects

def suggest_tags_llm(project_content: str, project_metadata: Dict, master_tags: Dict, tag_descriptions: Dict) -> Optional[Dict]:
    """
    Call LLM to suggest tags for a project.
    Returns: {
        'selected_tags': [...],
        'reasoning': '...',
        'confidence': 0.85,
        'new_tags_suggested': [...]
    }
    
    NOTE: This is a placeholder. Implement with your preferred LLM API:
    - OpenAI API
    - Anthropic Claude API  
    - Local model (Ollama, etc.)
    """
    print("\n⚠️  LLM tagging not yet implemented!")
    print("    To implement, edit suggest_tags_llm() function in build_smart.py")
    print("    Use taxonomy/llm_tagging_prompt_example.md as reference")
    print()
    
    # Return None to indicate LLM not available
    return None

def prompt_user_for_tags(suggested_tags: List[str], project_name: str) -> Tuple[List[str], bool]:
    """Show suggested tags and let user approve/edit"""
    print(f"\n📋 Suggested tags for: {project_name}")
    print(f"   {', '.join(suggested_tags)}")
    print()
    
    response = input("✓ Accept these tags? [Y/n/e(dit)]: ").strip().lower()
    
    if response == 'n':
        return [], False
    elif response == 'e':
        print("\nEnter tags (comma-separated, with #):")
        custom_tags = input("> ").strip()
        tags = [t.strip() for t in custom_tags.split(',') if t.strip()]
        return tags, True
    else:
        return suggested_tags, True

# ============================================================================
# ORIGINAL FUNCTIONS
# ============================================================================

def convert_markdown_formatting(text):
    """Convert markdown formatting to HTML (links, italic, bold, highlighted)"""
    if not text:
        return text
    # Convert [text](url) to <a href="url">text</a>
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    # Convert **text** to <strong>text</strong> (bold) - must be before *text*
    text = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', text)
    # Convert *text* to <em>text</em> (italic)
    text = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', text)
    # Convert ==text== to <span class="highlighted">text</span> (highlighted)
    text = re.sub(r'==([^=]+)==', r'<span class="highlighted">\1</span>', text)
    return text

def parse_exhibitions_list(content):
    """
    Parse exhibitions:: with sub-properties from markdown.
    Returns list of dicts with exhibition info.
    
    Format:
    - exhibitions::
        - Sep-Nov 2023: Solo Exhibition, Gallery Name
          start:: [[date]]
          end:: [[date]]
          place:: Name
          town:: City
          country:: Country
          venue-type:: type
          link:: [text](url)
    """
    exhibitions = []
    lines = content.split('\n')
    in_exhibitions = False
    current_exhibition = None
    
    for i, line in enumerate(lines):
        # Start of exhibitions list
        if 'exhibitions::' in line.lower():
            in_exhibitions = True
            continue
        
        if in_exhibitions:
            stripped = line.lstrip()
            indent_level = len(line) - len(stripped)
            
            # Stop if we hit a non-indented bullet or new section
            if stripped.startswith('- #') or (stripped.startswith('-') and indent_level == 0 and not stripped.startswith('- \t')):
                break
            
            # Main exhibition item (tab-indented bullet with title)
            if stripped.startswith('- ') and indent_level == 1:  # Single tab
                # Save previous exhibition
                if current_exhibition:
                    exhibitions.append(current_exhibition)
                
                # Start new exhibition
                title = stripped[2:].strip()
                current_exhibition = {
                    'title': title,
                    'properties': {}
                }
            
            # Sub-properties (double-tab indented)
            elif '::' in stripped and indent_level >= 2 and current_exhibition:
                # Parse property
                match = re.match(r'^([a-z-]+)::\s*(.+)$', stripped.strip())
                if match:
                    key = match.group(1)
                    value = match.group(2).strip()
                    # Clean up wiki links [[...]] and markdown links
                    value = re.sub(r'\[\[([^\]]+)\]\]', r'\1', value)
                    current_exhibition['properties'][key] = value
    
    # Don't forget last exhibition
    if current_exhibition:
        exhibitions.append(current_exhibition)
    
    return exhibitions


def parse_metadata(content):
    """Parse metadata from markdown file (key:: value format)"""
    metadata = {}
    lines = content.split('\n')
    
    for line in lines:
        if '::' in line and not line.strip().startswith('-'):
            match = re.match(r'^([a-z-]+)::\s*(.+)$', line.strip())
            if match:
                key = match.group(1)
                value = match.group(2).strip()
                # Clean up wiki links [[...]]
                value = re.sub(r'\[\[([^\]]+)\]\]', r'\1', value)
                metadata[key] = value
    
    # Parse exhibitions list separately
    exhibitions = parse_exhibitions_list(content)
    if exhibitions:
        metadata['exhibitions_list'] = exhibitions
    
    return metadata

def extract_content_sections(content):
    """Extract text sections from markdown - preserves order"""
    sections = {
        'content': [],  # Simple list in order: [{'type': 'header'/'paragraph'/'quote', ...}]
        'images': [],
        'image_captions': {},  # {image_filename: {'caption': '...', 'link': '...'}}
        'image_group_captions': {}  # {image_index: 'caption text'} - captions before image groups
    }
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip metadata (both top-level and indented id:: lines)
        if ('::' in line and not line.startswith('-')) or line.strip().startswith('id::'):
            i += 1
            continue
        
        # Extract images with optional captions and links
        # Use non-greedy match (.+?) to handle filenames with parentheses
        img_match = re.search(r'!\[([^\]]*)\]\(\.\.\/assets\/(.+?\.[a-zA-Z0-9]+)\)', line)
        if img_match:
            alt_text = img_match.group(1)  # This will be used as tooltip
            img_filename = img_match.group(2)
            sections['images'].append(img_filename)
            
            # Check for caption/link after image (on same line)
            rest_of_line = line[img_match.end():].strip()
            caption_data = {}
            
            # Store alt text as tooltip
            if alt_text and alt_text not in ['-', '']:
                caption_data['tooltip'] = alt_text
            
            # Check for wikilink [[Page Name]] on same line
            wikilink_match = re.search(r'\[\[([^\]]+)\]\]', rest_of_line)
            if wikilink_match:
                caption_data['link'] = wikilink_match.group(1)
            
            # Check for text caption on same line
            text_caption = re.sub(r'\[\[[^\]]+\]\]', '', rest_of_line).strip()
            if text_caption and text_caption not in ['-', '']:
                caption_data['caption'] = text_caption
            
            # Also check NEXT line if indented (caption on separate line)
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.startswith('  ') and not next_line.strip().startswith('id::') and not next_line.strip().startswith('!['):
                    indented_caption = next_line.strip()
                    # Check for wikilink
                    wikilink_match_next = re.search(r'\[\[([^\]]+)\]\]', indented_caption)
                    if wikilink_match_next:
                        caption_data['link'] = wikilink_match_next.group(1)
                    # Get text (remove wikilink)
                    indented_text = re.sub(r'\[\[[^\]]+\]\]', '', indented_caption).strip()
                    if indented_text and indented_text not in ['-', '']:
                        caption_data['caption'] = indented_text
                    i += 1  # Skip next line since we processed it
            
            if caption_data:
                sections['image_captions'][img_filename] = caption_data
            
            i += 1
            continue
        
        # UNIVERSAL HEADER PARSING: Any line starting with "- ####"
        if line.startswith('- ####'):
            # Extract section title (everything after ####, remove trailing : if present)
            title_match = re.search(r'####\s*(.+?)(:?)$', line)
            if not title_match:
                i += 1
                continue
                
            section_title = title_match.group(1).strip()
            section_data = {
                'type': 'header',
                'title': section_title,
                'collapsed': False,
                'collapsed_type': None,  # None, 'full', or 'read-more'
                'content': []
            }
            
            i += 1  # Move to next line
            
            # Check for collapsed directive (Logseq native)
            if i < len(lines) and 'collapsed::' in lines[i]:
                section_data['collapsed'] = True
                section_data['collapsed_type'] = 'full'  # Whole section collapsed
                i += 1
            
            # Check for show-first-paragraph directive (our custom)
            if i < len(lines) and 'show-first-paragraph::' in lines[i]:
                section_data['collapsed'] = True
                section_data['collapsed_type'] = 'read-more'  # First paragraph visible
                i += 1
            
            # Skip block reference if present
            if i < len(lines) and '((' in lines[i]:
                i += 1
            
            # Read section content (indented lines)
            while i < len(lines) and lines[i].startswith('\t'):
                content_line = lines[i].strip()
                if content_line.startswith('id::'):
                    i += 1
                    continue
                
                # Check if this is a quote (- > text)
                is_quote = False
                if content_line.startswith('- >'):
                    is_quote = True
                    content_line = content_line[3:].strip()  # Remove "- >"
                elif content_line.startswith('- '):
                    content_line = content_line[2:].strip()  # Remove "- "
                
                # Convert markdown formatting
                content_line = convert_markdown_formatting(content_line)
                if content_line:
                    section_data['content'].append({
                        'text': content_line,
                        'is_quote': is_quote
                    })
                i += 1
            
            if section_data['content']:
                sections['content'].append(section_data)
            continue
        
        # Extract quotes (lines with > or inside tabs)
        # Formats: "> text", "- > text", or old format "- *"text"*"
        if line.startswith('>') or line.startswith('- >') or (line.startswith('-') and '*"' in line and not '„' in line):
            quote_text = line.strip('- \t>*"').strip()
            # Apply markdown formatting to quotes (for italic etc)
            quote_text = convert_markdown_formatting(quote_text)
            if quote_text and len(quote_text) > 20:
                sections['content'].append({
                    'type': 'quote',
                    'text': quote_text
                })
            i += 1
            continue
        
        # Empty bullet line - add spacer for vertical spacing
        if line == '-':
            sections['content'].append({
                'type': 'spacer'
            })
            i += 1
            continue
        
        # Extract regular body paragraphs and image group captions
        if line.startswith('- ') and not line.startswith('- #') and not line.startswith('- !'):
            para = line[2:].strip()
            
            # Skip exhibition list items (they're handled separately by parse_exhibitions_list)
            # They typically look like: "Sep-Nov 2023: Solo Exhibition, ..." or "Prosinec 2024-Únor 2025: Skupinová výstava"
            # Check for date patterns (English or Czech months) followed by colon
            if re.match(r'^[A-ZÚ][a-zřčšžýáíéůú]+-[A-ZÚ][a-zřčšžýáíéůú]+ \d{4}:', para) or \
               re.match(r'^[A-ZÚ][a-zřčšžýáíéůú]+ \d{4}:', para) or \
               ('Exhibition' in para and ':' in para[:30]) or \
               ('výstava' in para.lower() and ':' in para[:50]) or \
               ('Výstava' in para and ':' in para[:50]):
                i += 1
                continue
            
            # Check if next line(s) lead to an image - this is an image group caption
            next_line_idx = i + 1
            is_image_group_caption = False
            if next_line_idx < len(lines):
                # Skip id:: lines and whitespace to find if there's an image following
                check_idx = next_line_idx
                while check_idx < len(lines):
                    check_line = lines[check_idx].strip()
                    if not check_line or check_line.startswith('id::'):
                        # Skip empty lines and id:: lines
                        check_idx += 1
                        continue
                    # Check if this line is an image (with or without bullet)
                    if '![' in check_line:
                        is_image_group_caption = True
                    break
            
            if is_image_group_caption:
                # This is a caption for a group of images
                # Store it with the index of the NEXT image (which will follow)
                para_html = convert_markdown_formatting(para)
                next_image_index = len(sections['images'])  # Index of next image to be added
                sections['image_group_captions'][next_image_index] = para_html
                i += 1
                continue
            
            # Continue reading if next lines are indented (part of same paragraph)
            j = i + 1
            while j < len(lines) and lines[j].startswith('  ') and not lines[j].strip().startswith('!['):
                # Skip id:: lines
                if lines[j].strip().startswith('id::'):
                    j += 1
                    continue
                para += ' ' + lines[j].strip()
                j += 1
            
            if para and len(para) > 30 and not para.startswith('####'):
                para_html = convert_markdown_formatting(para)
                sections['content'].append({
                    'type': 'paragraph',
                    'text': para_html
                })
            i = j
            continue
        
        i += 1
    
    return sections

def slugify(text):
    """
    Convert text to URL-friendly slug without diacritics.
    Examples:
        'Měňavec' → 'menavec'
        'Přízraky' → 'prizraky'
        'Changeling' → 'changeling'
    """
    # Czech diacritics mapping
    diacritics_map = {
        'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e', 'í': 'i',
        'ň': 'n', 'ó': 'o', 'ř': 'r', 'š': 's', 'ť': 't', 'ú': 'u',
        'ů': 'u', 'ý': 'y', 'ž': 'z',
        'Á': 'a', 'Č': 'c', 'Ď': 'd', 'É': 'e', 'Ě': 'e', 'Í': 'i',
        'Ň': 'n', 'Ó': 'o', 'Ř': 'r', 'Š': 's', 'Ť': 't', 'Ú': 'u',
        'Ů': 'u', 'Ý': 'y', 'Ž': 'z'
    }
    
    # Replace diacritics
    text_no_diacritics = ''.join(diacritics_map.get(c, c) for c in text)
    
    # Convert to lowercase and remove special characters
    slug = re.sub(r'[^\w\s-]', '', text_no_diacritics.lower())
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug

def copy_images_to_project_folder(images, project_slug_en):
    """
    Process images from logseq-data/assets to assets/images/ProjectName/
    Generates responsive versions (thumbnail, medium, full) if PIL is available.
    
    IMPORTANT: Always uses English project slug for folder name to avoid duplication
    between language versions (e.g., both 'Changeling' and 'Měňavec' use same folder 'Changeling/')
    
    Args:
        images: List of image filenames
        project_slug_en: English project slug (used for folder name)
    
    Returns: List of dicts with 'medium' and 'full' paths for each image
    """
    project_images_dir = IMAGES_DIR / project_slug_en.capitalize()
    project_images_dir.mkdir(parents=True, exist_ok=True)
    
    processed_images = []
    
    for idx, img_filename in enumerate(images, start=1):
        source = LOGSEQ_ASSETS / img_filename
        if not source.exists():
            print(f"    Warning: Image not found: {source}")
            # Fallback - return simple path
            processed_images.append({
                'medium': f"../../logseq-data/assets/{img_filename}",
                'full': f"../../logseq-data/assets/{img_filename}"
            })
            continue
        
        if IMAGE_PROCESSOR_AVAILABLE:
            # Generate responsive versions
            try:
                print(f"    Processing: {img_filename}")
                versions = generate_responsive_versions(
                    source_path=source,
                    output_dir=project_images_dir,
                    project_slug=project_slug_en,
                    image_index=idx
                )
                # Return medium for display, full for lightbox
                processed_images.append({
                    'medium': versions['medium']['path'],
                    'full': versions['full']['path'],
                    'thumbnail': versions['thumbnail']['path']
                })
            except Exception as e:
                print(f"    ⚠️  Error processing image: {e}")
                # Fallback: copy original
                dest = project_images_dir / img_filename
                shutil.copy2(source, dest)
                rel_path = f"../../assets/images/{project_slug_en.capitalize()}/{img_filename}"
                processed_images.append({
                    'medium': rel_path,
                    'full': rel_path
                })
        else:
            # Fallback: just copy without processing
            dest = project_images_dir / img_filename
            shutil.copy2(source, dest)
            rel_path = f"../../assets/images/{project_slug_en.capitalize()}/{img_filename}"
            processed_images.append({
                'medium': rel_path,
                'full': rel_path
            })
            print(f"    Copied: {img_filename}")
    
    return processed_images

def generate_meta_description(metadata, sections, max_length=160):
    """
    Generate SEO meta description from project content.
    Prefers: about text > first paragraph > description metadata
    """
    # Try to find about text from sections
    for section in sections.get('content', []):
        if section['type'] == 'header' and 'about' in section.get('title', '').lower():
            if section.get('content'):
                # Get first paragraph, strip HTML tags
                first_para = section['content'][0].get('text', '')
                clean_text = re.sub(r'<[^>]+>', '', first_para)
                if len(clean_text) > max_length:
                    return clean_text[:max_length-3] + '...'
                return clean_text
        elif section['type'] == 'paragraph':
            # Use first regular paragraph
            clean_text = re.sub(r'<[^>]+>', '', section.get('text', ''))
            if len(clean_text) > max_length:
                return clean_text[:max_length-3] + '...'
            return clean_text
    
    # Fallback to metadata description
    if 'description' in metadata:
        desc = metadata['description']
        if len(desc) > max_length:
            return desc[:max_length-3] + '...'
        return desc
    
    # Last fallback: type and year
    return f"{metadata.get('type', 'Artwork')} by Viktor Dedek ({metadata.get('year', 'TBD')})"

def generate_structured_data(metadata, sections, project_slug, image_paths):
    """
    Generate JSON-LD structured data for artwork and exhibitions.
    Returns JSON string ready for insertion into <script type="application/ld+json">
    """
    project_name = metadata.get('name-en', project_slug)
    project_url = f"https://viktordedek.com/en/projects/{project_slug}.html"
    
    # Base artwork data
    artwork_data = {
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "name": project_name,
        "creator": {
            "@type": "Person",
            "name": "Viktor Dedek",
            "url": "https://viktordedek.com"
        },
        "dateCreated": str(metadata.get('year', '')),
        "artMedium": metadata.get('type', 'installation'),
        "url": project_url
    }
    
    # Add image if available
    if image_paths:
        hero_img = image_paths[0].get('full', image_paths[0].get('medium', ''))
        if hero_img.startswith('../../'):
            hero_img = 'https://viktordedek.com/' + hero_img[6:]  # Remove ../../
        artwork_data["image"] = hero_img
    
    # Add description
    if 'description' in metadata:
        artwork_data["description"] = metadata['description']
    
    # Add materials
    if 'materials' in metadata:
        artwork_data["material"] = metadata['materials']
    
    # Add exhibition events
    exhibitions = metadata.get('exhibitions_list', [])
    if exhibitions:
        events = []
        for exh in exhibitions:
            props = exh.get('properties', {})
            event = {
                "@type": "ExhibitionEvent",
                "name": exh['title']
            }
            
            if 'place' in props:
                event["location"] = {
                    "@type": "Place",
                    "name": props['place']
                }
                if 'town' in props:
                    event["location"]["address"] = {
                        "@type": "PostalAddress",
                        "addressLocality": props['town']
                    }
                    if 'country' in props:
                        event["location"]["address"]["addressCountry"] = props['country']
            
            if 'start' in props:
                event["startDate"] = props['start']
            if 'end' in props:
                event["endDate"] = props['end']
            
            events.append(event)
        
        if events:
            artwork_data["workPresented"] = events
    
    return json.dumps(artwork_data, indent=2, ensure_ascii=False)

def generate_project_from_template(md_file, template_content, project_slug, language='en', translations=None):
    """
    Generate HTML using template with language support.
    
    Args:
        md_file: Path to markdown file
        template_content: HTML template content
        project_slug: URL-friendly project slug
        language: Language code ('en' or 'cz')
        translations: Translations dict (loaded from JSON)
    """
    if translations is None:
        translations = load_translations()
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata = parse_metadata(content)
    sections = extract_content_sections(content)
    
    # Skip if no year
    if 'year' not in metadata:
        return None, None
    
    # Get project info
    project_name = metadata.get('name-en', md_file.stem)
    project_type = metadata.get('type', 'exhibition')
    
    # Always use English name for image folder (to avoid duplication between language versions)
    project_slug_en = slugify(metadata.get('name-en', md_file.stem))
    
    # Copy images to project folder and get new paths
    print(f"  Copying images...")
    image_paths = copy_images_to_project_folder(sections['images'], project_slug_en) if sections['images'] else []
    
    # Format type nicely
    if 'solo' in project_type:
        type_display = 'Solo Exhibition'
    elif 'group' in project_type:
        type_display = 'Group Exhibition'
    else:
        type_display = project_type.title()
    
    # Build metadata chips (general work info only - NO exhibition details)
    metadata_chips = []
    
    # Helper function for translation
    def t(key, category='common'):
        return translate(key, language, translations, category)
    
    # Type - translate the type string
    type_display_translated = translate_project_type(project_type, language, translations)
    metadata_chips.append(f'<span class="metadata-chip">{t("type")}: {type_display_translated}</span>')
    
    # Year
    if 'year' in metadata:
        metadata_chips.append(f'<span class="metadata-chip">{t("year")}: {metadata["year"]}</span>')
    
    # Materials
    if 'materials' in metadata:
        metadata_chips.append(f'<span class="metadata-chip">{t("materials")}: {metadata["materials"]}</span>')
    elif 'description' in metadata:
        metadata_chips.append(f'<span class="metadata-chip">{t("materials")}: {metadata["description"]}</span>')
    
    # Duration
    if 'duration' in metadata:
        metadata_chips.append(f'<span class="metadata-chip">{t("duration")}: {metadata["duration"]}</span>')
    
    # Audio button (if audio-url-cz or audio-url-en exists)
    if 'audio-url-cz' in metadata:
        metadata_chips.append(f'<a href="{metadata["audio-url-cz"]}" target="_blank" class="metadata-chip metadata-chip-link">{t("listen_to_audio_cz")} ↗</a>')
    if 'audio-url-en' in metadata:
        metadata_chips.append(f'<a href="{metadata["audio-url-en"]}" target="_blank" class="metadata-chip metadata-chip-link">{t("listen_to_audio_en")} ↗</a>')
    
    # Video button (if video exists)
    if 'video' in metadata and metadata['video']:
        metadata_chips.append(f'<a href="{metadata["video"]}" target="_blank" class="metadata-chip metadata-chip-link">{t("watch_video")} ↗</a>')
    
    # Combine all chips into one row
    metadata_html = f'''    <tr>
      <td class="content-cell">
        <div class="metadata-chips-container">
          {' '.join(metadata_chips)}
        </div>
      </td>
    </tr>
'''
    
    # EXHIBITIONS LIST - Generate as buttons with links (all in one cell)
    exhibitions_html = ''
    if 'exhibitions_list' in metadata and metadata['exhibitions_list']:
        exhibitions_html = f'''    <tr>
      <td class="content-cell">
        <h2 class="section-header">{t("exhibition_history")}</h2>
      </td>
    </tr>
    <tr>
      <td class="content-cell">
'''
        # Generate all buttons in one cell
        for exhibition in metadata['exhibitions_list']:
            title = exhibition['title']
            props = exhibition.get('properties', {})
            
            # Build exhibition info text
            info_parts = []
            if 'place' in props:
                info_parts.append(props['place'])
            if 'town' in props:
                info_parts.append(props['town'])
            if 'country' in props:
                info_parts.append(props['country'])
            
            info_text = f"{title}"
            if info_parts:
                info_text += f"<br>{', '.join(info_parts)}"
            
            # Check for link
            link_url = None
            if 'link' in props:
                # Extract URL from markdown link [text](url)
                link_match = re.search(r'\[([^\]]+)\]\(([^\)]+)\)', props['link'])
                if link_match:
                    link_url = link_match.group(2)
                else:
                    link_url = props['link']
            
            # Generate button (no <tr>, just the element)
            if link_url:
                exhibitions_html += f'''        <a href="{link_url}" target="_blank" class="metadata-chip metadata-chip-link" style="display: block; text-align: left; padding: 12px 16px; margin: 8px 0;">
          {info_text} ↗
        </a>
'''
            else:
                exhibitions_html += f'''        <div class="metadata-chip" style="display: block; padding: 12px 16px; margin: 8px 0;">
          {info_text}
        </div>
'''
        
        # Close the cell
        exhibitions_html += '''      </td>
    </tr>
'''
    
    # CONTENT GENERATOR - Simple, preserves .md order
    content_html = ''
    last_was_paragraph = False
    
    for idx, item in enumerate(sections['content']):
        # Check if next item is spacer - if so, add extra padding to current item
        has_spacer_after = (idx + 1 < len(sections['content']) and 
                           sections['content'][idx + 1]['type'] == 'spacer')
        
        # Skip spacer items - they just signal to add padding to previous item
        if item['type'] == 'spacer':
            continue
        
        if item['type'] == 'header':
            # #### Section with optional collapsed
            section = item
            author = metadata.get('curated-by', '')
            
            # Generate header section HTML
            if section['collapsed']:
                if section['collapsed_type'] == 'read-more' and len(section['content']) > 1:
                    # First paragraph visible, rest collapsible
                    first_item = section['content'][0]
                    first_para_html = f'<div class="quote">{first_item["text"]}</div>' if first_item['is_quote'] else f'<div class="body-text">{first_item["text"]}</div>'
                    
                    # Build rest of paragraphs with proper separation
                    rest_html = ''
                    for item in section['content'][1:]:
                        if item['is_quote']:
                            rest_html += f'<div class="quote">{item["text"]}</div>'
                        else:
                            rest_html += f'<div class="body-text">{item["text"]}</div>'
                    
                    # Regular text style with read more tab at bottom
                    cell_class = "content-cell read-more-cell" + (" spacer-after" if has_spacer_after else "")
                    content_html += f'''
    <!-- {section['title']} (Read More) -->
    <tr>
      <td class="content-cell">
        <h2 class="section-header">{section['title']}</h2>
      </td>
    </tr>
    <tr>
      <td class="{cell_class}">
        {first_para_html}
        <details class="read-more-section">
          <summary class="read-more-tab">
            <svg class="read-more-borders" viewBox="0 0 100 25" preserveAspectRatio="none">
              <line x1="12" y1="0" x2="88" y2="0" stroke="white" stroke-width="2" />
              <line x1="12" y1="0" x2="0" y2="25" stroke="white" stroke-width="2" />
              <line x1="88" y1="0" x2="100" y2="25" stroke="#808080" stroke-width="2" />
            </svg>
            <span class="read-more-text"></span>
          </summary>
          <div class="read-more-hidden">
            {rest_html}
          </div>
        </details>
      </td>
    </tr>
'''
                else:
                    # Fully collapsible
                    full_html = ''
                    for item in section['content']:
                        if item['is_quote']:
                            full_html += f'<div class="quote">{item["text"]}</div>'
                        else:
                            full_html += f'<div class="body-text">{item["text"]}</div>'
                    
                    cell_class = "content-cell" + (" spacer-after" if has_spacer_after else "")
                    content_html += f'''
    <!-- {section['title']} (Fully Collapsible) -->
    <tr>
      <td class="{cell_class}">
        <details class="collapsible-section">
          <summary>{section['title']}</summary>
          {full_html}
        </details>
      </td>
    </tr>
'''
            else:
                # Not collapsed - regular display
                content_html += f'''
    <!-- {section['title']} -->
    <tr>
      <td class="content-cell">
        <h2 class="section-header">{section['title']}</h2>
      </td>
    </tr>
'''
                # Add content lines (check if last item needs spacer)
                for content_idx, content_item in enumerate(section['content']):
                    is_last = content_idx == len(section['content']) - 1
                    cell_class = "content-cell" + (" spacer-after" if is_last and has_spacer_after else "")
                    
                    if content_item['is_quote']:
                        content_html += f'''    <tr>
      <td class="{cell_class}">
        <div class="quote">{content_item["text"]}</div>
      </td>
    </tr>
'''
                    else:
                        # Regular body text
                        content_html += f'''    <tr>
      <td class="{cell_class}">
        <div class="body-text">{content_item["text"]}</div>
      </td>
    </tr>
'''
        
        elif item['type'] == 'paragraph':
            # Regular paragraph
            cell_class = "content-cell" + (" spacer-after" if has_spacer_after else "")
            content_html += f'''    <tr>
      <td class="{cell_class}">
        <div class="body-text">{item['text']}</div>
      </td>
    </tr>
'''
        
        elif item['type'] == 'quote':
            # Quote/excerpt
            cell_class = "content-cell" + (" spacer-after" if has_spacer_after else "")
            content_html += f'''    <tr>
      <td class="{cell_class}">
        <div class="quote">{item['text']}</div>
      </td>
    </tr>
'''
        
    
    # Images/Gallery section
    gallery_html = ''
    gallery_js_images = []
    
    if image_paths:
        # Hero image (first one) - use full size
        hero_img_data = image_paths[0]
        hero_img_path = hero_img_data.get('full', hero_img_data.get('medium', hero_img_data))
        gallery_js_images.append(hero_img_path)
        
        # Documentation images (rest)
        if len(image_paths) > 1:
            gallery_html = f'''
    <!-- Documentation Gallery -->
    <tr>
      <td class="content-cell">
        <h2 class="section-header">{t("documentation")}</h2>
      </td>
    </tr>
'''
            for idx, original_img_filename in enumerate(sections['images'][1:], start=1):
                img_data = image_paths[idx]  # idx because first image is hero (idx 0)
                # Use full for both display and lightbox
                img_path_full = img_data.get('full', img_data.get('medium', img_data))
                gallery_js_images.append(img_path_full)
                
                # Check for group caption BEFORE this image
                if idx in sections['image_group_captions']:
                    group_caption = sections['image_group_captions'][idx]
                    gallery_html += f'''    <tr>
      <td class="content-cell">
        <div class="image-caption">{group_caption} ⤵</div>
      </td>
    </tr>
'''
                
                # Build title attribute for tooltip
                title_attr = ""
                if original_img_filename in sections['image_captions']:
                    caption_data = sections['image_captions'][original_img_filename]
                    if 'tooltip' in caption_data:
                        # Escape quotes for HTML attribute
                        tooltip_escaped = caption_data["tooltip"].replace('"', '&quot;')
                        title_attr = f' title="{tooltip_escaped}"'
                
                gallery_html += f'''    <tr class="project-cell visible">
      <td style="padding: 0 1px 1px 0;">
        <img src="{img_path_full}" alt="{project_name} view {idx}"{title_attr} style="width: 100%; height: auto; display: block; cursor: pointer;" onclick="openGallery({idx})">
'''
                
                # Add caption/link if exists (always with arrow ↪)
                if original_img_filename in sections['image_captions']:
                    caption_data = sections['image_captions'][original_img_filename]
                    caption_parts = []
                    
                    # Always start with arrow
                    if 'caption' in caption_data or 'link' in caption_data:
                        caption_parts.append('↪')
                    
                    # Add caption text (if any)
                    if 'caption' in caption_data:
                        caption_parts.append(f'<span>{caption_data["caption"]}</span>')
                    
                    # Add link (if exists)
                    if 'link' in caption_data:
                        link_slug = slugify(caption_data['link'])
                        caption_parts.append(f'<a href="{link_slug}.html">{caption_data["link"]}</a>')
                    
                    if len(caption_parts) > 1:  # More than just the arrow
                        caption_html = ' '.join(caption_parts)
                        gallery_html += f'''        <div class="image-caption">{caption_html}</div>
'''
                
                gallery_html += '''      </td>
    </tr>
'''
    
    # Related projects (manual or auto-generated)
    related_html = ''
    
    if 'related-projects' in metadata:
        # Manual curation - use specified projects
        related_list = [r.strip() for r in metadata['related-projects'].split(',')]
        related_html = f'''
  <!-- Related Projects Table -->
  <table class="projects-table" cellspacing="1" cellpadding="0">
    <tr>
      <td class="content-cell">
        <h2 class="section-header">{t("related_projects")}</h2>
      </td>
    </tr>
'''
        for rel_name in related_list:
            rel_slug = slugify(rel_name)
            # Try to get year from metadata (if available)
            related_html += f'''    <tr>
      <td class="content-cell">
        <a href="{rel_slug}.html" class="related-project">
          <span class="project-title">{rel_name}</span>
          <span class="project-year">TBD</span>
        </a>
      </td>
    </tr>
'''
        related_html += '  </table>\n'
    else:
        # Auto-similarity - find related projects by tags
        try:
            master_tags = load_json(MASTER_TAGS_FILE)
            all_projects = get_all_project_metadata()
            
            if master_tags and all_projects:
                related_projects = find_related_projects(metadata, all_projects, master_tags, max_results=3)
                
                if related_projects:
                    related_html = f'''
  <!-- Related Projects Table (Auto-generated) -->
  <table class="projects-table" cellspacing="1" cellpadding="0">
    <tr>
      <td class="content-cell">
        <h2 class="section-header">{t("related_projects")}</h2>
      </td>
    </tr>
'''
                    for rel_proj in related_projects:
                        matching_tags_str = ', '.join(rel_proj['matching_tags'][:3]) if rel_proj['matching_tags'] else ''
                        related_html += f'''    <tr>
      <td class="content-cell">
        <a href="{rel_proj['slug']}.html" class="related-project">
          <span class="project-title">{rel_proj['name']}</span>
          <span class="project-year">{rel_proj['year']}</span>
        </a>'''
                        if matching_tags_str:
                            related_html += f'''
        <div class="similarity-tags">{matching_tags_str}</div>'''
                        related_html += '''
      </td>
    </tr>
'''
                    related_html += '  </table>\n'
        except Exception as e:
            print(f"  Warning: Could not generate related projects: {e}")
            # Continue without related projects
    
    # Replace content in template
    html = template_content
    
    # ============================================================================
    # LANGUAGE & LOCALIZATION (Do this FIRST)
    # ============================================================================
    
    # Set HTML lang attribute
    html_lang = translations.get(language, {}).get('html_lang', language)
    html = re.sub(r'<html lang="[^"]*">', f'<html lang="{html_lang}">', html)
    
    # ============================================================================
    # SEO META TAGS & STRUCTURED DATA
    # ============================================================================
    
    # Generate meta description
    meta_description = generate_meta_description(metadata, sections)
    
    # Generate keywords from tags
    project_tags = extract_tags_from_metadata(metadata)
    # Base keywords that appear on all project pages
    base_keywords = ["Viktor Dedek", "contemporary art", "artistic research"]
    
    if project_tags:
        # Use project-specific tags + base keywords
        tag_keywords = [tag.lstrip('#') for tag in project_tags]
        keywords = ', '.join(tag_keywords + base_keywords)
    else:
        # Fallback if no tags
        keywords = ', '.join([project_type, "installation art", "new media"] + base_keywords)
    
    # Get hero image URL for Open Graph
    hero_image_url = "https://viktordedek.com/assets/images/default-preview.jpg"  # Fallback
    if image_paths:
        hero_img = image_paths[0].get('full', image_paths[0].get('medium', ''))
        if hero_img.startswith('../../'):
            hero_image_url = 'https://viktordedek.com/' + hero_img[6:]  # Remove ../../
    
    # Project canonical URL (use correct language folder)
    lang_folder = 'cz' if language == 'cz' else 'en'
    project_url = f"https://viktordedek.com/{lang_folder}/projects/{project_slug}.html"
    
    # Generate structured data (JSON-LD)
    structured_data = generate_structured_data(metadata, sections, project_slug, image_paths)
    
    # Replace SEO placeholders in template
    html = html.replace('PROJECT_DESCRIPTION', meta_description)
    html = html.replace('PROJECT_KEYWORDS', keywords)
    html = html.replace('PROJECT_IMAGE_URL', hero_image_url)
    html = html.replace('PROJECT_URL', project_url)
    html = html.replace('STRUCTURED_DATA_JSON', structured_data)
    
    # Update Open Graph and Twitter titles
    og_title = f'{project_name} - Viktor Dedek'
    html = re.sub(
        r'<meta property="og:title" content="[^"]*">',
        f'<meta property="og:title" content="{og_title}">',
        html
    )
    html = re.sub(
        r'<meta name="twitter:title" content="[^"]*">',
        f'<meta name="twitter:title" content="{og_title}">',
        html
    )
    
    # Replace title
    html = re.sub(r'<title>.*?</title>', f'<title>{project_name} - Viktor Dedek</title>', html)
    
    # Replace h1.project-title text (template already has h1)
    html = re.sub(
        r'(<h1 class="project-title">)▓ [^<]+(</h1>)',
        rf'\1▓ {project_name}\2',
        html
    )
    
    # Replace hero image
    if image_paths:
        hero_img_data = image_paths[0]
        # Use full size for hero image
        hero_img_path = hero_img_data.get('full', hero_img_data.get('medium', hero_img_data))
        
        # Check for tooltip on hero image
        hero_title_attr = ""
        if sections['images'] and sections['images'][0] in sections['image_captions']:
            hero_caption_data = sections['image_captions'][sections['images'][0]]
            if 'tooltip' in hero_caption_data:
                # Escape quotes for HTML attribute
                tooltip_escaped = hero_caption_data["tooltip"].replace('"', '&quot;')
                hero_title_attr = f' title="{tooltip_escaped}"'
        
        html = re.sub(
            r'<img src="[^"]*" alt="[^"]*hero image"[^>]*>',
            f'<img src="{hero_img_path}" alt="{project_name} hero image"{hero_title_attr} style="width: 100%; height: auto; display: block;">',
            html
        )
    
    # Replace metadata section
    # Match from <!-- Project Info --> to the closing </tr> of metadata-chips-container
    metadata_pattern = r'(<!-- Project Info -->\s*\n\s*<tr>.*?metadata-chips-container.*?</tr>)'
    html = re.sub(
        metadata_pattern,
        '<!-- Project Info -->\n    \n' + metadata_html,
        html,
        flags=re.DOTALL
    )
    
    # Replace all content sections
    # First, remove any old exhibitions text block (between metadata and curatorial/documentation)
    # This removes lines like: <tr><td class="content-cell"><div class="body-text">Sep-Nov 2023: ...</div></td></tr>
    html = re.sub(
        r'(metadata-chips-container.*?</tr>\s*</tr>)\s*<tr>\s*<td class="content-cell">\s*<div class="body-text">[^<]*Exhibition[^<]*</div>\s*</td>\s*</tr>\s*',
        r'\1\n',
        html,
        flags=re.DOTALL
    )
    
    # Then replace all content (Curatorial, Body, Audio, Quotes, etc.) with single content_html
    # Match any curatorial comment variant
    content_pattern = r'<!--\s*Curatorial[^>]*-->.*?(?=<!-- Documentation)'
    # Prepend exhibitions_html to content_html
    full_content = exhibitions_html + content_html
    if full_content:
        html = re.sub(content_pattern, full_content + '\n    ', html, flags=re.DOTALL)
    else:
        html = re.sub(content_pattern, '', html, flags=re.DOTALL)
    
    # Replace gallery section
    gallery_pattern = r'(<!-- Documentation Gallery -->.*?</tr>\s*)((?:<tr class="project-cell visible">.*?</tr>\s*)+)'
    if gallery_html:
        html = re.sub(gallery_pattern, gallery_html + '\n  ', html, flags=re.DOTALL)
    
    # Replace gallery images in JavaScript
    if gallery_js_images:
        images_js = ',\n      '.join([f'"{img}"' for img in gallery_js_images])
        html = re.sub(
            r'const galleryImages = \[(.*?)\];',
            f'const galleryImages = [\n      {images_js}\n    ];',
            html,
            flags=re.DOTALL
        )
        
        # Update counter
        html = re.sub(
            r'<span id="galleryCounter">.*?</span>',
            f'<span id="galleryCounter">1 / {len(gallery_js_images)}</span>',
            html
        )
    
    # Replace related projects section
    if related_html:
        related_pattern = r'<!-- Related Projects Table -->.*?</table>'
        html = re.sub(related_pattern, related_html, html, flags=re.DOTALL)
    
    return html, metadata

def map_project_to_filters(metadata: Dict, master_tags: Dict) -> List[str]:
    """
    Map project metadata to work.html filter categories.
    Uses filter_mapping from master_tags.json
    
    Returns: list of filter categories (e.g., ['selected', 'solo', 'audio'])
    """
    filters = []
    filter_mapping = master_tags.get('filter_mapping', {}).get('filters', {})
    
    for filter_name, mapping in filter_mapping.items():
        metadata_key = mapping.get('metadata_key')
        
        if metadata_key == 'featured':
            # Check for featured: yes
            if metadata.get('featured', '').lower() == 'yes':
                filters.append(filter_name)
        
        elif metadata_key == 'type':
            # Check if type OR exhibition-context contains the filter value
            type_value = metadata.get('type', '').lower()
            exhibition_context = metadata.get('exhibition-context', '').lower()
            filter_value = mapping.get('metadata_value', '').lower()
            if filter_value in type_value or filter_value in exhibition_context:
                filters.append(filter_name)
        
        elif metadata_key == 'series':
            # Check series metadata
            series_value = metadata.get('series', '').lower()
            filter_value = mapping.get('metadata_value', '').lower()
            if series_value == filter_value:
                filters.append(filter_name)
        
        elif metadata_key == 'tag':
            # Check if project has this tag
            tag_value = mapping.get('tag_value')
            if tag_value:
                project_tags = extract_tags_from_metadata(metadata)
                if f"#{tag_value}" in project_tags:
                    filters.append(filter_name)
    
    return filters

def get_project_preview_image(project_slug: str) -> Optional[str]:
    """
    Find preview/hero image for a project.
    Prefers thumbnail or medium, falls back to full.
    Returns relative path from en/work.html perspective or None
    """
    # Try various image folders
    image_folders = [
        IMAGES_DIR / project_slug.capitalize(),
        IMAGES_DIR / project_slug,
        IMAGES_DIR / project_slug.title()
    ]
    
    for folder in image_folders:
        if not folder.exists():
            continue
        
        # Prefer thumbnail or medium for preview
        for subfolder in ['thumbnail', 'medium', 'full']:
            subfolder_path = folder / subfolder
            if subfolder_path.exists():
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif']:
                    images = sorted(subfolder_path.glob(ext))
                    if images:
                        # Return relative path from en/work.html
                        return f"../assets/images/{folder.name}/{subfolder}/{images[0].name}"
        
        # Fallback: try direct folder (no subfolder structure)
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif']:
            images = sorted(folder.glob(ext))
            if images:
                return f"../assets/images/{folder.name}/{images[0].name}"
    
    return None

def generate_sitemap():
    """
    Generate sitemap.xml with all pages on the website.
    Includes homepage, main pages, and all project pages.
    Returns True on success, False on failure.
    """
    print("=" * 60)
    print("Generating sitemap.xml")
    print("=" * 60)
    print()
    
    base_url = "https://viktordedek.com"
    sitemap_entries = []
    
    # 1. Homepage (highest priority)
    sitemap_entries.append({
        'loc': f"{base_url}/",
        'priority': '1.0',
        'changefreq': 'monthly'
    })
    
    # 2. Main pages
    main_pages = [
        ('en/work.html', '0.9', 'weekly'),
        ('en/about.html', '0.8', 'monthly'),
        ('en/progress.html', '0.6', 'monthly'),
    ]
    
    for page, priority, freq in main_pages:
        page_path = Path(page)
        if page_path.exists():
            sitemap_entries.append({
                'loc': f"{base_url}/{page}",
                'priority': priority,
                'changefreq': freq
            })
            print(f"  ✓ Added: {page}")
    
    # 3. Project pages (auto-detect all HTML files in en/projects/)
    project_files = list(PROJECTS_DIR.glob('*.html'))
    project_files = [f for f in project_files if f.name != 'template.html']
    
    # Load master tags to determine featured projects
    master_tags = load_json(MASTER_TAGS_FILE)
    
    for html_file in sorted(project_files):
        # Try to find corresponding .md file to check if featured
        html_slug = html_file.stem
        is_featured = False
        
        for potential_md in LOGSEQ_DIR.glob('*.md'):
            if potential_md.stem.startswith('_'):
                continue
            potential_slug = slugify(potential_md.stem)
            if potential_slug == html_slug:
                try:
                    with open(potential_md, 'r', encoding='utf-8') as f:
                        content = f.read()
                    metadata = parse_metadata(content)
                    is_featured = metadata.get('featured', '').lower() == 'yes'
                except:
                    pass
                break
        
        # Featured projects get higher priority
        priority = '0.9' if is_featured else '0.7'
        
        sitemap_entries.append({
            'loc': f"{base_url}/en/projects/{html_file.name}",
            'priority': priority,
            'changefreq': 'monthly'
        })
        print(f"  ✓ Added: en/projects/{html_file.name} (priority: {priority})")
    
    # Generate XML
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for entry in sitemap_entries:
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{entry["loc"]}</loc>\n'
        xml_content += f'    <changefreq>{entry["changefreq"]}</changefreq>\n'
        xml_content += f'    <priority>{entry["priority"]}</priority>\n'
        xml_content += '  </url>\n'
    
    xml_content += '</urlset>\n'
    
    # Write sitemap.xml to root directory
    sitemap_file = Path('sitemap.xml')
    with open(sitemap_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print()
    print("=" * 60)
    print(f"✅ SUCCESS! Generated: {sitemap_file}")
    print("=" * 60)
    print()
    print(f"  Total URLs: {len(sitemap_entries)}")
    print(f"  Homepage: 1")
    print(f"  Main pages: {len(main_pages)}")
    print(f"  Project pages: {len(project_files)}")
    print()
    print("💡 Don't forget to:")
    print("   1. Add sitemap.xml to your robots.txt")
    print("   2. Submit sitemap to Google Search Console")
    print()
    
    return True

def generate_work_html():
    """
    Generate work.html from PUBLISHED project HTML files.
    Only includes projects that have generated HTML in en/projects/.
    Reads metadata from corresponding .md files.
    """
    print("=" * 60)
    print("Generating work.html from published projects")
    print("=" * 60)
    print()
    
    # Load master tags for filter mapping
    master_tags = load_json(MASTER_TAGS_FILE)
    if not master_tags:
        print("❌ ERROR: Master tags not found")
        return False
    
    # Find all HTML files in en/projects/ (these are the published ones)
    html_files = list(PROJECTS_DIR.glob('*.html'))
    
    # Filter out template.html
    html_files = [f for f in html_files if f.name != 'template.html']
    
    if not html_files:
        print("❌ ERROR: No project HTML files found in en/projects/")
        return False
    
    print(f"✓ Found {len(html_files)} published project HTML files")
    print()
    
    # Build project data with filter categories
    projects_data = []
    skipped_projects = []
    
    for html_file in html_files:
        # Try to find corresponding .md file
        # HTML filename might be slugified, so we need to search
        html_slug = html_file.stem
        
        # Try to find matching .md file by comparing slugs
        md_file = None
        for potential_md in LOGSEQ_DIR.glob('*.md'):
            if potential_md.stem.startswith('_'):
                continue
            potential_slug = slugify(potential_md.stem)
            if potential_slug == html_slug:
                md_file = potential_md
                break
        
        if not md_file:
            print(f"  ⚠ Skipped {html_file.name} - no matching .md file found")
            skipped_projects.append(html_file.name)
            continue
        
        # Load metadata from .md file
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            metadata = parse_metadata(content)
        except Exception as e:
            print(f"  ⚠ Skipped {html_file.name} - error reading metadata: {e}")
            skipped_projects.append(html_file.name)
            continue
        
        # Skip if no year (shouldn't happen for published projects, but check anyway)
        if 'year' not in metadata:
            print(f"  ⚠ Skipped {html_file.name} - no year metadata")
            skipped_projects.append(html_file.name)
            continue
        # Decode URL-encoded characters in project name
        project_name_raw = metadata.get('name-en', md_file.stem)
        project_name = urllib.parse.unquote(project_name_raw)
        project_slug = slugify(project_name)
        
        # Clean up year (remove trailing commas, spaces)
        year_raw = metadata.get('year', 'TBD')
        year = str(year_raw).strip().rstrip(',').strip()
        
        project_type = metadata.get('type', 'exhibition')
        
        # Map to filter categories
        filters = map_project_to_filters(metadata, master_tags)
        
        # Format type display - build from all type components
        project_type_lower = project_type.lower()
        exhibition_context = metadata.get('exhibition-context', '').lower()
        
        # Parse all types from type:: field
        type_parts = [t.strip() for t in project_type.split(',')]
        
        # Check exhibition context
        has_solo = 'solo' in exhibition_context
        has_group = 'group' in exhibition_context
        
        # Build display string
        display_parts = []
        
        # Add exhibition context
        if has_solo and has_group:
            display_parts.append('Solo & Group Exhibition')
        elif has_solo:
            display_parts.append('Solo Exhibition')
        elif has_group:
            display_parts.append('Group Exhibition')
        
        # Add all other types from type:: field
        for part in type_parts:
            part_lower = part.lower()
            # Skip exhibition context types (already handled above)
            if part_lower in ['solo', 'group', 'exhibition']:
                continue
            # Capitalize and add
            display_parts.append(part.capitalize())
        
        # Join with comma
        type_display = ', '.join(display_parts) if display_parts else 'Project'
        
        # Get preview image
        preview_image = get_project_preview_image(project_slug)
        
        # Determine symbol class
        symbol_class = 'solo' if 'solo' in filters else 'group'
        
        projects_data.append({
            'name': project_name,
            'slug': project_slug,
            'year': year,
            'type_display': type_display,
            'filters': filters,
            'preview_image': preview_image,
            'symbol_class': symbol_class
        })
        
        print(f"  ✓ {project_name} ({year}) → filters: {', '.join(filters) if filters else 'none'}")
    
    if skipped_projects:
        print()
        print(f"⚠ Skipped {len(skipped_projects)} HTML files without matching .md files")
    
    print()
    print(f"✓ Successfully processed {len(projects_data)} projects")
    print()
    
    # Sort by year (descending)
    projects_data.sort(key=lambda x: str(x['year']), reverse=True)
    
    # Group by year
    years = {}
    for proj in projects_data:
        year = proj['year']
        if year not in years:
            years[year] = []
        years[year].append(proj)
    
    # Generate HTML content
    projects_html = ''
    
    for year in sorted(years.keys(), reverse=True):
        projects_html += f'''    <!-- {year} -->
    <tr>
      <td class="year-cell">> {year}</td>
    </tr>
'''
        for proj in years[year]:
            filters_str = ' '.join(proj['filters'])
            
            # Build preview image HTML
            preview_html = ''
            if proj['preview_image']:
                preview_html = f'''              <div class="project-preview">
                <img src="{proj['preview_image']}" alt="{proj['name']} preview">
              </div>
'''
            
            projects_html += f'''    <tr class="project-cell visible" data-categories="{filters_str}">
      <td>
        <div class="project-content">
          <a href="projects/{proj['slug']}.html" class="project-link">
            <div class="project-info">
              <div class="project-header">
                <div class="project-title-line">
                  <span class="project-symbol {proj['symbol_class']}">▓</span>
                  <span class="project-title-text">{proj['name']}</span>
                </div>
                <div class="project-meta">{proj['type_display']}</div>
              </div>
{preview_html}            </div>
          </a>
        </div>
      </td>
    </tr>
'''
    
    # Read template (use current work.html as template)
    work_template_file = EN_DIR / 'work.html'
    if not work_template_file.exists():
        print(f"❌ ERROR: work.html template not found: {work_template_file}")
        return False
    
    with open(work_template_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Replace projects table content
    # Match from first year cell to end of projects-table
    pattern = r'(<table class="projects-table"[^>]*>).*?(</table>)'
    replacement = r'\1\n' + projects_html + r'  \2'
    
    html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    
    # Write output
    output_file = EN_DIR / 'work.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print()
    print("=" * 60)
    print(f"✅ SUCCESS! Generated: {output_file}")
    print("=" * 60)
    print()
    print(f"  Total projects: {len(projects_data)}")
    print(f"  Years covered: {', '.join(str(y) for y in sorted(years.keys(), reverse=True))}")
    print()
    
    # Automatically generate sitemap after work.html
    print("Updating sitemap...")
    print()
    generate_sitemap()
    
    return True

def find_markdown_file(project_name):
    """Find markdown file by project name or slug"""
    # Try direct match first
    md_file = LOGSEQ_DIR / f"{project_name}.md"
    if md_file.exists():
        return md_file
    
    # Try case-insensitive search
    for f in LOGSEQ_DIR.glob('*.md'):
        if f.stem.lower() == project_name.lower():
            return f
    
    # Try searching by slug match
    search_slug = slugify(project_name)
    for f in LOGSEQ_DIR.glob('*.md'):
        file_slug = slugify(f.stem)
        if file_slug == search_slug:
            return f
    
    return None

def build_single_project(project_name):
    """Build a single project page from markdown"""
    
    print("=" * 60)
    print(f"Building project: {project_name}")
    print("=" * 60)
    print()
    
    # Find markdown file
    md_file = find_markdown_file(project_name)
    if not md_file:
        print(f"❌ ERROR: Markdown file not found for: {project_name}")
        print(f"   Searched in: {LOGSEQ_DIR}")
        return False
    
    print(f"✓ Found markdown: {md_file.name}")
    
    # Detect language from filename
    language = detect_language(md_file)
    print(f"✓ Detected language: {language.upper()}")
    
    # Load translations
    translations = load_translations()
    
    # Get output directories for this language
    lang_dir, projects_dir = get_output_dirs(language)
    
    # Load template
    if not TEMPLATE_FILE.exists():
        print(f"❌ ERROR: Template file not found: {TEMPLATE_FILE}")
        return False
    
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template = f.read()
    
    print(f"✓ Template loaded: {TEMPLATE_FILE}")
    print()
    
    # Create directories
    projects_dir.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)
    
    try:
        # Read metadata first to get project slug
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        metadata = parse_metadata(content)
        
        if 'year' not in metadata:
            print(f"❌ ERROR: Project has no 'year' metadata")
            return False
        
        # Use name-cz for Czech projects, name-en for English
        name_key = 'name-cz' if language == 'cz' else 'name-en'
        project_slug = slugify(metadata.get(name_key, metadata.get('name-en', md_file.stem)))
        output_file = projects_dir / f"{project_slug}.html"
        
        print(f"Generating HTML...")
        print(f"  Language: {language.upper()}")
        print(f"  Project slug: {project_slug}")
        print(f"  Output file: {output_file}")
        print()
        
        # Generate HTML with language support
        result = generate_project_from_template(md_file, template, project_slug, language=language, translations=translations)
        
        if result[0] is None:
            print(f"❌ ERROR: Failed to generate HTML")
            return False
        
        html_content, metadata = result
        
        # Write HTML file (overwrite if exists)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print()
        print("=" * 60)
        print(f"✅ SUCCESS! Generated: {output_file}")
        print("=" * 60)
        print()
        print(f"  Project: {metadata.get('name-en', 'Unknown')}")
        print(f"  Year: {metadata.get('year', 'Unknown')}")
        print(f"  Type: {metadata.get('type', 'Unknown')}")
        print()
        
        return True
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Build portfolio project pages from Logseq markdown + Taxonomy tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Build single project
  python build_smart.py Ludomancer
  python build_smart.py "Place of Family"
  
  # Generate work.html from all projects (also updates sitemap)
  python build_smart.py --build-work
  
  # Generate sitemap.xml only
  python build_smart.py --build-sitemap
  
  # Taxonomy tools
  python build_smart.py --show-related "Place of Family"
  python build_smart.py --list-tags
  python build_smart.py --audit-tags

The script will:
  1. Find the markdown file in logseq-data/pages/
  2. Copy images to assets/images/ProjectName/
  3. Generate HTML with auto-generated Related Projects
  4. (--build-work) Generate work.html with all projects + sitemap.xml
  5. (--build-sitemap) Generate sitemap.xml with all pages
        '''
    )
    
    parser.add_argument(
        'project',
        type=str,
        nargs='?',
        help='Project name (as it appears in markdown filename)'
    )
    
    parser.add_argument(
        '--show-related',
        metavar='PROJECT',
        help='Show related projects for given project name'
    )
    
    parser.add_argument(
        '--list-tags',
        action='store_true',
        help='List all unique tags used across projects'
    )
    
    parser.add_argument(
        '--audit-tags',
        action='store_true',
        help='Audit taxonomy - show stats and potential issues'
    )
    
    parser.add_argument(
        '--build-work',
        action='store_true',
        help='Generate work.html from all projects (also updates sitemap)'
    )
    
    parser.add_argument(
        '--build-sitemap',
        action='store_true',
        help='Generate sitemap.xml with all pages'
    )
    
    args = parser.parse_args()
    
    # Taxonomy commands
    if args.show_related:
        # Show related projects for a given project
        print("=" * 60)
        print(f"Finding related projects for: {args.show_related}")
        print("=" * 60)
        print()
        
        md_file = find_markdown_file(args.show_related)
        if not md_file:
            print(f"❌ ERROR: Project not found: {args.show_related}")
            sys.exit(1)
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        metadata = parse_metadata(content)
        
        master_tags = load_json(MASTER_TAGS_FILE)
        all_projects = get_all_project_metadata()
        
        if not master_tags:
            print("❌ ERROR: Master tags not found. Run from project root.")
            sys.exit(1)
        
        # Show IDF weights for this project's tags
        project_tags = extract_tags_from_metadata(metadata)
        idf_weights = calculate_tag_idf_weights(all_projects)
        
        print(f"Project tags with IDF weights (rare tags = higher weight):\n")
        for tag in project_tags:
            tag_clean = tag.lstrip('#')
            weight = idf_weights.get(tag_clean, 1.0)
            # Count how many projects have this tag
            count = sum(1 for _, m in all_projects if tag in extract_tags_from_metadata(m))
            print(f"  {tag:25s} → weight: {weight:4.2f}  (used in {count}/{len(all_projects)} projects)")
        print()
        print("-" * 60)
        print()
        
        related = find_related_projects(metadata, all_projects, master_tags, max_results=5)
        
        if not related:
            print("ℹ️  No related projects found (project may have no tags)")
            sys.exit(0)
        
        print(f"Found {len(related)} related projects:\n")
        for i, proj in enumerate(related, 1):
            print(f"{i}. {proj['name']} ({proj['year']})")
            print(f"   Similarity: {proj['similarity']:.0%}")
            print(f"   Matching tags: {', '.join(proj['matching_tags'])}")
            print()
        
        sys.exit(0)
    
    elif args.list_tags:
        # List all unique tags
        print("=" * 60)
        print("All unique tags across projects")
        print("=" * 60)
        print()
        
        all_projects = get_all_project_metadata()
        all_tags = set()
        tag_counts = {}
        
        for md_file, metadata in all_projects:
            tags = extract_tags_from_metadata(metadata)
            for tag in tags:
                all_tags.add(tag)
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        if not all_tags:
            print("ℹ️  No tags found in projects")
            sys.exit(0)
        
        # Sort by frequency
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"Total unique tags: {len(all_tags)}")
        print(f"Total projects: {len(all_projects)}\n")
        
        for tag, count in sorted_tags:
            print(f"{tag:30s} → {count:2d} project(s)")
        
        sys.exit(0)
    
    elif args.audit_tags:
        # Audit taxonomy
        print("=" * 60)
        print("Taxonomy Audit")
        print("=" * 60)
        print()
        
        master_tags = load_json(MASTER_TAGS_FILE)
        all_projects = get_all_project_metadata()
        
        if not master_tags:
            print("❌ ERROR: Master tags not found")
            sys.exit(1)
        
        # Collect all tags from projects
        project_tags = set()
        projects_without_tags = []
        projects_few_tags = []
        projects_many_tags = []
        
        for md_file, metadata in all_projects:
            tags = extract_tags_from_metadata(metadata)
            if not tags:
                projects_without_tags.append(metadata.get('name-en', md_file.stem))
            elif len(tags) < 3:
                projects_few_tags.append((metadata.get('name-en', md_file.stem), len(tags)))
            elif len(tags) > 7:
                projects_many_tags.append((metadata.get('name-en', md_file.stem), len(tags)))
            
            project_tags.update(tags)
        
        # Get master tags
        master_tag_list = set()
        for category in master_tags.get('categories', {}).values():
            if 'tags' in category:
                master_tag_list.update(f"#{tag}" for tag in category['tags'])
            if 'specific_games' in category:
                master_tag_list.update(f"#{tag}" for tag in category['specific_games'])
        
        # Find deprecated tags still in use
        deprecated = master_tags.get('deprecated_tags', {})
        deprecated_in_use = [tag for tag in project_tags if tag.lstrip('#') in deprecated]
        
        # Find tags not in master list
        unknown_tags = project_tags - master_tag_list
        
        # Find unused master tags
        unused_tags = master_tag_list - project_tags
        
        # Report
        print(f"📊 Statistics:")
        print(f"   Projects: {len(all_projects)}")
        print(f"   Unique tags in use: {len(project_tags)}")
        print(f"   Master taxonomy tags: {len(master_tag_list)}")
        print()
        
        if projects_without_tags:
            print(f"⚠️  Projects without tags ({len(projects_without_tags)}):")
            for proj in projects_without_tags:
                print(f"   - {proj}")
            print()
        
        if projects_few_tags:
            print(f"ℹ️  Projects with < 3 tags ({len(projects_few_tags)}):")
            for proj, count in projects_few_tags:
                print(f"   - {proj} ({count} tags)")
            print()
        
        if projects_many_tags:
            print(f"ℹ️  Projects with > 7 tags ({len(projects_many_tags)}):")
            for proj, count in projects_many_tags:
                print(f"   - {proj} ({count} tags)")
            print()
        
        if deprecated_in_use:
            print(f"❌ Deprecated tags still in use ({len(deprecated_in_use)}):")
            for tag in deprecated_in_use:
                replacement = deprecated.get(tag.lstrip('#'), 'N/A')
                print(f"   - {tag} → {replacement}")
            print()
        
        if unknown_tags:
            print(f"⚠️  Tags not in master taxonomy ({len(unknown_tags)}):")
            for tag in sorted(unknown_tags):
                print(f"   - {tag}")
            print()
        
        if unused_tags and len(unused_tags) < 15:
            print(f"ℹ️  Unused tags in master taxonomy ({len(unused_tags)}):")
            for tag in sorted(unused_tags):
                print(f"   - {tag}")
            print()
        
        print("✅ Audit complete")
        sys.exit(0)
    
    elif args.build_sitemap:
        # Generate sitemap only
        success = generate_sitemap()
        sys.exit(0 if success else 1)
    
    elif args.build_work:
        # Generate work.html (automatically generates sitemap too)
        success = generate_work_html()
        sys.exit(0 if success else 1)
    
    # Default: Build project
    if not args.project:
        parser.print_help()
        sys.exit(1)
    
    success = build_single_project(args.project)
    sys.exit(0 if success else 1)

