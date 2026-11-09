"""Create a reproducible pipeline figure from the existing demo image."""
from pathlib import Path
import json
import sys
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from classical_ocr.preprocessing import load_image
from classical_ocr.recognition import recognize
from classical_ocr.template_generator import available_fonts, generate_templates

out = Path(__file__).parent / 'assets'
out.mkdir(exist_ok=True)
result = recognize(load_image(ROOT / 'sample_images/demo_multiline.png'), generate_templates(available_fonts()))
canvas = Image.new('RGB', (1500, 700), 'white')
draw = ImageDraw.Draw(canvas)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 30)
panels = [('Ảnh đầu vào', result.steps['original']), ('Nhị phân Otsu', result.steps['binary']),
          ('Sau làm sạch', result.steps['denoised']), ('Vùng ký tự', result.annotated)]
for n, (label, arr) in enumerate(panels):
    x, y = 24 + (n % 2) * 750, 15 + (n // 2) * 350
    draw.text((x, y), f'{n+1}  {label}', font=font, fill='black')
    im = Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB) if arr.ndim == 3 else arr).convert('RGB')
    im.thumbnail((690, 270))
    scale = min(690/im.width, 270/im.height)
    if scale > 1: im = im.resize((round(im.width*scale), round(im.height*scale)))
    canvas.paste(im, (x + (700-im.width)//2, y + 58 + (265-im.height)//2))
    draw.rectangle((x, y+55, x+700, y+325), outline='#cccccc', width=2)
canvas.save(out / 'pipeline.png')
qa = Path(__file__).parent / '_qa'
qa.mkdir(exist_ok=True)
(qa / 'demo_result.json').write_text(json.dumps({'text':result.text,'characters':len(result.characters),
    'threshold':result.steps['threshold_used'],'seconds':result.processing_seconds},ensure_ascii=False,indent=2),encoding='utf-8')
print(result.text)
