# Green Keepalive Test Plan

Use the original app and keep the color fixed to `GREEN`.

The goal is to find the lowest resend rate that still looks continuously on.

## Suggested tests

1. `BPM = 10`, `duration = 120s`
2. `BPM = 15`, `duration = 180s`
3. `BPM = 20`, `duration = 180s`
4. `BPM = 30`, `duration = 300s`
5. `BPM = 40`, `duration = 300s`

## Resend intervals

- `10 BPM` = every `6s`
- `15 BPM` = every `4s`
- `20 BPM` = every `3s`
- `30 BPM` = every `2s`
- `40 BPM` = every `1.5s`

## What to watch for

- If the wristband turns off between sends, increase BPM.
- If each resend causes an obvious re-trigger flash, decrease BPM.
- The best setting is the lowest BPM that still looks continuously on.
