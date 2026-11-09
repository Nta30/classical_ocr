import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "D:/TaiLieu/Nam4Ky1/Image_Processing/classical-ocr";
const skillDir = "C:/Users/nguye/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations";
const buildDir = path.join(workspaceDir, ".presentation_build");
const outputDir = path.join(workspaceDir, "deliverables");
const candidatePath = path.join(buildDir, "candidate.pptx");
const finalPath = path.join(outputDir, "de_cuong_bao_cao_classical_ocr.pptx");
const receiptPath = path.join(buildDir, "validation.json");
const expectedSlideSizeEmu = "12192000,6858000";

const { makeNativeBulletParagraphs, resolvePresentationFont, finalizePresentation } =
  await import(pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href);

const fontFamily = resolvePresentationFont({ fontFamily: "Arial" });
const COLORS = {
  background: "#F8FAFC",
  navy: "#16324F",
  body: "#263746",
  muted: "#607487",
  teal: "#087E8B",
};

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const slide = presentation.slides.add();
slide.background.fill = COLORS.background;

function addTextBox(position, text, style = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = {
    typeface: fontFamily,
    fontSize: 22.7,
    color: COLORS.body,
    verticalAlignment: "top",
    autoFit: "none",
    insets: 0,
    ...style,
  };
  return box;
}

addTextBox(
  { left: 72, top: 42, width: 1136, height: 72 },
  "Đề cương báo cáo dự kiến",
  { fontSize: 58, bold: true, color: COLORS.navy },
);

addTextBox(
  { left: 76, top: 121, width: 1128, height: 38 },
  "Đề tài: OCR chữ in tiếng Anh bằng xử lý ảnh cổ điển và so khớp mẫu",
  { fontSize: 24, color: COLORS.muted },
);

const columns = [
  {
    left: 74,
    items: [
      {
        heading: "01. Bài toán và mục tiêu",
        detail: "Nêu nhu cầu chuyển ảnh chữ in tiếng Anh thành văn bản; chốt phạm vi A–Z, a–z, chữ số, dấu câu và điều kiện ảnh nền sáng, gần thẳng.",
      },
      {
        heading: "02. Cơ sở lý thuyết",
        detail: "Giải thích OCR và so khớp mẫu; tóm tắt bốn bước trong bài Hossain & Afrin (2019); tách rõ nội dung bài báo và lựa chọn của nhóm.",
      },
      {
        heading: "03. Phương pháp",
        detail: "Trình bày luồng: grayscale/Otsu → lọc nhiễu → tách dòng, ký tự bằng phép chiếu → chuẩn hóa 48×48 → Pixel Similarity (NumPy) → ghép văn bản.",
      },
    ],
  },
  {
    left: 660,
    items: [
      {
        heading: "04. Cài đặt và demo",
        detail: "Nêu Python, OpenCV, NumPy, Pillow và giao diện web; minh họa tải ảnh, nhận dạng, xem kết quả/vùng ký tự và tải tệp .txt.",
      },
      {
        heading: "05. Thực nghiệm và đánh giá",
        detail: "Mô tả 32 ảnh tổng hợp (4 font, 8 tình huống); báo cáo chính xác ký tự gộp 95,1%, CER gộp 4,9%, CER trung bình ảnh 16,3%, khớp toàn văn 15/32; phân tích lỗi.",
      },
      {
        heading: "06. Kết luận và hướng phát triển",
        detail: "Tổng kết phạm vi hiện tại; nêu hạn chế với font lạ, ảnh nghiêng và chữ dính; đề xuất thử ảnh chụp thật, mở rộng dữ liệu và đối chiếu Pixel Similarity với NCC.",
      },
    ],
  },
];

for (const column of columns) {
  const sourceItems = column.items.map((item) => `${item.heading} — ${item.detail}`);
  const paragraphs = makeNativeBulletParagraphs(sourceItems, {
    marginLeftPoints: 19,
    hangingPoints: 10,
    spaceAfterPoints: 12,
    bulletCharacter: "•",
  });
  for (let index = 0; index < paragraphs.length; index += 1) {
    const item = column.items[index];
    paragraphs[index].runs = [
      {
        run: item.heading,
        style: { bold: true, typeface: fontFamily, fontSize: "18pt", color: COLORS.navy },
      },
      {
        run: ` — ${item.detail}`,
        style: { typeface: fontFamily, fontSize: "17pt", color: COLORS.body },
      },
    ];
  }
  addTextBox(
    { left: column.left, top: 183, width: 546, height: 422 },
    paragraphs,
    { fontSize: 22.7, color: COLORS.body },
  );
}

addTextBox(
  { left: 76, top: 615, width: 1128, height: 36 },
  [
    {
      runs: [
        { run: "Xin thầy góp ý: ", style: { bold: true, color: COLORS.teal, typeface: fontFamily } },
        { run: "Bố cục đã đủ chưa? Có cần bổ sung ảnh chụp thực tế hoặc bảng so sánh Pixel Similarity với NCC?", style: { color: COLORS.body, typeface: fontFamily } },
      ],
    },
  ],
  { fontSize: 19, color: COLORS.body },
);

addTextBox(
  { left: 76, top: 661, width: 1128, height: 28 },
  "Lưu ý: kết quả hiện có được đo trên ảnh tổng hợp từ font máy tính, chưa đại diện cho ảnh chụp thực tế.",
  { fontSize: 17, color: COLORS.muted },
);

slide.speakerNotes.text = [
  "Nguồn phạm vi, giao diện và phương pháp: README.md và docs/presentation_guide.md trong dự án.",
  "Nguồn mô tả bài báo và phân biệt phương pháp của paper với lựa chọn triển khai: docs/paper_analysis.md.",
  "Nguồn số liệu: evaluation_pixel.csv. Có 32 ảnh thuộc 4 font, 34 lỗi trên 688 ký tự tham chiếu, weighted character accuracy 95.058%, weighted CER 4.942%, macro CER 16.281%, exact match 15/32.",
  "Bộ ảnh tổng hợp có 8 tình huống được sinh từ font máy tính; đây không phải thí nghiệm tái lập chính xác dữ liệu trong bài báo.",
];

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const preview = await presentation.export({ slide, format: "png", scale: 1 });
await fs.writeFile(path.join(buildDir, "slide-preview.png"), new Uint8Array(await preview.arrayBuffer()));

const fontPolicy = { basis: "design", families: [fontFamily] };
const requirements = {
  explicitTotalSlideCount: 1,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
};

const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: "C:/Users/nguye/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe",
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", expectedSlideSizeEmu, "--validate-bullet-geometry", "--validate-heading-fit"],
  fontPolicy,
  verifyArtifactToolImport: true,
  receiptPath,
});

console.log(JSON.stringify({ finalPath, fontFamily, result }, null, 2));
