# Viktor Dedek - Portfolio Website

Personal portfolio website showcasing interdisciplinary art projects exploring gaming, performance, installation, and narrative.

## 🌐 Live Site

[viktordedek.com](https://viktordedek.com) *(coming soon)*

## 🎨 About

Portfolio of Viktor Dedek - artist working at the intersection of:
- Gaming studies & player experience
- Installation & performance art
- Audio & narrative work
- Critical theory & speculative fiction

## 🛠️ Technology Stack

- **Pure HTML/CSS/JS** - No frameworks, fast and simple
- **Python build system** - Automated project page generation
- **Responsive images** - Optimized for web (thumbnail, medium, full)
- **Retro 90s aesthetic** - Windows 95-inspired UI

## 📁 Project Structure

```
portfolio-web/
├── assets/           # Public web assets
│   ├── css/         # Stylesheets
│   ├── js/          # JavaScript
│   ├── fonts/       # Custom fonts
│   ├── gif_intro/   # Retro GIF animations
│   └── images/      # Optimized project images
├── en/              # English pages
│   ├── projects/    # Generated project pages
│   ├── work.html    # Projects index with filters
│   └── welcome.html # Homepage
├── cz/              # Czech pages (coming soon)
├── taxonomy/        # Tag system & project metadata
├── build_smart.py   # Project page generator
├── image_processor.py  # Image optimization
└── requirements.txt
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Pillow library for image processing

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/portfolio-web.git
cd portfolio-web

# Install dependencies
pip install -r requirements.txt
```

### Usage

#### Generate a project page:
```bash
python build_smart.py "Project Name"
```

#### Regenerate all published projects:
```bash
python build_smart.py --build-work
```

#### View the site:
Open `en/welcome.html` in your browser

## 📝 Build System

The site uses a custom Python build system that:
1. Reads project metadata from Logseq markdown files (private workspace)
2. Processes and optimizes images (thumbnail/medium/full versions)
3. Generates HTML pages from templates
4. Maintains taxonomy and filtering system
5. Auto-generates the work.html index page

See [BUILD-README.md](BUILD-README.md) for detailed documentation.

## 🖼️ Image Processing

Images are automatically processed into three sizes:
- **Thumbnail** (400px) - For project grid/list view
- **Medium** (1200px) - For in-page display
- **Full** (2000px) - For lightbox/zoom view

Original high-resolution images are kept private in the workspace.

See [IMAGE-OPTIMIZATION-README.md](IMAGE-OPTIMIZATION-README.md) for details.

## 🏷️ Taxonomy System

Projects are tagged and filtered using a hierarchical taxonomy:
- Medium (installation, performance, object, photography)
- Technology (audio, 3d, AI)
- Gaming (gaming, gamebook, rpg, specific games)
- Themes (dream, memory, transformation, speculation)
- Context (collaboration, museum, interactive, workshop)

See [taxonomy/README.md](taxonomy/README.md) for complete tag system.

## 📄 License

© 2025 Viktor Dedek. All rights reserved.

Website code is available for reference, but content and artwork remain under copyright.

## 📧 Contact

- Website: [viktordedek.com](https://viktordedek.com)
- Email: dedekviktor@gmail.com

---

**Note:** The `logseq-data/` folder (private workspace) is not included in this repository.

