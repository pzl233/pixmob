from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_PATH = ROOT / "tmp" / "PixMob_IR" / "pixmob_ir_protocol.py"
OUTPUT_PATH = ROOT / "assets" / "ir" / "pixmob_x2_gen31_steady_green.ir"
UNIT_US = 694
INTER_COMMAND_ZERO_UNITS = 3


def load_protocol_module():
    spec = importlib.util.spec_from_file_location("pixmob_ir_protocol", PROTOCOL_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def bits_to_raw_timings(bits):
    if not bits or bits[0] != 1:
        raise ValueError("IR bit stream must be non-empty and start with 1")

    timings = []
    current = bits[0]
    run_length = 1

    for bit in bits[1:]:
        if bit == current:
            run_length += 1
        else:
            timings.append(run_length * UNIT_US)
            current = bit
            run_length = 1

    timings.append(run_length * UNIT_US)
    return timings


def merge_bit_sequences(*bit_sequences):
    merged = []
    for index, bits in enumerate(bit_sequences):
        if index > 0:
            merged.extend([0] * INTER_COMMAND_ZERO_UNITS)
        merged.extend(bits)
    return merged


def build_candidates(pmir):
    green_soft = 0x3F
    green_full = 0xFF
    green_mid = 0x80

    same_cfg_960 = pmir.CommandSetConfig(
        on_start=True,
        gst_enable=True,
        profile_id_lo=0,
        profile_id_hi=0,
        is_random=False,
        attack=pmir.Time.TIME_960_MS,
        sustain=pmir.Time.TIME_960_MS,
        release=pmir.Time.TIME_0_MS,
    )
    same_cfg_2400 = pmir.CommandSetConfig(
        on_start=True,
        gst_enable=True,
        profile_id_lo=0,
        profile_id_hi=0,
        is_random=False,
        attack=pmir.Time.TIME_2400_MS,
        sustain=pmir.Time.TIME_2400_MS,
        release=pmir.Time.TIME_0_MS,
    )

    candidates = [
        (
            "X2_STEADY_GREEN_SOFT_960",
            "Single-trigger same-color indefinitely pattern, lower green intensity.",
            [
                pmir.CommandSetColor(red=0x00, green=green_soft, blue=0x00, profile_id=0, skip_display=True),
                same_cfg_960,
            ],
        ),
        (
            "X2_STEADY_GREEN_FULL_960",
            "Single-trigger same-color indefinitely pattern, full green intensity.",
            [
                pmir.CommandSetColor(red=0x00, green=green_full, blue=0x00, profile_id=0, skip_display=True),
                same_cfg_960,
            ],
        ),
        (
            "X2_STEADY_GREEN_FULL_2400",
            "Same-color indefinitely pattern with slower attack/sustain timings.",
            [
                pmir.CommandSetColor(red=0x00, green=green_full, blue=0x00, profile_id=0, skip_display=True),
                same_cfg_2400,
            ],
        ),
        (
            "X2_STEADY_GREEN_GST3840",
            "Same-color indefinitely pattern with global sustain set to 3840 ms first.",
            [
                pmir.CommandSetColor(red=0x00, green=green_full, blue=0x00, profile_id=0, skip_display=True),
                pmir.CommandSetGlobalSustainTime(global_sustain=pmir.GlobalSustainTime.TIME_3840_MS),
                same_cfg_960,
            ],
        ),
        (
            "X2_BACKGROUND_GREEN_DISPLAY",
            "Store green as background and display immediately.",
            [
                pmir.CommandSetColor(
                    red=0x00,
                    green=green_full,
                    blue=0x00,
                    is_background=True,
                    skip_display=False,
                ),
            ],
        ),
        (
            "X2_BACKGROUND_GREEN_TRIGGER",
            "Set green background silently, then trigger a short green effect that may settle on background.",
            [
                pmir.CommandSetColor(
                    red=0x00,
                    green=green_full,
                    blue=0x00,
                    is_background=True,
                    skip_display=True,
                ),
                pmir.CommandSingleColorExt(
                    red=0x00,
                    green=green_full,
                    blue=0x00,
                    attack=pmir.Time.TIME_0_MS,
                    sustain=pmir.Time.TIME_96_MS,
                    release=pmir.Time.TIME_32_MS,
                ),
            ],
        ),
        (
            "X2_BACKGROUND_GREEN_TRIGGER_480",
            "Set green background silently, then trigger a longer green effect with visible release back to background.",
            [
                pmir.CommandSetColor(
                    red=0x00,
                    green=green_full,
                    blue=0x00,
                    is_background=True,
                    skip_display=True,
                ),
                pmir.CommandSingleColorExt(
                    red=0x00,
                    green=green_mid,
                    blue=0x00,
                    attack=pmir.Time.TIME_32_MS,
                    sustain=pmir.Time.TIME_480_MS,
                    release=pmir.Time.TIME_480_MS,
                ),
            ],
        ),
        (
            "X2_BACKGROUND_GREEN_TRIGGER_960",
            "Set green background silently, then trigger a longer green effect with 960 ms sustain.",
            [
                pmir.CommandSetColor(
                    red=0x00,
                    green=green_full,
                    blue=0x00,
                    is_background=True,
                    skip_display=True,
                ),
                pmir.CommandSingleColorExt(
                    red=0x00,
                    green=green_mid,
                    blue=0x00,
                    attack=pmir.Time.TIME_32_MS,
                    sustain=pmir.Time.TIME_960_MS,
                    release=pmir.Time.TIME_480_MS,
                ),
            ],
        ),
        (
            "X2_BACKGROUND_GREEN_RELEASE0",
            "Set green background silently, then trigger a green effect with release=0 to try to latch current color.",
            [
                pmir.CommandSetColor(
                    red=0x00,
                    green=green_full,
                    blue=0x00,
                    is_background=True,
                    skip_display=True,
                ),
                pmir.CommandSingleColorExt(
                    red=0x00,
                    green=green_full,
                    blue=0x00,
                    attack=pmir.Time.TIME_32_MS,
                    sustain=pmir.Time.TIME_480_MS,
                    release=pmir.Time.TIME_0_MS,
                ),
            ],
        ),
        (
            "X2_BACKGROUND_GREEN_REPEAT5",
            "Set green background silently, then repeat a green effect several times before returning to background.",
            [
                pmir.CommandSetColor(
                    red=0x00,
                    green=green_full,
                    blue=0x00,
                    is_background=True,
                    skip_display=True,
                ),
                pmir.CommandSetRepeatDelayTime(repeat_delay=pmir.Time.TIME_480_MS),
                pmir.CommandSetRepeatCount(repeat_count=5),
                pmir.CommandSingleColorExt(
                    red=0x00,
                    green=green_mid,
                    blue=0x00,
                    attack=pmir.Time.TIME_32_MS,
                    sustain=pmir.Time.TIME_480_MS,
                    release=pmir.Time.TIME_480_MS,
                    enable_repeat=True,
                ),
            ],
        ),
    ]

    results = []
    for name, note, commands in candidates:
        merged_bits = merge_bit_sequences(*(command.encode() for command in commands))
        results.append(
            {
                "name": name,
                "note": note,
                "timings": bits_to_raw_timings(merged_bits),
            }
        )
    return results


def write_ir_file(candidates):
    lines = [
        "Filetype: IR signals file",
        "Version: 1",
        "#",
        "# PixMob X2 gen3.1 single-trigger steady-green candidates.",
        "# These entries combine one or more protocol commands into a single raw send.",
        "# Start with the STEADY entries before trying the BACKGROUND entries.",
    ]

    for candidate in candidates:
        lines.extend(
            [
                "#",
                f"# {candidate['note']}",
                f"name: {candidate['name']}",
                "type: raw",
                "frequency: 38000",
                "duty_cycle: 0.330000",
                "data: " + " ".join(str(value) for value in candidate["timings"]),
            ]
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    pmir = load_protocol_module()
    candidates = build_candidates(pmir)
    write_ir_file(candidates)
    print(f"Generated {len(candidates)} candidates at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
