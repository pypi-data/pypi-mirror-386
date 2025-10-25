import os
import re
import json
import base64
import click
import io
import time
from pathlib import Path
from rich.console import Console
from PIL import Image

try:
    from google import genai
    from google.genai import types as genai_types
except Exception:  # pragma: no cover
    genai = None  # type: ignore
    genai_types = None  # type: ignore


def _encode_image(image_path: str) -> bytes:
    with open(image_path, "rb") as f:
        return f.read()


def _infer_mime_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext in (".png",):
        return "image/png"
    if ext in (".gif",):
        return "image/gif"
    if ext in (".webp",):
        return "image/webp"
    return "image/png"


def _build_indexed_path(sample_path: str, index: int) -> str:
    dirname = os.path.dirname(sample_path)
    filename = os.path.basename(sample_path)
    m = re.match(r"^(.*?)(\d+)(\.[^.]+)$", filename)
    if m:
        prefix, _, ext = m.groups()
        return os.path.join(dirname, f"{prefix}{index}{ext}")
    name, ext = os.path.splitext(filename)
    return os.path.join(dirname, f"{name}_{index}{ext}")


@click.command(help="Process images with Gemini to remove background and save transparent PNG + text.")
@click.option("-i", "--image", type=click.Path(exists=True), required=True, help="Path to an indexed image (e.g., main_1.jpg)")
@click.option(
    "-r",
    "--range",
    "ranges",
    nargs=2,
    type=int,
    required=False,
    help="Inclusive start and end indices to process. If omitted, processes the given image as-is.",
)
@click.option("-m", "--model", default="gemini-2.5-flash-image-preview", show_default=True, help="Gemini model name")
@click.option("--retries", default=0, show_default=True, type=int, help="Retry attempts on 429 quota errors")
@click.option("--retry-wait", default=None, type=int, help="Seconds to wait before retry; if omitted, uses server hint or backoff")
@click.option("--local-fallback/--no-local-fallback", default=True, show_default=True, help="On failure/quota, perform local background removal and save PNG")
@click.option("--white-threshold", default=245, show_default=True, type=int, help="0-255 threshold treating near-white as background when using local fallback")
def ocr(image: str, ranges: tuple[int, int] | None, model: str, retries: int, retry_wait: int | None, local_fallback: bool, white_threshold: int):
    console = Console()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        console.print(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) not set", style="bold red")
        raise click.Abort()
    if genai is None or genai_types is None:
        console.print("google-genai SDK is not installed", style="bold red")
        console.print("Add 'google-genai' to your dependencies and reinstall.")
        raise click.Abort()

    client = genai.Client(api_key=api_key)

    out_dir = Path("src") / "orc"
    out_dir.mkdir(parents=True, exist_ok=True)

    def _existing_index(path: str) -> int | None:
        fn = os.path.basename(path)
        m = re.match(r"^(.*?)(\d+)(\.[^.]+)$", fn)
        return int(m.group(2)) if m else None

    pairs: list[tuple[int, str]] = []
    if ranges and len(ranges) == 2:
        start, end = ranges
        for i in range(start, end + 1):
            pairs.append((i, _build_indexed_path(image, i)))
    else:
        idx = _existing_index(image) or 1
        pairs.append((idx, image))

    processed = 0
    for i, img_path in pairs:
        if not os.path.exists(img_path):
            console.print(
                f"Skipping missing image: {img_path}", style="yellow")
            continue
        try:
            img_bytes = _encode_image(img_path)
            mime = _infer_mime_type(img_path)
        except Exception as e:
            console.print(f"Failed to read {img_path}: {e}", style="bold red")
            continue

        # instruction = (
        #     "You are an expert image editor. Task: isolate the physics diagram only. "
        #     "Steps: (1) Detect the main diagram/graph region and crop tightly to its bounding box (no outer margins/padding). "
        #     "(2) Remove the background fully while preserving all labels, axes, ticks, grid/graph lines, and annotations. "
        #     "(3) Output a single transparent RGBA PNG (alpha channel) at the original resolution of the cropped region with a maximum margin of 5 pixels on each side. "
        #     "Do not stylize or redraw; only precise background removal and tight cropping."
        # )
        instruction = (
            "You are an expert image editor. Task: isolate the physics diagram only. "
            "Steps: (1) Detect the main diagram/graph region and crop tightly to its bounding box (no outer margins/padding). "
            "Ensure that no extra whitespace, margins, or padding remain. "
            "All labels, axes, ticks, grid/graph lines, and annotations must remain fully preserved. "
            "try to keep the image sharply focused and clear. "
        )

        attempt = 0
        while True:
            try:
                # Build parts with fallbacks if helper constructors are unavailable
                try:
                    text_part = genai_types.Part.from_text(text=instruction)
                except Exception:
                    try:
                        text_part = genai_types.Part(text=instruction)
                    except Exception:
                        text_part = instruction  # final fallback; SDK may coerce strings

                try:
                    image_part = genai_types.Part.from_bytes(
                        data=img_bytes, mime_type=mime)
                except Exception:
                    try:
                        blob = genai_types.Blob(mime_type=mime, data=img_bytes)
                        image_part = genai_types.Part(inline_data=blob)
                    except Exception:
                        image_part = {"inline_data": {
                            "mime_type": mime, "data": img_bytes}}

                parts = [text_part, image_part]
                contents = [genai_types.Content(role="user", parts=parts)]
                config = genai_types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"])

                collected_text: list[str] = []
                image_blobs: list[tuple[bytes, str]] = []

                for chunk in client.models.generate_content_stream(
                    model=model,
                    contents=contents,
                    config=config,
                ):
                    try:
                        if not getattr(chunk, "candidates", None):
                            continue
                        cand = chunk.candidates[0]
                        content = getattr(cand, "content", None)
                        if not content:
                            continue
                        for p in getattr(content, "parts", []) or []:
                            txt = getattr(p, "text", None)
                            if isinstance(txt, str) and txt.strip():
                                collected_text.append(txt)
                                continue
                            inline = getattr(p, "inline_data", None)
                            if inline and getattr(inline, "data", None) is not None:
                                data_buf = inline.data
                                if isinstance(data_buf, (bytes, bytearray)):
                                    data_bytes = bytes(data_buf)
                                elif isinstance(data_buf, str):
                                    try:
                                        data_bytes = base64.b64decode(data_buf)
                                    except Exception:
                                        data_bytes = data_buf.encode(
                                            "utf-8", errors="ignore")
                                else:
                                    continue
                                mime_out = getattr(
                                    inline, "mime_type", None) or "image/png"
                                image_blobs.append((data_bytes, str(mime_out)))
                    except Exception:
                        continue

                text = "\n".join(collected_text).strip()

                md_path = out_dir / f"problem_{i}.md"
                json_path = out_dir / f"problem_{i}.json"
                try:
                    md_path.write_text(text or "")
                    payload = {
                        "input": {"path": img_path, "mime": mime, "model": model, "index": i},
                        "text": text,
                        "images": [{"mime": m, "bytes": len(b)} for (b, m) in image_blobs],
                    }
                    with open(json_path, "w") as jf:
                        json.dump(payload, jf, ensure_ascii=False, indent=2)
                except Exception as e:
                    console.print(
                        f"Failed to save text/json for {img_path}: {e}", style="bold red")

                # Save images
                if image_blobs:
                    if len(image_blobs) == 1:
                        data, _ = image_blobs[0]
                        png_path = out_dir / f"problem_{i}.png"
                        try:
                            im = Image.open(io.BytesIO(data))
                            if im.mode != "RGBA":
                                im = im.convert("RGBA")
                            im.save(png_path, format="PNG")
                            # Quick transparency sanity check
                            try:
                                alpha = im.getchannel("A")
                                if not any(px < 255 for px in alpha.getdata()):
                                    console.print(
                                        f"Note: {png_path} has no transparency (alpha). Model may not have removed background.",
                                        style="yellow",
                                    )
                            except Exception:
                                pass
                            console.print(f"Wrote {png_path}", style="green")
                        except Exception:
                            with open(png_path, "wb") as pf:
                                pf.write(data)
                            console.print(
                                f"Wrote {png_path} (raw)", style="yellow")
                    else:
                        for idx_, (data, _) in enumerate(image_blobs, start=1):
                            png_path = out_dir / f"problem_{i}_{idx_}.png"
                            try:
                                im = Image.open(io.BytesIO(data))
                                if im.mode != "RGBA":
                                    im = im.convert("RGBA")
                                im.save(png_path, format="PNG")
                                try:
                                    alpha = im.getchannel("A")
                                    if not any(px < 255 for px in alpha.getdata()):
                                        console.print(
                                            f"Note: {png_path} has no transparency (alpha).", style="yellow"
                                        )
                                except Exception:
                                    pass
                                console.print(
                                    f"Wrote {png_path}", style="green")
                            except Exception:
                                with open(png_path, "wb") as pf:
                                    pf.write(data)
                                console.print(
                                    f"Wrote {png_path} (raw)", style="yellow")
                else:
                    # Fallback: no images returned; save input copy as PNG
                    try:
                        png_path = out_dir / f"problem_{i}.png"
                        im = Image.open(io.BytesIO(img_bytes))
                        if im.mode != "RGBA":
                            im = im.convert("RGBA")
                        im.save(png_path, format="PNG")
                        console.print(
                            f"Wrote {png_path} (input copy)", style="yellow")
                    except Exception as e:
                        console.print(
                            f"Failed to save input copy: {e}", style="yellow")

                processed += 1
                console.print(f"Wrote {md_path}", style="green")
                console.print(f"Wrote {json_path}")
                break  # success

            except Exception as e:
                s = str(e)
                is_quota = ("RESOURCE_EXHAUSTED" in s) or (
                    "429" in s) or ("quota" in s.lower())
                if is_quota and attempt < retries:
                    # Try to parse retry delay from message e.g. 'retryDelay': '49s'
                    if retry_wait is not None:
                        delay = retry_wait
                    else:
                        m = re.search(r"retryDelay['\"]?:\s*'?(\d+)s", s)
                        if m:
                            try:
                                delay = int(m.group(1))
                            except Exception:
                                delay = None
                        else:
                            delay = None
                    if delay is None:
                        delay = min(60, 10 * (attempt + 1))
                    console.print(
                        f"Quota hit; retrying in {delay}s (attempt {attempt+1}/{retries})", style="yellow")
                    time.sleep(delay)
                    attempt += 1
                    continue

                if local_fallback:
                    try:
                        png_path = out_dir / f"problem_{i}.png"
                        im = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                        datas = list(im.getdata())
                        new_data = []
                        T = max(0, min(255, int(white_threshold)))
                        for (r, g, b, a) in datas:
                            if r >= T and g >= T and b >= T:
                                new_data.append((r, g, b, 0))
                            else:
                                new_data.append((r, g, b, 255))
                        im.putdata(new_data)
                        im.save(png_path, format="PNG")

                        json_path = out_dir / f"problem_{i}.json"
                        payload = {
                            "input": {"path": img_path, "mime": mime, "model": model, "index": i},
                            "text": "",
                            "images": [{"mime": "image/png", "bytes": os.path.getsize(png_path)}],
                            "fallback": {"type": "local_background_removal", "white_threshold": T, "reason": s[:400]},
                        }
                        with open(json_path, "w") as jf:
                            json.dump(
                                payload, jf, ensure_ascii=False, indent=2)
                        console.print(
                            f"Used local fallback → {png_path}", style="yellow")
                        processed += 1
                        break
                    except Exception as le:
                        console.print(
                            f"Local fallback failed: {le}", style="bold red")

                console.print(
                    f"Gemini call failed for {img_path}: {e}", style="bold red")
                break

    console.print(f"✅ Processed {processed} image(s)")


if __name__ == "__main__":
    ocr()
