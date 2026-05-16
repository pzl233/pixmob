from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_PATH = ROOT / "tmp" / "PixMob_IR" / "pixmob_ir_protocol.py"
OUTPUT_PATH = ROOT / "assets" / "ir" / "pixmob_x2_gen31_onstart_green.ir"
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
    green_full = 0xFF
    green_soft = 0x80

    def make_scene(name, note, green_value, attack, sustain, release):
        return (
            name,
            note,
            [
                pmir.CommandSetColor(
                    red=0x00,
                    green=green_value,
                    blue=0x00,
                    profile_id=0,
                    skip_display=True,
                ),
                pmir.CommandSetConfig(
                    on_start=True,
                    gst_enable=True,
                    profile_id_lo=0,
                    profile_id_hi=0,
                    is_random=False,
                    attack=attack,
                    sustain=sustain,
                    release=release,
                ),
            ],
        )

    candidates = [
        make_scene(
            "X2_ONSTART_GREEN_960_REL0",
            "Write profile 0 as green and set on-start single-profile scene with release=0.",
            green_full,
            pmir.Time.TIME_960_MS,
            pmir.Time.TIME_960_MS,
            pmir.Time.TIME_0_MS,
        ),
        make_scene(
            "X2_ONSTART_GREEN_2400_REL0",
            "Single-profile on-start green scene with slower attack/sustain and release=0.",
            green_full,
            pmir.Time.TIME_2400_MS,
            pmir.Time.TIME_2400_MS,
            pmir.Time.TIME_0_MS,
        ),
        make_scene(
            "X2_ONSTART_GREEN_3840_REL0",
            "Single-profile on-start green scene with maximum attack/sustain and release=0.",
            green_full,
            pmir.Time.TIME_3840_MS,
            pmir.Time.TIME_3840_MS,
            pmir.Time.TIME_0_MS,
        ),
        make_scene(
            "X2_ONSTART_GREEN_SOFT_960_REL0",
            "Same as 960/rel0 but with softer green intensity.",
            green_soft,
            pmir.Time.TIME_960_MS,
            pmir.Time.TIME_960_MS,
            pmir.Time.TIME_0_MS,
        ),
        make_scene(
            "X2_ONSTART_GREEN_960_REL480",
            "Single-profile on-start green scene with visible release back into the same profile cycle.",
            green_full,
            pmir.Time.TIME_960_MS,
            pmir.Time.TIME_960_MS,
            pmir.Time.TIME_480_MS,
        ),
        (
            "X2_ONSTART_GREEN_GST3840",
            "Set global sustain to 3840 ms first, then write single-profile green on-start scene.",
            [
                pmir.CommandSetColor(
                    red=0x00,
                    green=green_full,
                    blue=0x00,
                    profile_id=0,
                    skip_display=True,
                ),
                pmir.CommandSetGlobalSustainTime(
                    global_sustain=pmir.GlobalSustainTime.TIME_3840_MS
                ),
                pmir.CommandSetConfig(
                    on_start=True,
                    gst_enable=True,
                    profile_id_lo=0,
                    profile_id_hi=0,
                    is_random=False,
                    attack=pmir.Time.TIME_960_MS,
                    sustain=pmir.Time.TIME_960_MS,
                    release=pmir.Time.TIME_0_MS,
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
        "# PixMob X2 gen3.1 EEPROM on-start green candidates.",
        "# These entries write profile/config combinations intended to survive power cycling.",
        "# Test one candidate, then remove and reconnect the battery to see if the scene persists.",
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
