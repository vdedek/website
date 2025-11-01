# Průvodce lokalizací / Localization Guide

## 🌍 Jak funguje lokalizace / How Localization Works

Tento build systém automaticky detekuje jazyk projektu podle názvu souboru a překládá všechny ustálené výrazy (labels, buttony, nadpisy) podle slovníku `translations.json`.

**Ty potřebuješ překládat jen velké textové bloky** - kurátorské texty, popisy projektů, atd.

---

## 📝 Postup pro vytvoření české verze projektu

### 1. Vytvoř českou verzi v Logsequ

V Logsequ přejmenuj stránku na strukturu s `/CZ`:
- `Changeling` → `Changeling/CZ`
- Vytvoří se soubor `Changeling___CZ.md` ve složce `logseq-data/pages/`

### 2. Překládej jen velké texty

V markdown souboru překládej:
- ✅ **Kurátorské texty** (pod `#### Curatorial text`)
- ✅ **Popisy projektů** (pod `#### About project`)
- ✅ **Dlouhé odstavce** (textové bloky)
- ✅ **Názvy výstav** v `exhibitions::` (pokud jsou česky)
- ✅ **Titulky obrázků** (pokud mají textový popis)

**NEPŘEKLÁDEJ:**
- ❌ Metadata (type::, year::, materials::, atd.) - zůstávají anglicky
- ❌ Názvy sekcí (`#### Documentation`, `#### Credits`) - překládají se automaticky
- ❌ Labely ("Type:", "Year:", "Listen to audio") - překládají se automaticky

### 3. Použij české názvy a přelož metadata přímo v souboru

V českém souboru (`Changeling___CZ.md`) překládej metadata přímo - není potřeba zvláštní varianty:

```markdown
name-en:: Changeling
name-cz:: Měňavec
materials:: digitální fotografie, audio nahrávka, přenosné rádio
description:: audiovizuální instalace, 7 černobílých fotografií, 14min audio nahrávka
```

**Důležité:** Protože máš dva samostatné soubory (`.md` pro EN, `___CZ.md` pro CZ), prostě překládej obsah polí přímo. Build script pozná jazyk podle názvu souboru.

### 4. Vygeneruj HTML

Spusť build script:
```bash
python build_smart.py "Changeling___CZ"
```

Build script:
- ✅ Detekuje jazyk (podle `___CZ` v názvu souboru)
- ✅ Načte překlady ze slovníku `translations.json`
- ✅ Vygeneruje HTML do složky `cz/projects/`
- ✅ Automaticky přeloží všechny ustálené výrazy
- ✅ Nastaví správný `lang="cs"` atribut v HTML
- ✅ Použije české URL **bez diakritiky**: `https://viktordedek.com/cz/projects/menavec.html`
- ✅ Sdílí obrázky mezi jazykovými verzemi (ukládá je vždy do složky podle anglického názvu)

---

## 🔧 Slovník překladů

Všechny ustálené výrazy jsou ve slovníku **`translations.json`**.

Můžeš přidávat nové překlady, pokud potřebuješ:

```json
{
  "en": {
    "common": {
      "new_label": "New Label"
    }
  },
  "cz": {
    "common": {
      "new_label": "Nový štítek"
    }
  }
}
```

### Aktuální překlady:

**Labels / Štítky:**
| English | Česky |
|---------|-------|
| Type | Typ |
| Year | Rok |
| Materials | Materiály |
| Duration | Délka |
| Listen to audio (CZ) | Poslechnout audio (CZ) |
| Exhibition History | Historie výstav |
| Documentation | Dokumentace |
| Related Projects | Související projekty |
| Read more | Číst dále |

**Typy projektů (automaticky překládané):**
| English | Česky |
|---------|-------|
| Installation | Instalace |
| Audio | Audio |
| Performance | Performance |
| Video | Video |
| Writing | Text |
| Solo Exhibition | Samostatná výstava |
| Group Exhibition | Skupinová výstava |
| Lecture | Přednáška |
| Workshop | Workshop |

**Příklad:** `type:: installation, audio` → zobrazí se jako "Instalace, Audio" v české verzi

---

## 📂 Struktura souborů

```
portfolio-web/
├── logseq-data/pages/
│   ├── Changeling.md              # Anglická verze
│   └── Changeling___CZ.md         # Česká verze (jen překládáš velké texty)
├── en/projects/
│   └── changeling.html            # Vygenerováno z Changeling.md
├── cz/projects/
│   └── menavec.html               # Vygenerováno z Changeling___CZ.md
├── translations.json              # Slovník překladů
└── build_smart.py                 # Build script s podporou lokalizace
```

---

## 🎯 Příklad: Changeling → Měňavec

### Anglická verze (`Changeling.md`)

```markdown
type:: installation, audio
name-en:: Changeling
name-cz:: Měňavec
year:: 2024
materials:: digital photography, audio recording, portable radio

#### About project
- Changeling is an audiovisual installation consisting of seven black and white photographs...

#### Documentation
- ![Installation view](../assets/image.jpg)
```

### Česká verze (`Changeling___CZ.md`)

```markdown
type:: installation, audio
name-en:: Changeling
name-cz:: Měňavec
year:: 2024
materials:: digitální fotografie, audio nahrávka, přenosné rádio

#### About project
- Měňavec je audiovizuální instalace sestavená ze sedmi černobílých fotografií...

#### Documentation
- ![Instalační pohled](../assets/image.jpg)
```

**Všimni si:** V české verzi prostě překládáš `materials::` přímo do češtiny.

### Výsledek:

**Anglická verze** → `en/projects/changeling.html`
- ✅ Používá anglické výrazy: "Documentation", "Related Projects"
- ✅ URL: `https://viktordedek.com/en/projects/changeling.html`
- ✅ `<html lang="en">`

**Česká verze** → `cz/projects/menavec.html`
- ✅ Používá české výrazy: "Dokumentace", "Související projekty"
- ✅ URL: `https://viktordedek.com/cz/projects/menavec.html`
- ✅ `<html lang="cs">`

---

## 🚀 Build příkazy

### Build jednoho projektu
```bash
# Anglická verze
python build_smart.py Changeling

# Česká verze
python build_smart.py "Changeling___CZ"
```

### Build všech projektů (work.html)
```bash
python build_smart.py --build-work
```

---

## 💡 Tipy

1. **Postupné překládání**: Nemusíš překládat všechny projekty najednou. Vytvoř `___CZ` verzi jen pro projekty, které chceš mít česky.

2. **Sdílení obrázků**: Obrázky se automaticky sdílí mezi jazykovými verzemi. Build systém vždy ukládá obrázky do složky podle **anglického názvu projektu** (např. `assets/images/Changeling/`), takže česká verze "Měňavec" používá stejné obrázky jako anglická "Changeling". Žádná duplikace! ✅

3. **URL bez diakritiky**: České URL jsou automaticky převedené bez diakritiky (`Měňavec` → `menavec.html`), aby fungovaly spolehlivě na všech serverech.

4. **Testování**: Po vygenerování zkontroluj HTML v prohlížeči, zda všechny výrazy jsou správně přeložené.

5. **Přidání nových výrazů**: Pokud najdeš výraz, který není v slovníku, přidej ho do `translations.json` a znovu vygeneruj.

---

## ❓ FAQ

**Q: Musím mít obě jazykové verze pro každý projekt?**  
A: Ne, můžeš mít jen anglickou verzi. Českou vytvoř jen pro projekty, kde to má smysl.

**Q: Co s obrázky? Musím je duplikovat pro českou verzi?**  
A: Ne! Obrázky se automaticky sdílí. Build systém vždy ukládá obrázky do složky podle anglického názvu (např. `assets/images/Changeling/`), a obě jazykové verze používají stejné soubory. Úspora místa! 🎉

**Q: Můžu změnit překlady v slovníku?**  
A: Ano! Uprav `translations.json` a znovu vygeneruj HTML.

**Q: Jak přidám další jazyk (např. němčinu)?**  
A: Přidej novou sekci do `translations.json` (např. `"de": {...}`) a uprav detekci jazyka v `build_smart.py` (funkce `detect_language`).

**Q: Co když chci jiný název souboru než `___CZ`?**  
A: Uprav funkci `detect_language()` v `build_smart.py` podle svých potřeb.

**Q: Co se stane s existujícími obrázky, když znovu vygeneruji projekt?**  
A: Obrázky se přegenerují jen pokud se změnily zdrojové soubory v Logsequ. Pokud už existují v `assets/images/ProjectName/`, použijí se existující.

---

## 🎨 Další rozvoj

V budoucnu můžeš:
- Přidat další jazyky (DE, FR, atd.)
- Vytvořit language switcher na webu
- Automaticky generovat links mezi jazykovými verzemi
- Vytvořit separate `work.html` pro každý jazyk

