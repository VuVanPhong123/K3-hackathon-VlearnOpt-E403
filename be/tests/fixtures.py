from __future__ import annotations

from pathlib import Path

import fitz


def _heading(page: fitz.Page, number: int, title: str) -> None:
    page.insert_text((54, 48), f"Page {number}", fontsize=11, color=(0.25, 0.3, 0.38))
    page.insert_text((54, 78), title, fontsize=18, color=(0.05, 0.17, 0.3))


def create_fixture_pdf(path: Path) -> Path:
    doc = fitz.open()

    page = doc.new_page(width=595, height=842)
    _heading(page, 1, "Grounded learning assistant")
    page.insert_textbox(
        (54, 110, 530, 300),
        "RAG helps a tutor answer from document evidence and return page citations.",
        fontsize=12,
    )

    page = doc.new_page(width=595, height=842)
    _heading(page, 2, "Context priority")
    bullets = [
        "Selected text is the strongest local context.",
        "A visual region carries an exact image crop.",
        "An attached page includes text and the full page image.",
        "Active page is weak context for the phrase current page.",
    ]
    for index, bullet in enumerate(bullets):
        y = 125 + index * 46
        page.draw_circle((70, y - 4), 3, color=(0.15, 0.39, 0.92), fill=(0.15, 0.39, 0.92))
        page.insert_text((84, y), bullet, fontsize=11)

    page = doc.new_page(width=595, height=842)
    _heading(page, 3, "Figure 1: Encoder-decoder architecture")
    boxes = [
        (70, 220, 210, 310, "Encoder"),
        (385, 220, 525, 310, "Decoder"),
        (228, 220, 367, 310, "Attention"),
    ]
    for x0, y0, x1, y1, label in boxes:
        page.draw_rect((x0, y0, x1, y1), color=(0.05, 0.17, 0.3), fill=(0.9, 0.94, 1))
        page.insert_textbox((x0, y0 + 34, x1, y1), label, fontsize=13, align=1)
    page.draw_line((210, 265), (228, 265), color=(0.15, 0.39, 0.92), width=2)
    page.draw_line((367, 265), (385, 265), color=(0.15, 0.39, 0.92), width=2)
    page.draw_polyline([(221, 259), (228, 265), (221, 271)], color=(0.15, 0.39, 0.92), width=2)
    page.draw_polyline([(378, 259), (385, 265), (378, 271)], color=(0.15, 0.39, 0.92), width=2)
    page.insert_text((70, 350), "Input tokens flow through attention before output generation.", fontsize=11)

    page = doc.new_page(width=595, height=842)
    _heading(page, 4, "Scaled dot-product attention")
    page.insert_text((85, 190), "Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V", fontsize=17)
    page.draw_rect((70, 145, 525, 225), color=(0.4, 0.45, 0.52))
    page.insert_textbox(
        (70, 270, 525, 380),
        "The scale factor controls large dot products before softmax.",
        fontsize=12,
    )

    page = doc.new_page(width=595, height=842)
    _heading(page, 5, "Multi-head attention")
    page.insert_textbox(
        (54, 120, 530, 400),
        "Multiple attention heads learn complementary relationships. Their outputs are concatenated and projected.",
        fontsize=12,
    )

    page = doc.new_page(width=595, height=842)
    _heading(page, 6, "Table 1: Layer comparison")
    x_positions = [45, 170, 290, 420, 550]
    y_positions = [130, 180, 230, 280, 330]
    headers = ["Layer type", "Complexity", "Sequential ops", "Max path"]
    rows = [
        ["Self-attention", "n^2 d", "1", "1"],
        ["Recurrent", "n d^2", "n", "n"],
        ["Convolutional", "k n d^2", "1", "log_k(n)"],
    ]
    for x in x_positions:
        page.draw_line((x, y_positions[0]), (x, y_positions[-1]), color=(0.25, 0.3, 0.38))
    for y in y_positions:
        page.draw_line((x_positions[0], y), (x_positions[-1], y), color=(0.25, 0.3, 0.38))
    for column, header in enumerate(headers):
        page.insert_textbox(
            (x_positions[column] + 4, 143, x_positions[column + 1] - 4, 176),
            header,
            fontsize=9,
            align=1,
        )
    for row_index, values in enumerate(rows):
        for column, value in enumerate(values):
            y0 = y_positions[row_index + 1] + 14
            page.insert_textbox(
                (x_positions[column] + 4, y0, x_positions[column + 1] - 4, y0 + 30),
                value,
                fontsize=9,
                align=1,
            )

    page = doc.new_page(width=595, height=842)
    _heading(page, 7, "Training loss chart")
    page.draw_line((90, 560), (500, 560), color=(0.08, 0.12, 0.18), width=1.5)
    page.draw_line((90, 560), (90, 170), color=(0.08, 0.12, 0.18), width=1.5)
    points = [(90, 220), (170, 295), (250, 390), (330, 455), (410, 505), (500, 535)]
    for first, second in zip(points, points[1:]):
        page.draw_line(first, second, color=(0.86, 0.18, 0.15), width=3)
    for point in points:
        page.draw_circle(point, 4, color=(0.86, 0.18, 0.15), fill=(0.86, 0.18, 0.15))
    page.insert_text((260, 600), "Training steps", fontsize=11)
    page.insert_text((100, 190), "Loss", fontsize=11)

    page = doc.new_page(width=595, height=842)
    _heading(page, 8, "Visual-only attention map")
    colors = [(0.12, 0.35, 0.85), (0.2, 0.55, 0.72), (0.35, 0.72, 0.55), (0.95, 0.72, 0.2)]
    for row in range(6):
        for column in range(6):
            color = colors[(row + column) % len(colors)]
            x0 = 130 + column * 52
            y0 = 180 + row * 52
            page.draw_rect((x0, y0, x0 + 46, y0 + 46), color=color, fill=color)

    page = doc.new_page(width=595, height=842)
    _heading(page, 9, "Conclusion")
    page.insert_textbox(
        (54, 120, 530, 360),
        "Know when evidence is missing: grounded assistants should abstain instead of inventing content.",
        fontsize=12,
    )

    doc.save(path)
    doc.close()
    return path
