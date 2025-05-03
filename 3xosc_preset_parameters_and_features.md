# 3x Osc Preset Parameters & Features (for Automation)

This document lists additional parameters and features you can support for FL Studio's 3x Osc preset automation, with confidence levels and mapping strategies.

---

## 1. Oscillator Mix Levels
- **Already mapped:** `mix_osc1`, `mix_osc2`, `mix_osc3`
- Control the blend of each oscillator in the output.

## 2. Oscillator Volume, Phase, Detune
- **Already mapped:** `oscX_volume`, `oscX_phase`, `oscX_detune`
- Key for shaping the sound and stereo image.

## 3. Oscillator Pan
- **Possible to map:** There is a pan slider for each oscillator in the UI.
- **How to find:** Compare .fst files with only pan changed to find the offset.

## 4. Global Phase Randomization
- **UI control:** The "PHASE RAND" knob at the bottom.
- **How to find:** Save .fst files with different phase randomization settings and compare.

## 5. AM OSC 3 (Amplitude Modulation)
- **UI control:** "AM OSC 3" button at the bottom left.
- **How to find:** Save .fst files with this toggled on/off and compare.

## 6. HQ (High Quality) Toggle
- **UI control:** "HQ" button at the bottom.
- **How to find:** Save .fst files with HQ on/off and compare.

## 7. Global Volume
- **UI control:** The master volume knob.
- **How to find:** Save .fst files with different master volume and compare.

---

## How to Add More Parameters

1. Create .fst files with only one parameter changed at a time.
2. Use `xxd` or a hex editor to compare the files and find the offset for each parameter.
3. Add the new offsets to your `OSC_OFFSETS` mapping.
4. Update the AI prompt to include the new parameters.
5. Update the encoder to write the new values.

---

## Features You Could Add

- **Randomize Preset:** Generate random values for all mapped parameters.
- **Preset Variations:** Generate multiple presets with slight variations.
- **Preset Preview:** Play a short sound using the generated preset (requires DAW scripting or integration).
- **Batch Export:** Generate a batch of presets from a single prompt.

---

## Summary Table

| Parameter/Feature      | Confidence | How to Add/Find         |
|------------------------|------------|-------------------------|
| Oscillator Pan         | High       | Compare .fst files      |
| Phase Randomization    | High       | Compare .fst files      |
| AM OSC 3 Toggle        | High       | Compare .fst files      |
| HQ Toggle              | High       | Compare .fst files      |
| Global Volume          | High       | Compare .fst files      |
| Batch/Random Presets   | High       | Code feature            |

---

**Tip:** If you want to map more offsets, provide .fst files with those parameters changed and analyze them with `xxd` or a hex editor. 