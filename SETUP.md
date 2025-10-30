# Portfolio Web - Setup Guide

## Instalace

### 1. Nainstaluj Python závislosti

```bash
pip install -r requirements.txt
```

To nainstaluje:
- **Pillow** - pro generování responsive obrázků (thumbnails, medium, full)

### 2. Struktura projektu

```
portfolio-web/
├── build_smart.py           # Hlavní build script
├── image_processor.py       # Modul pro optimalizaci obrázků
├── logseq-data/
│   ├── pages/              # Tvoje .md poznámky z Logseq
│   └── assets/             # Originální high-res obrázky (LOKÁLNĚ!)
├── assets/
│   ├── images/             # Vygenerované optimalizované obrázky (pro web)
│   ├── css/
│   └── js/
└── en/
    ├── projects/           # Vygenerované HTML stránky
    └── work.html
```

### 3. První build

```bash
# Vygeneruj první projekt
python build_smart.py "Ludomancer"
```

Script automaticky:
1. Načte `logseq-data/pages/Ludomancer.md`
2. Zpracuje obrázky z `logseq-data/assets/`:
   - Vygeneruje thumbnails (400px)
   - Vygeneruje medium (1200px)
   - Vygeneruje full (2000px) 
3. Uloží do `assets/images/Ludomancer/`
4. Vygeneruje `en/projects/ludomancer.html`

## Workflow

### Nový projekt

1. **Vytvoř .md poznámku v Logseq**
   - Ulož do `logseq-data/pages/`
   - Přidej metadata: `year::`, `type::`, `name-en::`, atd.
   - Vlož obrázky: `![caption](../assets/obrazek.jpg)`

2. **Spusť build**
   ```bash
   python build_smart.py "Název Projektu"
   ```

3. **Zkontroluj výsledek**
   - Otevři `en/projects/nazev-projektu.html`
   - Zkontroluj, že obrázky fungují na různých velikostech obrazovky

### Update existujícího projektu

```bash
# Stejný příkaz - přepíše HTML
python build_smart.py "Ludomancer"
```

**Note:** Pokud už vygenerované obrázky existují, přeskočí se (rychlé).  
Pro force regeneraci obrázků smaž složky `thumbnails/`, `medium/`, `full/`.

## Git & GitHub

### První nastavení

```bash
# 1. Inicializuj Git repository
git init

# 2. Přidej remote (vytvoř nejdřív repo na GitHubu)
git remote add origin https://github.com/your-username/portfolio-web.git

# 3. Přidej soubory (dle .gitignore)
git add .

# 4. První commit
git commit -m "Initial commit: Portfolio website with build system"

# 5. Push na GitHub
git push -u origin main
```

### Běžné commity

```bash
# Přidej změny
git add .

# Commit s popisem
git commit -m "Add Changeling project"

# Push
git push
```

### Co commitovat

**✅ Commituj:**
- `logseq-data/pages/*.md` - metadata projektů (důležité pro zálohu!)
- `assets/images/**/thumbnails/` - optimalizované náhledy
- `assets/images/**/medium/` - střední verze
- `assets/images/**/full/` - web-full verze (2000px, 85% kvalita)
- `en/projects/*.html` - vygenerované stránky
- `en/work.html` - index projektů
- `assets/css/`, `assets/js/` - styly a skripty
- `taxonomy/` - systém tagů

**❌ Necommituj (automaticky ignorováno):**
- `logseq-data/assets/` - originální high-res obrázky (tiskové kvality!)
- `logseq-data/journals/` - denní poznámky
- `logseq-data/logseq/` - systémové soubory Logseq (config, bak/)
- `logseq-data/pages/deprecated/` - staré/nepublikované projekty
- `__pycache__/` - Python cache
- `.vscode/`, `.idea/` - IDE konfigurace

## Taxonomie a Related Projects

Build system automaticky generuje "Related Projects" sekci pomocí #tagů.

### Použití tagů

V .md poznámce přidej:
```markdown
tag:: #game-art #audio/spatial #installation
```

Build script:
1. Porovná tagy všech projektů
2. Najde podobné projekty (IDF weighting - rare tags = vyšší váha)
3. Vygeneruje "Related Projects" sekci

### Taxonomy příkazy

```bash
# Zobraz související projekty pro daný projekt
python build_smart.py --show-related "Ludomancer"

# Seznam všech tagů
python build_smart.py --list-tags

# Audit taxonomie (najdi chyby, deprecated tagy, atd.)
python build_smart.py --audit-tags
```

## Generování work.html

Stránka `work.html` zobrazuje všechny publikované projekty s filtry (Selected Works, Solo, Group, Performance, Audio, atd.).

### Automatické generování work.html

```bash
# Vygeneruj work.html ze všech projektů, které mají HTML v en/projects/
python build_smart.py --build-work
```

**Jak to funguje:**
1. Script najde všechny HTML soubory v `en/projects/`
2. Pro každý HTML najde odpovídající `.md` soubor v `logseq-data/pages/`
3. Načte metadata (název, rok, typ, tagy, featured)
4. Namapuje projekty na filtry podle `taxonomy/master_tags.json`
5. Vygeneruje `en/work.html` s funkcí filtrování

**Kdy spustit:**
- Po vytvoření/aktualizaci projektu
- Po změně metadat (featured, exhibition-context, tags)
- Po změně typu výstavy (solo → group)

### Mapování filtrů

Filtry na work.html se mapují z metadat:

| Filtr | Metadata |
|-------|----------|
| Selected Works | `featured:: yes` |
| Solo | `exhibition-context:: solo` |
| Group | `exhibition-context:: group` |
| Collaboration | tag `#collaboration` |
| Performance | `type:: performance` |
| Audio | `type:: audio` |
| Euromedieval Saga | `series:: euromedieval-saga` |

Viz `taxonomy/master_tags.json` pro kompletní mapování.

## Další příkazy

```bash
# Help
python build_smart.py --help

# Build konkrétního projektu
python build_smart.py "Place of Family"
python build_smart.py Skeleton

# Generuj work.html
python build_smart.py --build-work
```

## Troubleshooting

### "Module 'PIL' not found"
```bash
pip install Pillow
```

### "Markdown file not found"
- Zkontroluj, že soubor existuje v `logseq-data/pages/`
- Název souboru musí odpovídat názvu projektu
- Zkus přesný název: `python build_smart.py "Skeleton. Episode Two of the Euromedieval Saga"`

### Obrázky se negenerují
- Zkontroluj, že obrázky existují v `logseq-data/assets/`
- Zkontroluj, že máš nainstalovaný Pillow
- Smaž složky `thumbnails/`, `medium/`, `full/` a zkus znovu

### Build je pomalý
- První build generuje všechny obrázky (může trvat 10-30s)
- Další buildy přeskočí existující obrázky (rychlé, 1-2s)

## Další informace

- **Taxonomy System:** Viz `taxonomy/master_tags.json` a `taxonomy/README.md`
- **GitHub README:** Viz `README.md` pro popis projektu a strukturu

## Tips

1. **Batch build:** Můžeš vytvořit shell script pro build všech projektů najednou
2. **Watch mode:** Použij `watchdog` pro automatický rebuild při změně .md souboru
3. **Deploy:** Commituj pouze `en/` a `assets/images/` složky na server
4. **Backup:** Originály z `logseq-data/assets/` zálohuj do cloudu (Google Drive, Dropbox, atd.)


