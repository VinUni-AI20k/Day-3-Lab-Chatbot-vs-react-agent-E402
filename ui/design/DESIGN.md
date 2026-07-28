---
name: Career Narrative Desktop
colors:
  surface: '#f7f9ff'
  surface-dim: '#d7dae0'
  surface-bright: '#f7f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f4fa'
  surface-container: '#ebeef4'
  surface-container-high: '#e5e8ee'
  surface-container-highest: '#dfe3e8'
  on-surface: '#181c20'
  on-surface-variant: '#414754'
  inverse-surface: '#2d3135'
  inverse-on-surface: '#eef1f7'
  outline: '#727785'
  outline-variant: '#c1c6d6'
  surface-tint: '#005bc0'
  primary: '#005bbf'
  on-primary: '#ffffff'
  primary-container: '#1a73e8'
  on-primary-container: '#ffffff'
  inverse-primary: '#adc7ff'
  secondary: '#005ac1'
  on-secondary: '#ffffff'
  secondary-container: '#4d8efe'
  on-secondary-container: '#00285c'
  tertiary: '#006d2c'
  on-tertiary: '#ffffff'
  tertiary-container: '#008939'
  on-tertiary-container: '#ffffff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc7ff'
  on-primary-fixed: '#001a41'
  on-primary-fixed-variant: '#004493'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a41'
  on-secondary-fixed-variant: '#004494'
  tertiary-fixed: '#89fa9b'
  tertiary-fixed-dim: '#6ddd81'
  on-tertiary-fixed: '#002108'
  on-tertiary-fixed-variant: '#005320'
  background: '#f7f9ff'
  on-background: '#181c20'
  surface-variant: '#dfe3e8'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 57px
    fontWeight: '400'
    lineHeight: 64px
    letterSpacing: -0.25px
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: 0px
  headline-md:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '500'
    lineHeight: 36px
    letterSpacing: 0px
  title-lg:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: 0px
  title-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0.15px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0.5px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0.25px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.1px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.5px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 16px
  md: 24px
  lg: 32px
  xl: 48px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style
The design system is engineered for a student-centric career orientation platform, emphasizing clarity, encouragement, and professional growth. The brand personality is "The Empathetic Mentor"—knowledgeable and structured, yet deeply approachable and optimistic. 

The aesthetic follows **Modern Corporate** principles infused with **Material Design 3** logic. It utilizes a clean, high-breathability layout with significant whitespace to reduce cognitive load during complex career mapping. Visuals are grounded in reliability but avoid being "stuffy" by using soft tonal shifts and fluid transitions. The emotional response should be one of "structured possibility"—helping students feel that their future is both exciting and manageable.

## Colors
The palette is rooted in the established primary blue, serving as the "Source" color for a full Material 3 tonal palette. 

- **Primary (#1a73e8):** Used for key action buttons, active states, and brand representation.
- **Secondary (#4285f4):** A lighter, supportive blue used for less prominent accents and subtle state changes.
- **Tertiary (#34a853):** A growth-oriented green reserved for "Success" states, career milestones, and positive progress indicators.
- **Surface & Background:** Utilizes a neutral-grey scale with very slight blue tinting (e.g., #F8F9FA) to ensure the interface feels expansive and clean. Surface-container roles are used to differentiate content areas without heavy borders.

## Typography
The system relies exclusively on **Inter** to maintain a systematic, neutral, and highly legible experience across all weights. 

- **Headlines:** Use Semi-Bold (600) for Headline-lg to create a strong information hierarchy.
- **Body:** Use Regular (400) for all long-form reading, ensuring a comfortable line height of 1.5x the font size.
- **Labels:** Medium (500) is preferred for buttons and navigational elements to ensure they stand out against body text.
- **Scale:** On desktop, use `headline-lg` for page titles and `title-lg` for card headers. `body-lg` is the default for most student-facing content to improve accessibility and readability.

## Layout & Spacing
This design system uses a **Fluid Grid** model with a maximum container width to ensure readability on ultra-wide monitors. 

- **Grid:** A 12-column grid is standard for desktop (1440px+), transitioning to 8 columns for smaller laptops. 
- **Margins:** Page-level horizontal margins are set to 48px to provide a "premium" sense of space.
- **Rhythm:** An 8px linear scale (with a 4px step for tight UI) governs all padding and margins. Vertical spacing between logical sections (e.g., Hero to Feature list) should use 48px or 64px to maintain an airy, student-friendly feel.

## Elevation & Depth
In accordance with Material 3, depth is primarily conveyed through **Tonal Layers** rather than heavy shadows.

- **Surface Levels:** The background is the lowest level. Content cards sit on `Surface Container Low`. Modals and floating action buttons sit on `Surface Container High`.
- **Shadows:** Shadows are used sparingly. When used, they are "Ambient Shadows"—soft, extremely diffused (20% blur-to-size ratio) with a 4% opacity black or a slight blue-tinted grey.
- **Interaction:** On hover, cards should lift slightly via a subtle increase in shadow spread and a shift to a lighter surface tone, providing tactile feedback to the student.

## Shapes
To ensure the platform feels "approachable" and "soft," the design system utilizes a **Rounded** shape language.

- **Standard Elements (8px):** Buttons, input fields, and small tags use a 0.5rem (8px) radius.
- **Containers (12px - 16px):** Content cards and navigation drawers use a larger `rounded-lg` (16px) radius to create a distinct, friendly containerization of information.
- **Pills:** Search bars and status indicators may use a fully rounded (pill) shape to denote a distinct functional class.

## Components
- **Buttons:** Follow the M3 "Filled" and "Outlined" styles. The primary button uses the brand blue (#1a73e8) with white text and an 8px corner radius.
- **Cards:** White or `Surface Container` background, 16px corner radius, and a 1px `Outline Variant` border. Avoid heavy drop shadows to keep the UI clean.
- **Input Fields:** Filled style with a thick bottom stroke or a full 8px-radius outline. Labels should use `label-md` and stay visible on focus.
- **Chips:** Used for "Career Interests" or "Skills." These should be 32px height with an 8px radius and a subtle background tint of the primary color.
- **Lists:** High-density lists are avoided. Instead, list items should have generous vertical padding (16px) and clear dividers or tonal separation.
- **Progress Indicators:** Use the Tertiary green for "Completed" steps in the orientation journey to evoke a sense of accomplishment.