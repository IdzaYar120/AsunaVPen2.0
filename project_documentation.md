# AsunaVPet - Technical Overview & Feature Set

**Version**: 1.0 (Beta / Early Access)
**Date**: 2024-01-31

## 🛠️ Technical Stack

-   **Language**: Python 3.12+
-   **GUI Framework**: PyQt6 (Widgets, Core, Gui, Multimedia)
-   **Image Processing**: Pillow (PIL) for sprite handling.
-   **AI Integration**: `google-genai` (v1.0+) - Google Gemini 2.0 Flash.
-   **Data Storage**: JSON (Atomic Save/Load with Backup).
-   **System Interaction**: `psutil` (for CPU/RAM/Battery monitoring).

## 🌟 Functional Modules

### 1. **Core Engine (`core/`)**
-   **PetEngine**: Central controller. Manages game loop, state transitions, and interaction between modules.
-   **ResourceManager**: Handles dynamic loading of sprite sheets and animations. Supports varying grid sizes (2x3, 2x5, etc.) and automatic scaling.
-   **StatsManager**: Manages persistent data (Hunger, Health, Happiness, XP, Inventory). Implements atomic saving (`.tmp` -> rename) and backup recovery (`.bak`).
-   **AIClient**: Interfaces with Google Gemini. Maintains "Asuna" persona with Ukrainian localization. Handles connection errors gracefully.

### 2. **User Interface (`ui/`)**
-   **PetWindow**: Transparent, frameless top-level window. Supports dragging, gravity simulation, and context menus.
-   **Dynamic Positioning**: UI elements (XP bar, Emotes, Bubbles) are anchored relative to the character's feet to support varying sprite sizes.
-   **Custom Widgets**:
    -   `SpeechBubble`: Interactive dialogs with AI.
    -   `HappinessGauge`: Circular progress indicator.
    -   `Inventory/Shop`: Grid-based item management.
    -   `FloatingText`: Animated status updates (+XP, +Health).

### 3. **Interactivity & Gameplay**
-   **States**: Idle, Walk (Left/Right), Sleep, Work, Training, Dragged, etc.
-   **Needs System**: Stats decay over time. Pet reacts to low stats (Sad/Tired emotions).
-   **System Monitor**: Asuna reacts to high CPU > 80%, low Battery < 20%, or high RAM usage.
-   **Mini-games**:
    -   *Coin Hunt*: Click interactive targets.
    -   *Slots*: Casino-style minigame.
-   **Progression**: Leveling system with visual badges. Unlocks features (currently conceptual).

### 4. **Localization**
-   **Language**: Ukrainian (UK).
-   **Structure**: All strings extracted to `assets/lang/uk.json`.

## 📂 Project Structure

```
AsunaVPet/
├── assets/             # Images, Sounds, Lang
│   └── lang/uk.json    # Localization
├── config/             # Configuration
│   ├── settings.py     # Game Constants
│   └── ui_settings.py  # UI Layout Constants
├── core/               # Business Logic
│   ├── engine.py       # Main Loop
│   ├── ai_client.py    # Gemini Integration
│   └── ...
├── ui/                 # Presentation Layer
│   ├── window.py       # Main Pet Window
│   └── ...
├── data/               # User Data (Excluded from git)
│   ├── stats.json
│   └── stats.json.bak
├── main.py             # Entry Point
└── production_audit.md # Audit Report
```

## 🔒 Security & Stability features
-   **Error Handling**: Logging of all critical failures (Asset loading, AI, Save/Load).
-   **Safe Mode**: App runs even if `google-genai` is missing (AI features disabled).
-   **Data Integrity**: Atomic writes prevent save file corruption.
