import argparse
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--low", type=int, default=100)
    parser.add_argument("--high", type=int, default=200)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path).convert("RGB")
    arr = np.array(img)
    edges = cv2.Canny(arr, args.low, args.high)
    edges_rgb = np.stack([edges, edges, edges], axis=2)

    Image.fromarray(edges_rgb).save(output_path)
    print(f"✅ canny saved: {output_path}")

if __name__ == "__main__":
    main()
