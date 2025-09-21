# Automatic License Plate Recognition (ALPR) — Classical Morphology + OCR

> A lightweight ALPR pipeline that detects plates, enhances them with **morphological image processing**, and reads text with OCR. Built for real‑time roadway footage, with optional blacklist (watchlist) matching and clear overlays.

---

## 🎬 Demo

Paste the GitHub attachment link to the demo video on its own line (GitHub will render an inline player):

[https://github.com/user-attachments/assets/14b95fe0-854a-4f81-be28-ff56e1cd322f](https://github.com/user-attachments/assets/14b95fe0-854a-4f81-be28-ff56e1cd322f)

---

## 🔎 What this project does — at a glance

1. **Detect** candidate license plates in each frame (compact one‑stage CNN).
2. **Crop** each plate region and run a short **morphology pipeline** to boost text contrast.
3. **OCR** the processed crop to obtain the plate string and a **confidence**.
4. **Overlay** the label, confidence, and a **green/red** ROI box (red on watchlist hit).
5. **Explainability:** draw tiny thumbnails of each processing step next to the vehicle.

<div align="center">
  <img src="https://github.com/user-attachments/assets/c45867d7-a45e-4050-a469-40c3cf4c436b" width="500" alt="Multi‑vehicle scene with ALPR overlays"/>
  <br/>
  <sub><b>Fig B.</b> Multi‑vehicle scene — each detected plate is read and labeled with confidence.</sub>
</div>

---

## 🧠 Classical morphology before OCR — the full story

Traffic footage often exhibits **glare**, **motion blur**, and **low contrast**. OCR models are much more reliable when characters are cleanly separated from background. The pipeline therefore applies a small sequence of contrast‑shaping operations to each plate crop.

Let the plate crop be an image $I\in[0,255]^{H\times W}$. The processing steps are:

### 1) Grayscale and denoise

* Convert RGB to a single channel $G$.
* Apply a small Gaussian blur with standard deviation $\sigma$ to suppress sensor noise: $\tilde G = G * \mathcal N(0,\sigma^2)$.

**Why:** smoothing removes high‑frequency speckle that otherwise creates spurious binary islands after thresholding.

### 2) Global binarization (Otsu)

Choose a threshold $\tau$ that maximizes the **between‑class variance** of foreground and background intensities. With histogram class probabilities $\omega_0(\tau), \omega_1(\tau)$ and class means $\mu_0(\tau), \mu_1(\tau)$:

$\sigma_b^2(\tau) = \omega_0(\tau)\,\omega_1(\tau)\,[\mu_0(\tau) - \mu_1(\tau)]^2.$

The binary image is $X=\mathbf{1}[\tilde G\ge\tau]$.

**Why:** Otsu selects a data‑driven threshold that best separates bright plate background from darker characters.

### 3) Morphological clean‑up (dilation / opening / closing)

Morphology treats binary images as sets. With structuring element $S$:

* **Erosion:** $X\ominus S=\{x\mid S_x\subseteq X\}$ removes small bright spots.
* **Dilation:** $X\oplus S=\{x\mid (\hat S)_x\cap X\neq\varnothing\}$ fattens bright regions, reconnecting broken strokes.
* **Opening:** $X\circ S=(X\ominus S)\oplus S$ deletes tiny noise while preserving thin strokes.
* **Closing:** $X\bullet S=(X\oplus S)\ominus S$ fills small gaps in bright components.

In practice we use a tiny rectangular $S$ (2×2 or 3×3) and either: (a) a single **dilation** when letters are fragmented, or (b) **open→close** when salt‑and‑pepper noise appears.

**Parameter intuition:** if the nominal character stroke width in pixels is $w$, then $|S|\approx 0.2w$ thickens without merging neighbors. Over‑dilation merges characters; under‑dilation leaves gaps that hurt OCR.

### 4) Polarity and gradients

* **Invert** when necessary so characters are dark on light (or vice‑versa) to match the OCR head’s training polarity.
* Optionally compute a **morphological gradient** $(X\oplus S)-(X\ominus S)$ as a thin outline that can help OCR trained on edge‑like glyphs.

### 5) What the OCR actually sees

The OCR head is evaluated on one or two variants (post‑dilation and/or inverted). The variant with the highest confidence $c\in[0,1]$ is selected.

<div align="center">
  <img src="https://github.com/user-attachments/assets/1ae88454-1fbf-4893-9395-ef175fa93a1a" width="500" alt="Close‑up: stacked morphology thumbnails with OCR and confidence"/>
  <br/>
  <sub><b>Fig A.</b> Per‑frame explainability — thumbnails of the morphological steps and the resulting OCR label with confidence.</sub>
</div>

**Key takeaways**

* Otsu provides a principled binary split; morphology then repairs stroke continuity.
* The entire chain is **deterministic**, low‑latency, and easy to tune with just $\sigma$, $S$ size, and a polarity flag.

---

## 🧩 End‑to‑end pipeline (concept)

**Detector → ROI → Morphology → OCR → Post‑process.**

**1) Detection.** A compact one‑stage detector (YOLO‑style) outputs plate boxes with a score per frame. Boxes are represented as $(x_1,y_1,x_2,y_2)$ in pixel coordinates.

**2) ROI crop.** Each box is sanity‑checked (aspect ratio, minimum size) and cropped. Tiny crops are skipped to avoid spurious OCR.

**3) Morphological enhancement.** The function `morphological_pipeline(...)` returns labeled snapshots: `("Gray", I1)`, `("Blur", I2)`, `("Otsu", I3)`, `("Dilate", I4)`, `("Invert", I5)`; these feed both OCR and the explainer strip in Fig A.

**4) OCR.** Returns an uppercase alphanumeric string and a confidence score.

**5) Post‑processing & overlays.** The label and confidence are drawn in a high‑contrast banner; the ROI box is **green** unless the string matches a watchlist (then **red**). A vertical strip of thumbnails is placed near the vehicle for quick debugging.

**Pseudocode**

```text
for each video frame:
  boxes = detector(frame)
  for b in boxes:
    roi = crop(frame, b)
    steps = morphological_pipeline(roi)   # [Gray, Blur, Otsu, Dilate, (Invert)]
    text, conf = ocr(select_best(steps))
    color = RED if text in WATCHLIST else GREEN
    draw_banner(frame, text, conf, near=b)
    draw_box(frame, b, color)
    draw_thumbnails(frame, steps, column_near=b)
show(frame)
```

<div align="center">
  <img src="https://github.com/user-attachments/assets/bd661eca-97d1-4e26-b833-01708ee8e631" width="500" alt="Street view with flagged and non‑flagged plates"/>
  <br/>
  <sub><b>Fig C.</b> Watchlist matching — non‑matches in green, flagged plate in red.</sub>
</div>

---

## 📐 Practical tuning notes

* **Thresholding:** Otsu is strong for daytime. Under harsh glare or at night, consider **adaptive** thresholding (mean or Gaussian) in place of, or in addition to, Otsu.
* **Structuring element:** start with 2×2 or 3×3 rectangles. Increase only if letters fragment; decrease if letters start to merge.
* **Text banner:** compute text extent via `cv2.getTextSize` and paint a white rectangle behind the text for legibility.
* **Throughput:** thumbnail sizes around 80×60 keep the explainer strip cheap while preserving interpretability.
* **Normalization for watchlists:** uppercase and strip whitespace/hyphens before lookup.

---

## ✅ Expected behavior and limits

* Clear, forward‑facing shots yield high read rates with confidences above 0.9 (see Fig B).
* On low‑contrast plates, morphology usually increases confidence by reconnecting strokes (Fig A).
* Limits: strong motion blur and severe glare degrade both detection and OCR; regional plate layouts vary; stacked characters or non‑Latin scripts require specialized OCR. Adding simple object tracking (IoU‑based) stabilizes labels across frames.

---

## 🗂️ Repository (brief)

* `main.py` — video loop, detector inference, overlays, thumbnails, watchlist logic.
* `morphological_pipeline.py` — the classical enhancement chain described above.

**Ethics & privacy.** Use ALPR in accordance with local law and policy. Consider blurring faces/vehicles outside the ROI in demos.

---

## License

MIT — see `LICENSE`.
