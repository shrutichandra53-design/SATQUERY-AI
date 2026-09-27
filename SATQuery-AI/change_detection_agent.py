# ============================================================
# SATQUERY AI — CHANGE DETECTION AGENT
# REAL IMAGE DIFFERENCE + ALIGNMENT + PRECISE CHANGE MASK
# ============================================================

import requests
import numpy as np

from PIL import Image, ImageDraw
from io import BytesIO


# ============================================================
# DOWNLOAD IMAGE
# ============================================================

def download_image(image_url):

    response = requests.get(
        image_url,
        timeout=60,
        headers={
            "User-Agent": "SATQuery-AI/1.0"
        }
    )

    response.raise_for_status()

    image = Image.open(
        BytesIO(response.content)
    ).convert("RGB")

    return image


# ============================================================
# RESIZE BOTH IMAGES TO SAME SIZE
# ============================================================

def prepare_images(before, after, max_size=1400):

    width = min(
        before.width,
        after.width
    )

    height = min(
        before.height,
        after.height
    )

    before = before.resize(
        (width, height),
        Image.Resampling.LANCZOS
    )

    after = after.resize(
        (width, height),
        Image.Resampling.LANCZOS
    )

    # --------------------------------------------------------
    # Limit extremely large images
    # --------------------------------------------------------

    if max(width, height) > max_size:

        scale = max_size / max(width, height)

        new_width = int(width * scale)
        new_height = int(height * scale)

        before = before.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )

        after = after.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )

    return before, after


# ============================================================
# IMAGE ALIGNMENT
# ============================================================

def align_images(before, after):

    try:

        import cv2

        before_np = np.array(before)
        after_np = np.array(after)

        before_gray = cv2.cvtColor(
            before_np,
            cv2.COLOR_RGB2GRAY
        )

        after_gray = cv2.cvtColor(
            after_np,
            cv2.COLOR_RGB2GRAY
        )

        before_gray = before_gray.astype(
            np.float32
        ) / 255.0

        after_gray = after_gray.astype(
            np.float32
        ) / 255.0

        # ----------------------------------------------------
        # ECC alignment
        # ----------------------------------------------------

        warp_matrix = np.eye(
            2,
            3,
            dtype=np.float32
        )

        criteria = (
            cv2.TERM_CRITERIA_EPS
            | cv2.TERM_CRITERIA_COUNT,
            100,
            1e-6
        )

        try:

            cc, warp_matrix = cv2.findTransformECC(
                before_gray,
                after_gray,
                warp_matrix,
                cv2.MOTION_AFFINE,
                criteria
            )

            aligned_after = cv2.warpAffine(
                after_np,
                warp_matrix,
                (
                    before_np.shape[1],
                    before_np.shape[0]
                ),
                flags=cv2.INTER_LINEAR
                | cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_REFLECT
            )

            return Image.fromarray(
                aligned_after
            ), True

        except Exception:

            # ------------------------------------------------
            # If ECC fails, use original image
            # ------------------------------------------------

            return after, False

    except ImportError:

        raise ImportError(
            "OpenCV is required.\n\n"
            "Run:\n"
            "pip install opencv-python-headless"
        )


# ============================================================
# REMOVE BORDER / EDGE EFFECTS
# ============================================================

def remove_border_artifacts(mask, border_ratio=0.02):

    height, width = mask.shape

    bx = int(width * border_ratio)
    by = int(height * border_ratio)

    mask[:by, :] = 0
    mask[-by:, :] = 0

    mask[:, :bx] = 0
    mask[:, -bx:] = 0

    return mask


# ============================================================
# DETECT CHANGES
# ============================================================

def detect_changes(
    before_url,
    after_url,
    threshold=35,
    min_area=500
):

    # ========================================================
    # DOWNLOAD
    # ========================================================

    before = download_image(
        before_url
    )

    after = download_image(
        after_url
    )

    # ========================================================
    # PREPARE
    # ========================================================

    before, after = prepare_images(
        before,
        after
    )

    width = before.width
    height = before.height

    # ========================================================
    # ALIGN AFTER TO BEFORE
    # ========================================================

    aligned_after, alignment_success = align_images(
        before,
        after
    )

    # ========================================================
    # NUMPY ARRAYS
    # ========================================================

    before_np = np.array(
        before
    )

    after_np = np.array(
        aligned_after
    )

    # ========================================================
    # OPENCV
    # ========================================================

    try:

        import cv2

    except ImportError:

        raise ImportError(
            "OpenCV is required.\n\n"
            "Run:\n"
            "pip install opencv-python-headless"
        )

    # ========================================================
    # CONVERT TO LAB
    #
    # LAB is more stable than raw RGB for brightness changes.
    # ========================================================

    before_lab = cv2.cvtColor(
        before_np,
        cv2.COLOR_RGB2LAB
    )

    after_lab = cv2.cvtColor(
        after_np,
        cv2.COLOR_RGB2LAB
    )

    # ========================================================
    # BLUR BEFORE DIFFERENCE
    #
    # Removes tiny satellite/image noise.
    # ========================================================

    before_blur = cv2.GaussianBlur(
        before_lab,
        (5, 5),
        0
    )

    after_blur = cv2.GaussianBlur(
        after_lab,
        (5, 5),
        0
    )

    # ========================================================
    # PIXEL DIFFERENCE
    # ========================================================

    difference = cv2.absdiff(
        before_blur,
        after_blur
    )

    # --------------------------------------------------------
    # Combine LAB channels
    # --------------------------------------------------------

    difference = np.mean(
        difference,
        axis=2
    )

    # ========================================================
    # SMOOTH DIFFERENCE MAP
    # ========================================================

    difference = cv2.GaussianBlur(
        difference.astype(np.float32),
        (7, 7),
        0
    )

    # ========================================================
    # THRESHOLD
    # ========================================================

    mask = (
        difference > threshold
    ).astype(np.uint8) * 255

    # ========================================================
    # REMOVE VERY SMALL NOISE
    # ========================================================

    kernel_small = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (3, 3)
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel_small,
        iterations=1
    )

    # ========================================================
    # CONNECT NEARBY CHANGE PIXELS
    # ========================================================

    kernel_medium = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (7, 7)
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel_medium,
        iterations=2
    )

    # ========================================================
    # REMOVE IMAGE BORDER ARTIFACTS
    # ========================================================

    mask = remove_border_artifacts(
        mask,
        border_ratio=0.015
    )

    # ========================================================
    # CONNECTED COMPONENTS
    # ========================================================

    num_labels, labels, stats, centroids = (
        cv2.connectedComponentsWithStats(
            mask,
            connectivity=8
        )
    )

    # ========================================================
    # CREATE CLEAN FILTERED MASK
    # ========================================================

    filtered_mask = np.zeros_like(
        mask
    )

    boxes = []

    # ========================================================
    # FILTER COMPONENTS
    # ========================================================

    for i in range(
        1,
        num_labels
    ):

        x = int(
            stats[i, cv2.CC_STAT_LEFT]
        )

        y = int(
            stats[i, cv2.CC_STAT_TOP]
        )

        w = int(
            stats[i, cv2.CC_STAT_WIDTH]
        )

        h = int(
            stats[i, cv2.CC_STAT_HEIGHT]
        )

        area = int(
            stats[i, cv2.CC_STAT_AREA]
        )

        # ----------------------------------------------------
        # Ignore tiny regions
        # ----------------------------------------------------

        if area < min_area:
            continue

        # ----------------------------------------------------
        # Ignore extremely huge region
        #
        # Prevents the entire image becoming one "change".
        # ----------------------------------------------------

        image_area = width * height

        component_ratio = (
            area / image_area
        )

        if component_ratio > 0.35:

            continue

        # ----------------------------------------------------
        # Keep this component
        # ----------------------------------------------------

        filtered_mask[
            labels == i
        ] = 255

        boxes.append(
            {
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "area": area,
                "center_x": x + w // 2,
                "center_y": y + h // 2
            }
        )

    # ========================================================
    # SECOND MORPHOLOGY PASS
    # ========================================================

    filtered_mask = cv2.morphologyEx(
        filtered_mask,
        cv2.MORPH_CLOSE,
        kernel_medium,
        iterations=1
    )

    # ========================================================
    # RE-CALCULATE COMPONENTS AFTER FILTERING
    # ========================================================

    num_final, final_labels, final_stats, final_centroids = (
        cv2.connectedComponentsWithStats(
            filtered_mask,
            connectivity=8
        )
    )

    final_boxes = []

    for i in range(
        1,
        num_final
    ):

        x = int(
            final_stats[i, cv2.CC_STAT_LEFT]
        )

        y = int(
            final_stats[i, cv2.CC_STAT_TOP]
        )

        w = int(
            final_stats[i, cv2.CC_STAT_WIDTH]
        )

        h = int(
            final_stats[i, cv2.CC_STAT_HEIGHT]
        )

        area = int(
            final_stats[i, cv2.CC_STAT_AREA]
        )

        if area < min_area:
            continue

        image_area = width * height

        if area / image_area > 0.35:
            continue

        final_boxes.append(
            {
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "area": area,
                "center_x": x + w // 2,
                "center_y": y + h // 2
            }
        )

    boxes = final_boxes

    # ========================================================
    # PRECISE RED OVERLAY
    #
    # IMPORTANT:
    # We DON'T make the entire bounding box red.
    # Only actual changed pixels get red overlay.
    # ========================================================

    annotated_np = after_np.copy()

    change_pixels = (
        filtered_mask > 0
    )

    # --------------------------------------------------------
    # Red overlay only on detected pixels
    # --------------------------------------------------------

    overlay = np.zeros_like(
        annotated_np
    )

    overlay[:, :, 0] = 255
    overlay[:, :, 1] = 40
    overlay[:, :, 2] = 40

    alpha = 0.45

    annotated_np[
        change_pixels
    ] = (
        annotated_np[
            change_pixels
        ] * (1 - alpha)
        +
        overlay[
            change_pixels
        ] * alpha
    ).astype(np.uint8)

    annotated = Image.fromarray(
        annotated_np
    )

    # ========================================================
    # DRAW BOUNDING BOXES
    # ========================================================

    draw = ImageDraw.Draw(
        annotated
    )

    for index, box in enumerate(
        boxes,
        start=1
    ):

        x = box["x"]
        y = box["y"]

        w = box["width"]
        h = box["height"]

        # ----------------------------------------------------
        # Slight padding
        # ----------------------------------------------------

        padding = 5

        x1 = max(
            0,
            x - padding
        )

        y1 = max(
            0,
            y - padding
        )

        x2 = min(
            width - 1,
            x + w + padding
        )

        y2 = min(
            height - 1,
            y + h + padding
        )

        # ----------------------------------------------------
        # Red outline
        # ----------------------------------------------------

        draw.rectangle(
            [
                x1,
                y1,
                x2,
                y2
            ],
            outline="red",
            width=3
        )

        # ----------------------------------------------------
        # Label
        # ----------------------------------------------------

        label = f"CHANGE {index}"

        text_y = max(
            0,
            y1 - 18
        )

        draw.text(
            (
                x1,
                text_y
            ),
            label,
            fill="red"
        )

    # ========================================================
    # CHANGE AREA
    # ========================================================

    total_pixels = (
        width * height
    )

    changed_pixels = int(
        np.count_nonzero(
            filtered_mask
        )
    )

    if total_pixels > 0:

        change_percentage = (
            changed_pixels
            /
            total_pixels
        ) * 100

    else:

        change_percentage = 0.0

    # ========================================================
    # RAW CHANGE
    # ========================================================

    raw_changed_pixels = int(
        np.count_nonzero(
            mask
        )
    )

    raw_change_percentage = (
        raw_changed_pixels
        /
        total_pixels
    ) * 100

    # ========================================================
    # CHANGE DETAILS
    # ========================================================

    change_details = []

    for index, box in enumerate(
        boxes,
        start=1
    ):

        area_percentage = (
            box["area"]
            /
            total_pixels
        ) * 100

        change_details.append(
            {
                "region": index,
                "x": box["x"],
                "y": box["y"],
                "width": box["width"],
                "height": box["height"],
                "area_pixels": box["area"],
                "area_percentage": round(
                    area_percentage,
                    4
                )
            }
        )

    # ========================================================
    # STATUS
    # ========================================================

    if len(boxes) > 0:

        status = "CHANGE_DETECTED"

        finding = (
            f"{len(boxes)} significant "
            f"changed region(s) detected."
        )

    else:

        status = "NO_MAJOR_CHANGE"

        finding = (
            "No significant spatial "
            "change detected."
        )

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "status": status,

        "confidence": (
            "HIGH"
            if len(boxes) > 0
            else "MODERATE"
        ),

        "finding": finding,

        # ----------------------------------------------------
        # Images
        # ----------------------------------------------------

        "before_image": before,

        "after_image": aligned_after,

        "annotated_image": annotated,

        "change_mask": Image.fromarray(
            filtered_mask
        ),

        # ----------------------------------------------------
        # Change information
        # ----------------------------------------------------

        "boxes": boxes,

        "change_count": len(
            boxes
        ),

        "region_count": len(
            boxes
        ),

        "changed_pixels": changed_pixels,

        "raw_changed_pixels": raw_changed_pixels,

        "total_pixels": total_pixels,

        "changed_area_percentage": round(
            change_percentage,
            2
        ),

        "change_percentage": round(
            change_percentage,
            2
        ),

        "raw_change_percentage": round(
            raw_change_percentage,
            2
        ),

        # ----------------------------------------------------
        # Image information
        # ----------------------------------------------------

        "image_width": width,

        "image_height": height,

        # ----------------------------------------------------
        # Technical information
        # ----------------------------------------------------

        "effective_threshold": threshold,

        "min_area": min_area,

        "alignment_success": alignment_success,

        "detection_mode": (
            "ALIGNED_LAB_PIXEL_DIFFERENCE"
        ),

        "parameters": {

            "threshold": threshold,

            "min_area": min_area,

            "blur_kernel": 5,

            "difference_blur": 7,

            "morphology": "OPEN + CLOSE",

            "alignment": (
                "ECC AFFINE"
                if alignment_success
                else "ORIGINAL"
            )

        },

        # ----------------------------------------------------
        # Detailed regions
        # ----------------------------------------------------

        "change_details": change_details
    }


# ============================================================
# CHANGE SUMMARY
# ============================================================

def build_change_summary(result):

    if not result:

        return "No change detection result available."

    count = result.get(
        "change_count",
        0
    )

    percentage = result.get(
        "changed_area_percentage",
        0
    )

    alignment = result.get(
        "alignment_success",
        False
    )

    if count == 0:

        return (
            "No major spatial change was detected. "
            f"Only {percentage:.2f}% of the analysed "
            "image was classified as changed."
        )

    summary = (
        f"{count} significant changed region(s) "
        f"were detected, covering approximately "
        f"{percentage:.2f}% of the analysed image."
    )

    if alignment:

        summary += (
            " The images were spatially aligned "
            "before comparison."
        )

    return summary