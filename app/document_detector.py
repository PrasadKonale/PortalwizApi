
import cv2


def detect_document(image_path):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Unable to read the uploaded image")

    height, width = image.shape[:2]

    if width < 100 or height < 100:
        raise ValueError("Image dimensions are too small")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contours = sorted(
        contours,
        key=cv2.contourArea,
        reverse=True
    )

    for contour in contours[:20]:
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(
            contour,
            0.02 * perimeter,
            True
        )

        if len(polygon) == 4:
            area = cv2.contourArea(polygon)

            if area > height * width * 0.10:
                return True

    return False
