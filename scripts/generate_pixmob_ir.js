const fs = require("fs");
const path = require("path");

const SOURCE_PATH = path.resolve(
  __dirname,
  "..",
  "tmp",
  "pixmob-web-controller",
  "src",
  "IR",
  "effects.ts",
);
const OUTPUT_PATH = path.resolve(
  __dirname,
  "..",
  "assets",
  "ir",
  "pixmob_flipper.ir",
);

const FREQUENCY_HZ = 38000;
const DUTY_CYCLE = "0.330000";
const UNIT_MICROS = 694;
const COMMON_COLOR_IDS = [
  "RED",
  "GREEN",
  "BLUE",
  "MAGENTA",
  "YELLOW",
  "PINK",
  "ORANGE",
  "WHITISH",
  "TURQUOISE",
];

function readSource() {
  if (!fs.existsSync(SOURCE_PATH)) {
    throw new Error(`Missing source file: ${SOURCE_PATH}`);
  }

  return fs.readFileSync(SOURCE_PATH, "utf8");
}

function getSection(source, exportName, openChar, closeChar) {
  const exportToken = `export const ${exportName}`;
  const start = source.indexOf(exportToken);
  if (start === -1) {
    throw new Error(`Unable to locate export: ${exportName}`);
  }

  const equalsIndex = source.indexOf("=", start);
  if (equalsIndex === -1) {
    throw new Error(`Unable to locate assignment for ${exportName}`);
  }

  const openIndex = source.indexOf(openChar, equalsIndex);
  if (openIndex === -1) {
    throw new Error(`Unable to locate ${openChar} for ${exportName}`);
  }

  let depth = 0;
  for (let index = openIndex; index < source.length; index += 1) {
    const ch = source[index];
    if (ch === openChar) {
      depth += 1;
    } else if (ch === closeChar) {
      depth -= 1;
      if (depth === 0) {
        return source.slice(openIndex + 1, index);
      }
    }
  }

  throw new Error(`Unable to find matching ${closeChar} for ${exportName}`);
}

function parseNumberArray(block) {
  const matches = block.match(/\d+/g);
  if (!matches) {
    return [];
  }

  return matches.map((value) => Number(value));
}

function parseObjectArray(section) {
  const entryRegex =
    /\{\s*id:\s*"([^"]+)",\s*data:\s*\[([\s\S]*?)\],\s*label:/g;
  const entries = [];

  for (const match of section.matchAll(entryRegex)) {
    entries.push({
      id: match[1],
      bits: parseNumberArray(match[2]),
    });
  }

  return entries;
}

function parseSpecialEffects(section) {
  const entryRegex = /^\s*([A-Z0-9_]+):\s*\[([\s\S]*?)\],\s*$/gm;
  const entries = [];

  for (const match of section.matchAll(entryRegex)) {
    entries.push({
      id: match[1],
      bits: parseNumberArray(match[2]),
    });
  }

  return entries;
}

function bitsToTimings(bits) {
  if (!bits.length) {
    throw new Error("Cannot convert an empty bit array");
  }
  if (bits[0] !== 1) {
    throw new Error("Raw IR data must start with an ON duration");
  }

  const timings = [];
  let current = bits[0];
  let runLength = 1;

  for (let index = 1; index < bits.length; index += 1) {
    if (bits[index] === current) {
      runLength += 1;
    } else {
      timings.push(runLength * UNIT_MICROS);
      current = bits[index];
      runLength = 1;
    }
  }

  timings.push(runLength * UNIT_MICROS);
  return timings;
}

function toButton(name, bits) {
  return {
    name,
    timings: bitsToTimings(bits),
  };
}

function buildButtons(source) {
  const tailCodes = parseObjectArray(getSection(source, "tail_codes", "[", "]"));
  const colorEffects = parseObjectArray(
    getSection(source, "colorEffects", "[", "]"),
  );
  const specialEffects = parseSpecialEffects(
    getSection(source, "special_effects", "{", "}"),
  );

  const commonColorMap = new Map(
    colorEffects
      .filter((entry) => COMMON_COLOR_IDS.includes(entry.id))
      .map((entry) => [entry.id, entry]),
  );

  const buttons = [];
  for (const effect of colorEffects) {
    buttons.push(toButton(effect.id, effect.bits));
  }

  for (const effect of specialEffects) {
    buttons.push(toButton(effect.id, effect.bits));
  }

  for (const colorId of COMMON_COLOR_IDS) {
    const color = commonColorMap.get(colorId);
    if (!color) {
      continue;
    }

    for (const tail of tailCodes) {
      buttons.push(toButton(`${colorId}__${tail.id}`, [...color.bits, ...tail.bits]));
    }
  }

  return buttons;
}

function formatButton(button) {
  return [
    "#",
    `name: ${button.name}`,
    "type: raw",
    `frequency: ${FREQUENCY_HZ}`,
    `duty_cycle: ${DUTY_CYCLE}`,
    `data: ${button.timings.join(" ")}`,
  ].join("\n");
}

function main() {
  const source = readSource();
  const buttons = buildButtons(source);

  fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });

  const fileContent = [
    "Filetype: IR signals file",
    "Version: 1",
    ...buttons.map(formatButton),
    "#",
    "",
  ].join("\n");

  fs.writeFileSync(OUTPUT_PATH, fileContent, "utf8");
  console.log(`Generated ${buttons.length} buttons at ${OUTPUT_PATH}`);
}

main();
