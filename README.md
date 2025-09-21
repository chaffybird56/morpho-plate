# Automatic License Plate Recognition (ALPR) — Classical Morphology + OCR

> A lightweight ALPR pipeline that detects plates, enhances them with **morphological image processing**, and reads text with OCR. Built to run in real‑time on roadway footage, with optional blacklist (watchlist) matching and clear visual overlays.

---

## 🎬 Demo

Paste the GitHub attachment link to the demo video on its own line (GitHub will render an inline player):

[https://github.com/user-attachments/assets/14b95fe0-854a-4f81-be28-ff56e1cd322f](https://github.com/user-attachments/assets/14b95fe0-854a-4f81-be28-ff56e1cd322f)

<sub>Tip: GitHub sizes video players automatically. To keep the page compact, a `<details>` block can be used to collapse the player if desired.</sub>

---

## 🔎 What this project does — at a glance

1. **Detect** candidate license plates in each frame (one‑stage CNN detector).
2. **Crop** each plate region and run a **morphology pipeline** to boost text contrast.
3. **OCR** the processed crop to obtain the plate string and a **confidence**.
4. **Overlay** the label, confidence, and a **green/red** ROI box (red on watchlist hit).
5. **Explainability:** draw tiny thumbnails of each processing step next to the vehicle.

<div align="left">
  <img src="https://github.com/user-attachments/assets/1ae88454-1fbf-4893-9395-ef175fa93a1a" width="400" alt="Close-up: stacked morphology thumbnails with OCR and confidence"/>
  <br/>
  <sub><b>Fig A.</b> Per‑frame explainability: thumbnails of the morphological steps (left), OCR text with confidence (center), and the plate ROI box (green when OK, red on hit).</sub>
</div>

<div align="center">
  <img src="https://github.com/user-attachments/assets/c45867d7-a45e-4050-a469-40c3cf4c436b" width="400" alt="Multi‑vehicle scene with ALPR overlays"/>
  <br/>
  <sub><b>Fig B.</b> Multi‑vehicle scene — each detected plate is read and labeled with confidence.</sub>
</div>

<div align="center">
  <img src="https://github.com/user-attachments/assets/bd661eca-97d1-4e26-b833-01708ee8e631" width="400" alt="Street view with flagged and non‑flagged plates"/>
  <br/>
  <sub><b>Fig C.</b> Watchlist match example: non‑matches (green) vs a flagged plate (red).</sub>
</div>

---

## 🧠 Why classical morphology before OCR?

Traffic footage often contains **glare**, **motion blur**, and **low contrast** between characters and the plate background. Modern OCR is far more reliable when characters are clearly separated from background. The pipeline therefore performs a short sequence of operations on each plate crop:

* **Grayscale** → remove color variation.
* **Gaussian blur** → reduce sensor noise/fine texture.
* **Otsu threshold** → pick a global binary threshold $\tau$ that maximizes between‑class variance, isolating characters from the plate field.
* **Dilation** → connect broken strokes using a small rectangular structuring element (e.g., 2×2 or 3×3), thickening characters just enough for OCR.
* **Invert** → ensure the foreground/background polarity matches what the OCR model expects.

**Mathematical note.** For a binary image $X$ and structuring element $S$, dilation is

$$
X \oplus S = \{\, x\;|\; (\hat S)_x \cap X \neq \emptyset \,\},
$$

which fatten bright components (character strokes). Otsu’s method chooses $\tau$ to maximize the between‑class variance of pixel intensities.

---

## 🧩 End‑to‑end pipeline (concept)

**Detector → ROI → Morphology → OCR → Post‑process.**

**1) Detection.** A compact one‑stage detector (configured in code as a YOLO‑style model) outputs plate bounding boxes $[x_1,y_1,x_2,y_2])$ with a class score. The detector is initialized once at startup.

**2) ROI crop.** Each box is sanity‑checked (aspect ratio / minimum size) and cropped. Very small crops are skipped to avoid spurious OCR.

**3) Morphological enhancement.** The function `morphological_pipeline(roi)` returns a list of labeled snapshots: `("Gray", I₁)`, `("Blur", I₂)`, `("Otsu", I₃)`, `("Dilate", I₄)`, `("Invert", I₅)`. These are also used to render the explainer thumbnails in Fig A.

**4) OCR.** The enhanced crop is read by the OCR head (provided through the ALPR wrapper). The output is an uppercase alphanumeric string and a confidence $c \in [0,1]$.

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

> Selection policy: OCR is evaluated on the post‑dilation or inverted image; if confidence is low, the raw crop is tried as fallback.

---

## 🧰 Practical guidance & tuning

* **Thresholding:** Otsu works well for daytime clips. Under harsh glare or night scenes, adaptive thresholding (mean/gaussian) can replace or complement Otsu.
* **Structuring element:** Start with 2×2 or 3×3. Over‑dilation can merge neighboring characters (false merges); under‑dilation leaves gaps.
* **Text banner legibility:** Measure text size via `cv2.getTextSize` and draw a white rectangle behind the text to ensure readability across backgrounds.
* **Throughput:** Keep thumbnail sizes small (≈80×60) to retain real‑time FPS while still providing explainability.
* **Watchlist:** Normalize OCR output by uppercasing and stripping spaces/hyphens before lookup.

---

## ✅ What to expect (typical results)

* On clear, forward‑facing shots: high read rates with confidences $>0.9$; stable overlays (Fig B).
* On low‑contrast plates: the morphology stage typically raises OCR confidence by connecting broken strokes (Fig A).
* On a watchlist hit: the ROI turns red and the label remains; false alarms are rare when confidence is high (Fig C).

**Limitations.** Motion blur and severe glare degrade detection and OCR; plate formats vary by region; stacked characters or non‑Latin scripts require specialized OCR. Adding basic object tracking (IoU‑based) stabilizes labels across frames.

---

## 🗂️ Repository (brief)

* `main.py` — video loop, detector inference, overlays, thumbnails, watchlist logic.
* `morphological_pipeline.py` — the classical enhancement chain described above.
* `data/` — sample clip(s) if provided.

**Ethics & privacy.** ALPR must be used in accordance with local law and organizational policy. Consider blurring faces/vehicles outside the ROI in demo footage.

---

## License

MIT — see `LICENSE`.
