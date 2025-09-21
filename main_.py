import cv2
from fast_alpr.alpr import ALPR
from morphological_pipeline import morphological_pipeline  
import numpy as np

def main():
    
    #alpr trained model  
    alpr = ALPR(detector_model="yolo-v9-s-608-license-plate-end2end")
    #as an example:
    stolen_plates = {"ABC123", "XYZ789"}

    cap = cv2.VideoCapture("data/test1.mp4")
    if not cap.isOpened():
        print("Error opening video.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 2) Run detection + OCR on this frame
        results = alpr.predict(frame)  # list of detection objects

        for r in results:
            # 3) Extract bounding box + recognized text
            bbox = r.detection.bounding_box
            x1, y1, x2, y2 = bbox.x1, bbox.y1, bbox.x2, bbox.y2
            plate_text = r.ocr.text
            plate_conf = r.ocr.confidence

            # 4) Color for stolen plates
            color = (0, 255, 0)
            if plate_text in stolen_plates:
                color = (0, 0, 255)

            # 5) Draw bounding box on the original frame
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)

            # 6) Prepare and draw the label with recognized text + confidence
            label = f"{plate_text} ({plate_conf:.2f})"
            font_scale = 1.2
            thickness = 3
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)

            text_x = int(x1)
            text_y = max(int(y1) - 10, th + 10)
            cv2.rectangle(frame, (text_x - 5, text_y - th - 10),
                                 (text_x + tw + 5, text_y + 5),
                                 (255, 255, 255), -1)
            cv2.putText(frame, label, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)
#--
            # 7) Crop the plate ROI for morphological demonstration.
            x1i, y1i = int(x1), int(y1)
            x2i, y2i = int(x2), int(y2)
            w = x2i - x1i
            h = y2i - y1i
            if w > 10 and h > 10:
                plate_roi = frame[y1i:y2i, x1i:x2i].copy()

                # 7a) Run morphological steps
                steps = morphological_pipeline(plate_roi)
                
                # 7b) Convert each step to BGR and resize
                step_width, step_height = 80, 60  # smaller thumbnails
                step_imgs = []
                for title, img in steps:
                    if len(img.shape) == 2:  # grayscale
                        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                    else:
                        bgr = img.copy()

                    thumb = cv2.resize(bgr, (step_width, step_height), interpolation=cv2.INTER_AREA)
                    step_imgs.append((title, thumb))

                # 7c) Stack them vertically with spacing
                #    We'll place them above the bounding box, each step 70 px tall + 10 px margin.
                #    Or we can space them with 15 px margin each to be sure they don't overlap.

                # Let's define spacing
                margin = 15
                total_height = len(step_imgs) * (step_height + margin)  # e.g. 5 steps => 5*(60+15)=375
                top_overlay = y1i - total_height - 40
                if top_overlay < 0:
                    top_overlay = 0

                left_overlay = x1i
                right_overlay = left_overlay + step_width
                if right_overlay > frame.shape[1]:
                    right_overlay = frame.shape[1]
                    left_overlay = right_overlay - step_width

                # 7d) Place each step image in the frame, top to bottom
                current_y = top_overlay
                for (title, thumb) in step_imgs:
                    h_ = thumb.shape[0]
                    w_ = thumb.shape[1]
                    # clamp bottom if necessary
                    bottom_y = current_y + h_
                    if bottom_y > frame.shape[0]:
                        break  # or clamp

                    frame[current_y:bottom_y, left_overlay:left_overlay+w_] = thumb
                    current_y += h_ + margin

        # 8) Show final frame
        cv2.imshow("End2End + Morph Pipeline Demo", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
