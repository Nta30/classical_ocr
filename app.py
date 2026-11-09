"""Local browser interface for the classical OCR pipeline."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
sys.path.insert(0, str(ROOT / "src"))

import cv2

from classical_ocr.preprocessing import load_image
from classical_ocr.recognition import recognize
from classical_ocr.template_generator import available_fonts, generate_templates


MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_REQUEST_BYTES = 21 * 1024 * 1024


class OCRHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], template_bank: list[object]):
        self.template_bank = template_bank
        super().__init__(address, OCRRequestHandler)


class OCRRequestHandler(BaseHTTPRequestHandler):
    server: OCRHTTPServer

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/health":
            self._send_json(200, {"ok": True})
            return
        if path not in {"/", "/index.html"}:
            self._send_json(404, {"error": "Không tìm thấy trang."})
            return

        try:
            page = (WEB_ROOT / "index.html").read_bytes()
        except OSError:
            self._send_json(500, {"error": "Không đọc được giao diện web."})
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/recognize":
            self._send_json(404, {"error": "Không tìm thấy API."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Yêu cầu tải ảnh không hợp lệ."})
            return
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Ảnh tải lên quá lớn hoặc yêu cầu không hợp lệ."})
            return

        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Yêu cầu tải ảnh không hợp lệ.")
            encoded_image = payload.get("image")
            filename = payload.get("filename", "image")
            if not isinstance(encoded_image, str):
                raise ValueError("Không nhận được dữ liệu ảnh.")
            if not isinstance(filename, str) or Path(filename).suffix.lower() not in {
                ".png",
                ".jpg",
                ".jpeg",
            }:
                raise ValueError("Chỉ hỗ trợ ảnh PNG hoặc JPG.")

            image_bytes = base64.b64decode(encoded_image, validate=True)
            if not image_bytes or len(image_bytes) > MAX_IMAGE_BYTES:
                raise ValueError("Ảnh rỗng hoặc vượt quá giới hạn 15 MB.")

            image = load_image(image_bytes)
            result = recognize(
                image,
                self.server.template_bank,
                threshold_method="otsu",
                matching_method="pixel",
                median_kernel=1,
                morphology="none",
                min_component_area=30,
            )

            success, annotated_png = cv2.imencode(".png", result.annotated)
            if not success:
                raise OSError("Không thể tạo ảnh kết quả.")

            characters = []
            for item in result.characters:
                x, y, width, height = item.segment.bbox
                characters.append(
                    {
                        "line": int(item.segment.line_index + 1),
                        "character": str(item.prediction),
                        "bbox": [int(x), int(y), int(width), int(height)],
                        "font": str(item.best_match.font_name),
                        "score": round(float(item.best_match.score), 4),
                        "review": bool(item.segment.uncertain),
                    }
                )

            self._send_json(
                200,
                {
                    "filename": Path(filename).name,
                    "text": result.text,
                    "processing_ms": round(result.processing_seconds * 1000, 1),
                    "character_count": len(result.characters),
                    "annotated_png": base64.b64encode(annotated_png).decode("ascii"),
                    "characters": characters,
                },
            )
        except (UnicodeDecodeError, json.JSONDecodeError, binascii.Error, ValueError) as error:
            self._send_json(400, {"error": str(error) or "Ảnh không hợp lệ."})
        except OSError as error:
            self._send_json(400, {"error": f"Không thể xử lý ảnh: {error}"})
        except Exception as error:
            self.log_message("OCR processing failed: %s", error)
            self._send_json(500, {"error": "Có lỗi khi nhận dạng. Hãy thử ảnh khác."})

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Chạy giao diện web OCR trên máy này.")
    parser.add_argument("--port", type=int, default=8501, help="Cổng localhost (mặc định: 8501).")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port phải nằm trong khoảng 1 đến 65535.")

    try:
        fonts = available_fonts()
        template_bank = generate_templates(list(fonts))
    except (FileNotFoundError, OSError) as error:
        raise SystemExit(f"Không thể chuẩn bị bộ mẫu ký tự: {error}") from error

    address = ("127.0.0.1", args.port)
    try:
        with OCRHTTPServer(address, template_bank) as server:
            print(f"Classical OCR đang chạy tại http://127.0.0.1:{args.port}")
            print("Chỉ nhận kết nối từ máy này. Nhấn Ctrl+C để dừng.")
            server.serve_forever()
    except OSError as error:
        raise SystemExit(f"Không thể mở cổng {args.port}: {error}") from error


if __name__ == "__main__":
    main()
