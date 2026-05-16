# PixMob IR Exports

This repository contains PixMob infrared command exports derived from
[`HFO4/pixmob-web-controller`](https://github.com/HFO4/pixmob-web-controller).

## Files

- `assets/ir/pixmob_flipper.ir`: bulk-importable raw IR commands in Flipper IR
  file format
- `scripts/generate_pixmob_ir.js`: regenerates the `.ir` file from the upstream
  `effects.ts` data

## Notes

- Carrier frequency: `38 kHz`
- Timing unit: `694 us`
- Generated commands include base colors, special effects, and common
  color-plus-tail combinations
