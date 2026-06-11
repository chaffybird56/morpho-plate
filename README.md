# Automatic License Plate Recognition (ALPR) — Classical Morphology + OCR

> A lightweight ALPR pipeline that detects plates, enhances them with **morphological image processing**, and reads text with OCR. Built to run in real‑time on roadway footage, with optional blacklist (watchlist) matching and clear visual overlays!

---

## 🎬 Demo

[https://github.com/user-attachments/assets/14b95fe0-854a-4f81-be28-ff56e1cd322f](https://github.com/user-attachments/assets/14b95fe0-854a-4f81-be28-ff56e1cd322f)

---

## 🔎 What this project does — at a glance

1. **Detect** candidate license plates in each frame (one‑stage CNN detector).
2. **Crop** each plate region and run a **morphology pipeline** to boost text contrast.
3. **OCR** the processed crop to obtain the plate string and a **confidence**.
4. **Overlay** the label, confidence, and a **green/red** ROI box (red on watchlist hit).
5. **Explainability:** draw tiny thumbnails of each processing step next to the vehicle.

<div align="left">
  <img src="https://github.com/user-attachments/assets/1ae88454-1fbf-4893-9395-ef175fa93a1a" width="500" alt="Close-up: stacked morphology thumbnails with OCR and confidence"/>
  <br/>
  <sub><b>Fig A.</b> Per‑frame explainability: thumbnails of the morphological steps.</sub>
</div>

<div align="left">
  <img src="https://github.com/user-attachments/assets/c45867d7-a45e-4050-a469-40c3cf4c436b" width="500" alt="Multi‑vehicle scene with ALPR overlays"/>
  <br/>
  <sub><b>Fig B.</b> Multi‑vehicle scene — each detected plate is read and labeled with confidence.</sub>
</div>

<div align="left">
  <img src="https://github.com/user-attachments/assets/bd661eca-97d1-4e26-b833-01708ee8e631" width="500" alt="Street view with flagged and non‑flagged plates"/>
  <br/>
  <sub><b>Fig C.</b> Watchlist match example: non‑matches (green) vs a flagged plate (red).</sub>
</div>

---

## 🧠 Why classical morphology before OCR?

Traffic footage often contains **glare**, **motion blur**, and **low contrast** between characters and the plate background. OCR is far more reliable when characters are clearly separated from background. The pipeline therefore performs a short sequence on each plate crop:

* **Grayscale** → remove color variation.
* **Gaussian blur** → reduce sensor noise/fine texture.
* **Otsu threshold** → pick a global binary threshold that best splits foreground letters from background.
* **Dilation** → connect broken strokes with a small rectangular structuring element (2×2 or 3×3).
* **Invert** → ensure polarity matches what the downstream OCR expects.

### Mathematical view, with plain‑English meaning

**Otsu’s threshold (global).**  For a threshold \$\tau\$, let \$\omega\_0(\tau)\$ and \$\omega\_1(\tau)\$ be the fractions of pixels classified as background and foreground; \$\mu\_0(\tau)\$ and \$\mu\_1(\tau)\$ their mean intensities; and \$\mu\$ the overall mean. Otsu chooses

$$
\tau^* = \arg\max_\tau\; \sigma_b^2(\tau),\quad\text{where}\quad \sigma_b^2(\tau)=\omega_0(\tau)\,\omega_1(\tau)\,\big(\mu_0(\tau)-\mu_1(\tau)\big)^2.
$$

**What this says:** among all possible cuts, pick the one that makes the two groups of pixels (text vs. plate) as far apart in brightness as possible. Maximizing between‑class variance is equivalent to maximizing separability, which increases OCR legibility.

**Binary dilation.** For a binary image \$X\$ and a structuring element \$S\$,

$$
X \oplus S = \{\, x\;\mid\; (\hat S)_x \cap X \neq \emptyset \,\}.
$$

**What this says:** slide the (reflected) shape \$\hat S\$ across the image; a pixel becomes white if \$\hat S\$ touches any white pixel of \$X\$. Practically, this **fattens** character strokes so the OCR sees continuous letters instead of broken ones.

**Binary erosion.**

$$
X \ominus S = \{\, x\;\mid\; S_x \subseteq X \,\}.
$$

**What this says:** a pixel stays white only if the entire structuring element fits inside the white region. Erosion **shrinks** shapes and removes small specks.

**Opening and closing.**

$$
X \circ S = (X \ominus S) \oplus S,\qquad X \bullet S = (X \oplus S) \ominus S.
$$

**What this says:** opening (erode then dilate) removes tiny bright noise while preserving object shape; closing (dilate then erode) fills tiny dark holes and connects narrow gaps. Either can be swapped in for the single dilation step depending on footage quality.

**Morphological gradient (edge emphasis).**

$$
\nabla_S X = (X \oplus S) - (X \ominus S).
$$

**What this says:** take the difference between a fattened and a shrunken version of the image; the result highlights **edges**. On plates, it accentuates character boundaries before OCR.

---

## 🧩 End‑to‑end pipeline (concept)

**Detector → ROI → Morphology → OCR → Post‑process.**

**1) Detection.** A compact one‑stage detector outputs plate boxes $\[x\_1, y\_1, x\_2, y\_2]\$ and a class score per frame (initialized once at startup).

**2) ROI crop.** Each box is sanity‑checked (aspect ratio / minimum size) and cropped. Very small crops are skipped to avoid spurious OCR.

**3) Morphological enhancement.** `morphological_pipeline(roi)` returns a list of labeled snapshots: `(Gray, I₁)`, `(Blur, I₂)`, `(Otsu, I₃)`, `(Dilate, I₄)`, `(Invert, I₅)`. These are also used to render the explainer thumbnails in Fig A.

**4) OCR.** The enhanced crop is read by the OCR head. The output is an uppercase alphanumeric string and a confidence \$c \in \[0,1]\$.

**5) Post‑processing & overlays.** The label and confidence are drawn in a legible banner above the box; the box is **green** by default and turns **red** if the plate string appears in a watchlist set. A vertical strip of thumbnails (from step 3) is placed near the vehicle for quick debugging.

**High‑level pseudocode**

```text
for each video frame:
  boxes = detector(frame)
  for b in boxes:
    roi = crop(frame, b)
    steps = morphological_pipeline(roi)   # [Gray, Blur, Otsu, Dilate, Invert]
    text, conf = ocr(select_best(steps))  # evaluate OCR on one/two variants
    color = RED if text in WATCHLIST else GREEN
    draw_banner(frame, text, conf, near=b)
    draw_box(frame, b, color)
    draw_thumbnails(frame, steps, column_near=b)
show(frame)
```

> **Selecting the best variant.** Confidence is evaluated on one or more processed snapshots (often the post‑dilation or inverted image); if low, fall back to the raw crop.

---

## 🧰 Practical guidance & tuning

* **Thresholding:** Otsu works well for daytime clips. Under harsh glare or night scenes, adaptive thresholding (mean/gaussian) can replace or complement Otsu.
* **Structuring element:** Start with 2×2 or 3×3. Over‑dilation can merge neighboring characters; under‑dilation leaves gaps.
* **Text banner legibility:** Measure text size via `cv2.getTextSize` and draw a white rectangle behind the text to ensure readability across backgrounds.
* **Throughput:** Keep thumbnail sizes small (≈80×60) to retain real‑time FPS while still providing explainability.
* **Watchlist:** Normalize OCR output by uppercasing and stripping spaces/hyphens before lookup.

---

## ✅ What to expect (typical results)

* On clear, forward‑facing shots: high read rates with confidences \$>0.9\$; stable overlays (Fig B).
* On low‑contrast plates: the morphology stage typically raises OCR confidence by connecting broken strokes (Fig A).
* On a watchlist hit: the ROI turns red and the label remains; false alarms are rare when confidence is high (Fig C).

**Limitations.** Motion blur and severe glare degrade detection and OCR; plate formats vary by region; stacked characters or non‑Latin scripts require specialized OCR. Adding simple tracking (IoU‑based) stabilises labels across frames.

---

## 🚀 Quick start

```bash
git clone https://github.com/chaffybird56/morpho-plate.git
cd morpho-plate
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Place a test clip at data/test1.mp4, then run:
morphoplate data/test1.mp4 -w config/watchlist.example.txt

# Save annotated output without a preview window:
morphoplate data/test1.mp4 -w config/watchlist.example.txt -o output/annotated.mp4 --no-display
```

For development (tests, coverage):

```bash
pip install -e ".[dev]"
pytest
```

---

## 🗂️ Repository layout

```
morphoplate/
├── alpr/          # fast-alpr wrapper (detection + OCR)
├── morphology/    # classical enhancement chain (Gray → Blur → Otsu → Dilate → Invert)
├── viz/           # overlays and morphology thumbnails
├── config.py      # Settings dataclass
├── watchlist.py   # plate normalization and file loader
├── pipeline.py    # VideoPipeline orchestrator
└── cli.py         # morphoplate CLI entry point
config/
└── watchlist.example.txt
tests/             # unit tests (no GPU / video required)
```

**Ethics & privacy.** ALPR must be used in accordance with local law and organizational policy. Consider blurring faces/vehicles outside the ROI in demo footage.

---

## License

MIT — see `LICENSE`.
