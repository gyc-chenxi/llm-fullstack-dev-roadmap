import argparse
from pathlib import Path
from PIL import Image, ImageDraw

def parse_box(s: str):
    parts = [int(x.strip()) for x in s.split(",")]
    if len(parts) != 4:
        raise ValueError("--box must be x1,y1,x2,y2")
    return tuple(parts)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--box", required=True, help="x1,y1,x2,y2")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path).convert("RGB")
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle(parse_box(args.box), fill=255)

    mask.save(output_path)
    print(f"✅ mask saved: {output_path}")

if __name__ == "__main__":
    main()
