# Prompting

GPT Image 2 responds best to concrete visual briefs. Prefer structured prompts over short slogans.

## Prompt Shape

```text
Create [asset type] for [audience/use].

Subject:
- ...

Composition:
- ...

Style and rendering:
- ...

Lighting and camera:
- ...

Text in image:
- Exact text: "..."
- Language: ...
- Placement: ...

Constraints:
- ...

Output:
- Aspect ratio/size: ...
- Quality target: ...
```

## Ask One Useful Question

Ask only when missing information would change the image materially. Examples:

- Product image: "Should the product be on pure white ecommerce background or in a lifestyle scene?"
- Poster: "What exact text must appear on the poster?"
- Character: "Should identity match a reference image exactly, or is it only style inspiration?"
- UI mockup: "Is this for mobile, desktop, or a marketing screenshot?"

If the user says "you decide", choose sensible defaults and state them briefly.

## Template Starters

### Product Studio

```text
Create a high-end studio product photograph of [product] for [brand/use].
Use a clean [background], realistic materials, accurate product geometry, crisp edges, and controlled reflections.
Camera: [angle], [lens feel], product centered with subtle shadow.
Lighting: [softbox/rim/key] lighting, premium commercial retouching.
Constraints: no extra text, no fake logos, no distorted product shape.
```

### Poster / Campaign Key Visual

```text
Create a professional campaign key visual for [topic/product/event].
Main visual: [subject/action].
Mood: [mood].
Layout: strong focal point, clean hierarchy, generous whitespace, print-ready composition.
Text: exact headline "[headline]" and optional subtext "[subtext]"; keep text legible and correctly spelled.
Style: [photoreal/editorial/illustration/3D/etc.].
```

### UI Mockup

```text
Create a polished [mobile/desktop] UI mockup for [app/product].
Screen content: [key sections].
Visual system: [colors, typography feel, density].
Use realistic interface details, coherent spacing, consistent icons, and readable text.
Do not include browser chrome unless requested.
```

### Reference Image Edit

```text
Edit the provided image. Preserve [identity/product shape/composition/pose/lighting] exactly.
Change only [target change].
Match perspective, shadows, reflections, and color temperature.
Avoid changing [protected elements].
```

### Diagram / Infographic

```text
Create a clear professional infographic explaining [topic].
Structure: [steps/sections].
Visual language: clean vector-like diagram, readable labels, consistent arrows, restrained color palette.
Text labels must be short and spelled exactly.
Avoid clutter; make hierarchy obvious.
```

## Quality Rules

- Exact text: keep it short; generated text can still fail. For critical copy, generate a clean image with reserved text areas and add final text in a design tool.
- Faces and brand identity: use reference images when exact continuity matters.
- Complex diagrams: request fewer labels and larger type.
- Multi-panel outputs: specify panel count, order, and repeated character/product invariants.
- For professional delivery, run one draft at lower cost, then one high-quality final.

## Negative Prompting

Use direct constraints instead of long negative lists. Good:

```text
No watermark, no extra logo, no misspelled text, no additional people, preserve the original product shape.
```

Avoid overloading the prompt with dozens of unrelated negatives.
