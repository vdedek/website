type:: installation, performance, audio
exhibition-context:: solo
name-en:: Project Name
name-cz:: Jméno projektu
year:: 2024
language:: Czech/English
author:: [[Viktor Dedek]]
collaboration:: 
curated-by:: Curator Name
materials:: materials used
description:: short description
duration:: 30min
dimensions:: 
audio-url-cz:: https://soundcloud.com/...
audio-url-en:: https://soundcloud.com/...
video:: 
link:: [Exhibition Website](https://example.com)
press:: [Press Article](https://example.com)
tag:: #installation #audio #performance #collaboration #writing
related-projects:: 
featured:: yes
series:: euromedieval-saga

# ========================================
# FILTRY NA WORK.HTML - jak je nastavit:
# ========================================
# 
# Filtry na work.html se nastavují pomocí těchto metadata:
#
# 1. Selected Works → featured:: yes
# 2. Solo → exhibition-context:: solo  (nebo type:: solo)
# 3. Group → exhibition-context:: group  (nebo type:: group)
# 4. Collaboration → tag:: #collaboration
# 5. Performance → type:: performance
# 6. Writing → tag:: #writing
# 7. Audio → type:: audio
# 8. Euromedieval Saga → series:: euromedieval-saga
#
# POZNÁMKA: "tag::" se používá na DVĚ věci:
#   - Filtry (collaboration, writing)
#   - Podobnost projektů (všechny ostatní tagy)
# 
# ========================================
-
- ![Hero image description for tooltip](../assets/hero-image.jpg)
- exhibitions::
	- Sep-Nov 2024: Solo Exhibition, Gallery Name
	  start:: [[Sep 1st, 2024]]
	  end:: [[Nov 30th, 2024]]
	  place:: Gallery Name
	  town:: City
	  country:: Czech Republic
	  venue-type:: gallery space, outdoor
	  link:: [Exhibition Website](https://example.com)
	- Jan-Mar 2025: Group Exhibition "Exhibition Title"
	  start:: [[Jan 15th, 2025]]
	  end:: [[Mar 31st, 2025]]
	  place:: Another Gallery
	  town:: Another City
	  country:: Country
	  venue-type:: museum
	  link:: [Exhibition Website](https://example.com)
-
- #### Curatorial text by Curator Name:
	- *„Curatorial text here..."*
-
- #### Curatorial text by Curator Name (FIRST PARAGRAPH VISIBLE):
  show-first-paragraph:: true
	- First paragraph is visible. This text is shown immediately to the reader in the quote style.
	- Second paragraph is collapsible. Click "Read whole text" to expand this part and continue reading the full curatorial text.
-
- #### Curatorial text by Curator Name (FULLY COLLAPSIBLE - Logseq native):
  collapsed:: true
	- Entire text is hidden. User must click "Curatorial Text (click to expand)" to see this text.
	- In Logseq, you can collapse/expand this section with the triangle icon.
-
- Main project description starts here. You can include [markdown links](https://example.com) anywhere in the text and they will be converted to HTML links automatically.
  
  Second paragraph with more information. Links to [external websites](https://soundcloud.com/artist) or [documentation](https://example.com/file.pdf) work anywhere.
-
- #### Exhibition text from authors:
	- *Author's text here...*
-
- > *"First quote from the work..."*
- > *"Second quote..."*
-
- #### Video:
	- @@html: <iframe src="video-url" width="640" height="360"></iframe>@@
-
- #### Short story / Review / Text:
  type:: shortstory
  author:: [[Viktor Dedek]]
	- @@html: <iframe src="path-to-pdf.pdf" height="800px"></iframe>@@
-
- #### Poster / Additional material:
  collapsed:: true
	- ![additional.png](../assets/additional.png)
-
- #### Credits:
	- **Concept authors:**
	  Name One and Name Two
	  **Artists:**
	  [[Artist One]], [[Artist Two]]
	  **Curator:**
	  Curator Name
	  **Graphic design:**
	  Designer Name
-
- #### Program:
	- **Speaker Name** – Talk title
	- **[[Viktor Dedek]]** – Project title
-
- #### Documentation
- Group Exhibition "Exhibition Name", Gallery Name
  id:: optional-id
- ![Tooltip text for image 1](../assets/image-01.jpg)
- ![Tooltip text for image 2](../assets/image-02.jpg)
- Solo Exhibition, Gallery Name, City
- ![Tooltip text](../assets/image-03.jpg) Optional caption text ↪
- ![Tooltip text](../assets/image-04.jpg)
  Optional caption on indented line ↪
- ![Tooltip text](../assets/image-05.jpg) [[Related Project Name]]