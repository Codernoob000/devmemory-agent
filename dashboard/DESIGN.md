---
name: DevMemory Agent
colors:
  surface: '#0e1416'
  surface-dim: '#0e1416'
  surface-bright: '#343a3c'
  surface-container-lowest: '#090f11'
  surface-container-low: '#171d1e'
  surface-container: '#1b2122'
  surface-container-high: '#252b2d'
  surface-container-highest: '#303638'
  on-surface: '#dee3e6'
  on-surface-variant: '#bcc9cd'
  inverse-surface: '#dee3e6'
  inverse-on-surface: '#2b3133'
  outline: '#869397'
  outline-variant: '#3d494c'
  surface-tint: '#4cd7f6'
  primary: '#4cd7f6'
  on-primary: '#003640'
  primary-container: '#06b6d4'
  on-primary-container: '#00424f'
  inverse-primary: '#00687a'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffb2b9'
  on-tertiary: '#67001f'
  tertiary-container: '#ff7e8f'
  on-tertiary-container: '#790b29'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#acedff'
  primary-fixed-dim: '#4cd7f6'
  on-primary-fixed: '#001f26'
  on-primary-fixed-variant: '#004e5c'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdadc'
  tertiary-fixed-dim: '#ffb2b9'
  on-tertiary-fixed: '#400010'
  on-tertiary-fixed-variant: '#891933'
  background: '#0e1416'
  on-background: '#dee3e6'
  surface-variant: '#303638'
typography:
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 16px
  margin: 24px
  container-max: 1440px
---

## Brand & Style
The design system is engineered for deep-focus technical environments, catering to DevOps engineers and system architects. The aesthetic is a fusion of **Corporate Modern** and **Subtle Glassmorphism**, prioritizing high information density without sacrificing visual clarity.

The brand personality is authoritative, precise, and utilitarian. It evokes a "command center" feel through a dark-mode-first approach, using high-contrast accents to draw attention to critical system states. Visual interest is generated through light-refraction metaphors—subtle glows, translucent surfaces, and razor-sharp 1px strokes—reflecting the speed and transparency of modern automated workflows.

## Colors
The palette is optimized for long-duration monitor usage. 
- **Core Surfaces:** The background utilizes `slate-950` to provide a deep, non-distracting canvas. Layered surfaces use `zinc-900` to create subtle structural separation.
- **Accents:** `Cyan-500` is the primary action color, used for high-intent interactions. `Emerald-400` represents positive delta (savings, success, uptime), while `Rose-400` is reserved strictly for destructive actions or system alerts.
- **Borders:** `Slate-800` is the standard for structural containment, ensuring high-definition edges even in low-light environments.

## Typography
This design system employs a dual-font strategy to distinguish between UI navigation and technical data.
- **Geist Sans:** Used for all interface elements, headings, and instructional text. It provides a clean, geometric structure that feels contemporary and engineered.
- **JetBrains Mono:** Dedicated to code snippets, log streams, terminal outputs, and metadata labels. The increased x-height and distinct character shapes ensure legibility in dense data tables.

All typography should favor a "tight" aesthetic with slightly reduced letter-spacing on headlines to maintain a professional, high-density feel.

## Layout & Spacing
The system uses a **Fluid Grid** model based on a 4px baseline shift. 
- **Desktop:** 12-column grid with 16px gutters and 24px side margins. 
- **Tablet:** 8-column grid with 16px gutters.
- **Mobile:** 4-column grid with 12px gutters.

The layout philosophy emphasizes **Horizontal Segmentation**. Long-form data lists and logs should span the full width of their containers, while configuration forms are restricted to 8-column spans to prevent line-length eye fatigue. Use "Sticky" headers for all data tables to maintain context during deep scrolls.

## Elevation & Depth
Depth is communicated through **Tonal Layering** and **Glassmorphism** rather than traditional heavy shadows.
- **Level 0 (Background):** `slate-950`.
- **Level 1 (Cards/Panels):** `zinc-900` with a 1px `slate-800` border.
- **Level 2 (Overlays/Modals):** `zinc-900` with 40% opacity and a 20px Backdrop Blur. These elements feature a subtle inner glow (white at 5% opacity) on the top edge to simulate a light source.
- **Primary CTA Depth:** Buttons and active states utilize a localized outer glow using the Primary Cyan color at 15% opacity to signify prominence.

## Shapes
The shape language is **Soft (0.25rem)**, moving away from the playfulness of pill shapes toward a more industrial, "hardware-inspired" look. 
- Standard components (Inputs, Buttons) use `rounded-md` (4px).
- Larger containers and cards use `rounded-lg` (8px).
- Status indicators (dots) are the only fully circular elements allowed, used for active/inactive server states.

## Components
- **Buttons:** Primary buttons feature a subtle gradient from Cyan-500 to Cyan-600 with a CSS transition on hover that increases the "Primary Glow" effect. Ghost buttons use a 1px Slate-800 border that brightens to Slate-600 on hover.
- **Input Fields:** Backgrounds are slightly darker than their parent surface. The focus state must replace the border color with Cyan-500 and add a 2px outer ring with 10% opacity.
- **Chips/Badges:** Use JetBrains Mono for text. Backgrounds are low-opacity versions of the status color (e.g., Emerald at 10% opacity for "Healthy").
- **Code Blocks:** Darker background than the main surface (`#09090b`). Syntax highlighting follows a customized "Night Owl" inspired palette optimized for the Cyan/Emerald/Rose primary colors.
- **Cards:** Incorporate a subtle glassmorphism effect for sidebar navigation and floating widgets to provide a sense of hierarchy without excessive weight.