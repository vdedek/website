# LLM Tagging Prompt Example

This is a reference prompt for how `build_smart.py` should call LLM to suggest tags for projects.

## Prompt Template

```
You are a curator helping tag art projects for a portfolio website.

## Available Tags

[LOAD: taxonomy/master_tags.json - categories section]
[LOAD: taxonomy/tag_descriptions.json - for detailed meanings]

## Tag Selection Guidelines

1. Choose 3-7 tags that best describe the project
2. Use specific hierarchical tags when applicable (e.g., audio/spatial instead of just audio)
3. Always include the project's primary medium (installation, object, performance, artwork)
4. Include game-specific tags if the project focuses on a specific game
5. Avoid redundancy - don't use both parent and child tags unless both are relevant

## Project to Tag

### Metadata
```
[INSERT PROJECT METADATA from markdown frontmatter]
```

### Content
```
[INSERT PROJECT DESCRIPTION, curatorial text, about section]
```

## Your Task

Analyze the project and return a JSON response:

```json
{
  "selected_tags": [
    "#tag1",
    "#tag2",
    "#tag3"
  ],
  "reasoning": "Brief explanation of why these tags were chosen",
  "confidence": 0.85,
  "new_tags_suggested": [
    {
      "tag": "#new_tag",
      "reason": "This concept is not covered by existing taxonomy",
      "similar_to": "#existing_tag",
      "importance": "medium"
    }
  ],
  "alternative_tags": [
    {
      "tag": "#alternative",
      "reason": "Could also fit, but less central to the project"
    }
  ]
}
```

## Response Requirements

- **selected_tags**: Array of 3-7 tags from master taxonomy
- **reasoning**: One paragraph explaining tag selection
- **confidence**: 0.0-1.0 score of how confident you are
- **new_tags_suggested**: ONLY if project has concepts not in taxonomy (usually empty)
- **alternative_tags**: Tags that could work but weren't selected (for human review)

## Examples

### Example 1: Audio Installation about Gaming

**Input:**
```yaml
type:: exhibition, solo, audio
name-en:: The Last Advanced Movement Guide You Will Need
description:: 8 speakers, 3D sound - 50 minutes
```

**Project description:**
"At the heart of Viktor Dedek's performance is the world of computer game players, especially their specific relationship to time, space and movement. The eight-channel installation, in the form of a 3d-sound tunnel, presents three intersecting audio essays over a 50 minute period. They address the nature of the gamer's memory..."

**Output:**
```json
{
  "selected_tags": [
    "#installation",
    "#audio/spatial",
    "#actors/voice",
    "#game",
    "#movement",
    "#narrative/spoken",
    "#memory"
  ],
  "reasoning": "Primary medium is installation with 8-channel spatial audio (audio/spatial). Content focuses on gaming culture (game), player experience, and movement mechanics (movement). Features voice-over essays (actors/voice, narrative/spoken) exploring memory (memory) in gaming context.",
  "confidence": 0.92,
  "new_tags_suggested": [],
  "alternative_tags": [
    {
      "tag": "#player",
      "reason": "About player experience, but 'game' already covers this aspect"
    }
  ]
}
```

### Example 2: D&D Performance

**Input:**
```yaml
type:: performance/game
name-en:: Ranger. Episode Three of the Euromedieval Saga
description:: RPG experience based on Dungeon & Dragons game, two games with participants from public (one game was over-night)
```

**Output:**
```json
{
  "selected_tags": [
    "#rpg",
    "#game",
    "#D&D",
    "#narrative/interactive"
  ],
  "reasoning": "This is a public D&D session (D&D, rpg), which is inherently a game (game) with interactive storytelling where players create narrative through choices (narrative/interactive). Kept minimal since it's a focused performance type.",
  "confidence": 0.95,
  "new_tags_suggested": [],
  "alternative_tags": [
    {
      "tag": "#performance/game",
      "reason": "Technically fits, but type:: already specifies this"
    }
  ]
}
```

### Example 3: New Concept - VR Installation

**Input:**
```yaml
type:: exhibition, solo
name-en:: Virtual Horizons
description:: VR headset installation exploring virtual architecture
```

**Project description:**
"Visitors put on VR headsets to explore procedurally generated architectural spaces..."

**Output:**
```json
{
  "selected_tags": [
    "#installation",
    "#3d/modeling",
    "#worldbuilding"
  ],
  "reasoning": "Installation with 3D virtual environments (3d/modeling), creating imaginary architectural worlds (worldbuilding).",
  "confidence": 0.75,
  "new_tags_suggested": [
    {
      "tag": "#VR",
      "reason": "VR is a distinct medium not covered by existing tags. Different enough from 3d/modeling or game to warrant its own tag.",
      "similar_to": "#3d/modeling",
      "importance": "high"
    }
  ],
  "alternative_tags": []
}
```

---

## Implementation Notes for build_smart.py

```python
def suggest_tags_for_project(project_path):
    # 1. Load taxonomy
    master_tags = load_json("taxonomy/master_tags.json")
    tag_descriptions = load_json("taxonomy/tag_descriptions.json")
    
    # 2. Parse project markdown
    metadata, content = parse_project_markdown(project_path)
    
    # 3. Build prompt
    prompt = build_tagging_prompt(
        master_tags=master_tags,
        tag_descriptions=tag_descriptions,
        project_metadata=metadata,
        project_content=content
    )
    
    # 4. Call LLM
    response = llm_call(prompt, response_format="json")
    
    # 5. Present to user for approval
    print(f"\n📋 Suggested tags for: {metadata['name-en']}")
    print(f"   {', '.join(response['selected_tags'])}")
    print(f"\n💭 Reasoning: {response['reasoning']}")
    print(f"   Confidence: {response['confidence']:.0%}")
    
    if response['new_tags_suggested']:
        print(f"\n✨ New tags proposed:")
        for new_tag in response['new_tags_suggested']:
            print(f"   {new_tag['tag']} - {new_tag['reason']}")
    
    # 6. Prompt user
    approved = input("\n✓ Accept these tags? [Y/n]: ")
    
    if approved.lower() != 'n':
        # Write tags to project file
        write_tags_to_project(project_path, response['selected_tags'])
        
        # Handle new tags
        if response['new_tags_suggested']:
            add_to_pending(response['new_tags_suggested'])
            print("→ New tags added to taxonomy/new_tags_pending.json for review")
    
    return response
```

