# Automatic License Plate Recognition (ALPR) — Classical Morphology + OCR

> A lightweight ALPR pipeline that detects plates, enhances them with **morphological image processing**, then reads text with OCR. Designed for real‑time use on roadway footage; includes optional blacklist matching and visual overlays.

---

## 🎬 Demo (placeholder)

Paste a GitHub **user‑attachments** video URL on its own line and (optionally) keep the HTML tag below for autoplay on supported renderers.

```
VIDEO_DEMO_URL
```

<!-- Optional HTML embed for some markdown renderers -->

<video src="(https://github.com/user-attachments/assets/14b95fe0-854a-4f81-be28-ff56e1cd322f)" width="500" autoplay loop muted playsinline></video>

---

## 🔎 What this project does

1. **Detect** candidate license plates in each frame.
2. **Crop** the plate region and run a **morphological pipeline** to increase text contrast.
3. **OCR** the processed crop to get the alphanumeric plate string and **confidence**.
4. **Overlay** the text, confidence, and an optional **green/red box** if it matches a watchlist.
5. **Explainability:** show tiny thumbnails of each processing step next to the vehicle.

<div align="center">
  <img src="IMG_CLOSE_STACK_URL" width="500" alt="Close-up: stacked morphology thumbnails with OCR and confidence"/>
  <br/>
  <sub><b>Fig A.</b> Per‑frame explainability: thumbnails of the morphological steps (left), OCR text with confidence (center), and the plate ROI box (green when OK, red on hit).</sub>
</div>

<div align="center">
  <img src="IMG_MULTI_CAR_URL" width="500" alt="Multi‑vehicle scene with ALPR overlays"/>
  <br/>
  <sub><b>Fig B.</b> Multi‑vehicle scene — each detected plate is read and labeled with confidence.</sub>
</div>

<div align="center">
  <img src="IMG_STREET_FLAG_URL" width="500" alt="Street view with flagged and non‑flagged plates"/>
  <br/>
  <sub><b>Fig C.</b> Watchlist match example: non‑matches (green) vs a flagged plate (red).</sub>
</div>

---

## 🧠 Why morphology?

Modern OCR works best when the foreground characters are clearly separated from background. Road footage often suffers from glare, blur, and low contrast. A **classical morphology chain** (blur → threshold → dilate → invert) improves character strokes so OCR has an easier job.

At a high level:

* **Grayscale** converts to a single intensity channel.
* **Gaussian blur** reduces sensor noise and small texture.
* **Otsu threshold** picks a binary cut‑off that separates dark letters from bright plate background.
* **Dilation** connects broken character strokes and makes them more OCR‑friendly.
* **Invert** produces dark text on white (or vice‑versa) to match the OCR model’s expectations.

Mathematically, dilation of a binary image $X$ by a structuring element $S$ is the set operation
$ X \oplus S = \{\, x \mid (\hat S)_x \cap X \neq \emptyset \,\} ,$
which fattens bright components; thresholding seeks a level $\tau$ that maximizes between‑class variance (Otsu).

---

## 🧩 End‑to‑end pipeline

**Detector → ROI → Morphology → OCR → Post‑process.**

**1) Detection.** A lightweight one‑stage detector (e.g., a small YOLO variant) produces plate boxes $[x_1,y_1,x_2,y_2]$ and a class score per frame.
*Reference in code:* initialization and detector load (approx. `main.py` lines 7–14).

**2) ROI crop.** For each detection, crop the plate region and sanity‑check the size (ignore tiny boxes).
*Reference:* `main.py` lines \~61–66 and \~71–77 (ROI prep and thumbnail sizing).

**3) Morphological pipeline.** The function `morphological_pipeline(roi)` performs the steps listed in its docstring and returns a list of `(title, image)` snapshots.
*Reference:* `morphological_pipeline.py` lines 7–16 (overview); lines 27–40 (Otsu, dilate, invert).

**4) OCR.** The enhanced crop is sent to an OCR head to obtain the plate string and a confidence $c \in [0,1]$.
*Reference:* `main.py` mid‑section where the label string and confidence are composed and rendered.

**5) Post‑processing & overlays.**

* Watchlist (set lookup) → **red** box on match; otherwise **green**.
* Draw text in a high‑contrast banner above the box.
* Place thumbnails of the intermediate steps as a vertical strip near the vehicle.
  *Reference:* `main.py` lines \~86–107 (overlay layout, placement, and rendering), lines 108–118 (display loop & keyboard).

---

## ✍️ Pseudocode (conceptual)

```text
for each video frame:
  boxes = detector(frame)
  for b in boxes:
    roi = crop(frame, b)
    steps = morphological_pipeline(roi)  # [("Gray", I1), ("Blur", I2), ("Otsu", I3), ("Dilate", I4), ("Invert", I5)]
    text, conf = ocr(select_best(steps))
    color = RED if text in WATCHLIST else GREEN
    draw_banner(frame, text, conf, near=b)
    draw_box(frame, b, color)
    draw_thumbnails(frame, steps, column_near=b)
show(frame)
```

**Selecting the best crop.** In practice, the OCR score is evaluated on one or more of the processed variants and the best is taken. Heuristics: prefer the post‑dilation or inverted image; fall back to the raw crop if confidence is low.

---

## 📐 Practical tuning notes

* **Thresholding:** Otsu works well under consistent lighting; add adaptive thresholding (mean/gaussian) for nighttime glare.
* **Structuring element:** start with a 2×2 or 3×3 rectangle; too large will merge characters.
* **Text banner:** compute text size via `cv2.getTextSize` and draw a white rectangle behind for legibility.
* **Throughput:** thumbnail sizes (≈80×60) keep the explainer strip cheap while maintaining readability.
* **Blacklists:** store plate strings in an uppercase set; normalize OCR output by stripping spaces and hyphens.

---

## 🚧 Limitations & next steps

* Sensitive to **motion blur** and **plate glare**; add deblurring or exposure‑robust thresholding.
* Country‑specific fonts/layouts vary; extend with region‑aware OCR or a small language model for post‑correction.
* For multi‑camera setups, add simple tracking (IoU‑based) to stabilize labels across frames.

---

## Repository structure (brief)

* `main.py` — video loop, detection, overlays, thumbnails, watchlist logic.
* `morphological_pipeline.py` — the classical enhancement chain.
* `data/` — sample video(s), if any.

---

### Swap in your media links

Replace the placeholders below with GitHub user‑attachments (or repo‑local) links:

* <img width="268" height="256" alt="SCR-20250921-mjiq" src="https://github.com/user-attachments/assets/1ae88454-1fbf-4893-9395-ef175fa93a1a" />

* <img width="626" height="440" alt="SCR-20250921-mjne" src="https://github.com/user-attachments/assets/c45867d7-a45e-4050-a469-40c3cf4c436b" />

* <img width="640" height="263" alt="SCR-20250921-mjoo" src="https://github.com/user-attachments/assets/bd661eca-97d1-4e26-b833-01708ee8e631" />

All images above are rendered with `width="500"` to keep a clean, consistent look on GitHub pages.
