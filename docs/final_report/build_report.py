"""Build the editable report from its Markdown source using native Word math."""
import re
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE = Path(__file__).parent
SOURCE = BASE / 'BAO_CAO_CUOI_KY_OCR.md'
DEST = BASE / 'BAO_CAO_CUOI_KY_OCR.docx'

def el(tag, text=None, **attrs):
    e=OxmlElement(tag)
    if text is not None: e.text=text
    for key,value in attrs.items(): e.set(qn(key),str(value))
    return e
def mr(text):
    e=el('m:r'); e.append(el('m:t',text)); return e
def group(tag, items):
    e=el(tag)
    for item in items:
        e.append(mr(item) if isinstance(item,str) else item)
    return e
def sub(base, value):
    e=el('m:sSub');e.append(group('m:e',[base]));e.append(group('m:sub',[value]));return e
def sup(base,value):
    e=el('m:sSup');e.append(group('m:e',base if isinstance(base,list) else [base]));e.append(group('m:sup',[value]));return e
def frac(num,den):
    e=el('m:f');e.append(group('m:num',num));e.append(group('m:den',den));return e
def sqrt(items):
    e=el('m:rad');pr=el('m:radPr');pr.append(el('m:degHide', **{'m:val':'1'}));e.append(pr);e.append(el('m:deg'));e.append(group('m:e',items));return e
def summation(low, high, items):
    e=el('m:nary');pr=el('m:naryPr');pr.append(el('m:chr',**{'m:val':'∑'}));pr.append(el('m:limLoc',**{'m:val':'subSup'}))
    if not high: pr.append(el('m:supHide',**{'m:val':'1'}))
    e.append(pr);e.append(group('m:sub',[low]));e.append(group('m:sup',[high]));e.append(group('m:e',items));return e

def equation(number):
    if number==1: return ['Y = 0,299R + 0,587G + 0,114B']
    if number==2: return [sup('t','*'),' = ',sub('arg max','t'),' ',sub('ω','0'),'(t)',sub('ω','1'),'(t)',sup([ '[',sub('μ','0'),'(t) − ',sub('μ','1'),'(t)]' ],'2')]
    if number==3: return [sub('P','y'),'(y) = ',summation('x=0','W−1',['B(y,x)'])]
    if number==4: return [sub('P','x'),'(x) = ',summation('y=y₀','y₁−1',['B(y,x)'])]
    if number==5: return [sub('S','pixel'),'(I,T) = 1 − ',frac(['1'],['M']),summation('j=1','M',['|',sub('I','j'),' − ',sub('T','j'),'|'])]
    if number==6:
        return ['NCC(i,t) = ',frac([summation('j','',['(',sub('i','j'),' − ī)(',sub('t','j'),' − t̄)'])],
             [sqrt([summation('j','',[sup(['(',sub('i','j'),' − ī)'],'2')]),' ',summation('j','',[sup(['(',sub('t','j'),' − t̄)'],'2')])])])]
    return [sub('CER','gộp'),' = ',frac([summation('i','',[sub('D','i')])],[summation('i','',[sub('N','i')])]),'     ',sub('CER','macro'),' = ',frac(['1'],['m']),summation('i=1','m',[frac([sub('D','i')],[sub('N','i')])])]

doc=Document()
sec=doc.sections[0]
sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=Cm(2.2);sec.bottom_margin=Cm(2.1);sec.left_margin=Cm(2.5);sec.right_margin=Cm(2.1)
sec.header_distance=Cm(0.9);sec.footer_distance=Cm(1.0)
styles=doc.styles
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption']:
    s=styles[name];s.font.name='Times New Roman';s.font.color.rgb=RGBColor(0,0,0)
    fonts=s.element.get_or_add_rPr().rFonts
    for key in list(fonts.attrib):
        if key.endswith('Theme'): del fonts.attrib[key]
    for key in ['ascii','hAnsi','eastAsia','cs']: fonts.set(qn('w:'+key),'Times New Roman')
    for node in s.element.findall('.//'+qn('w:pBdr')): node.getparent().remove(node)
normal=styles['Normal'];normal.font.size=Pt(12)
normal.paragraph_format.line_spacing=1.08;normal.paragraph_format.space_after=Pt(3)
normal.paragraph_format.widow_control=True
normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
styles['Title'].font.size=Pt(20);styles['Title'].font.bold=True
styles['Title'].paragraph_format.space_after=Pt(12)
styles['Heading 1'].font.size=Pt(15);styles['Heading 1'].font.bold=True
styles['Heading 1'].paragraph_format.space_before=Pt(14);styles['Heading 1'].paragraph_format.space_after=Pt(7)
styles['Heading 2'].font.size=Pt(13);styles['Heading 2'].font.bold=True
styles['Heading 2'].paragraph_format.space_before=Pt(10);styles['Heading 2'].paragraph_format.space_after=Pt(5)
styles['Caption'].font.size=Pt(11);styles['Caption'].font.italic=True;styles['Caption'].font.bold=False
styles['Caption'].paragraph_format.line_spacing=1.05
for name in ['Heading 1','Heading 2','Heading 3']:
    styles[name].paragraph_format.keep_with_next=True
    styles[name].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT

header=sec.header.paragraphs[0];header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=header.add_run('CLASSICAL OCR LAB');r.font.name='Times New Roman';r.font.size=Pt(9);r.font.color.rgb=RGBColor(0,0,0)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=footer.add_run();field=el('w:fldSimple',**{'w:instr':'PAGE'});r._r.addnext(field)
sec.different_first_page_header_footer=True

def text_runs(p,text):
    for n,chunk in enumerate(re.split(r'`([^`]+)`',text)):
        r=p.add_run(chunk)
        if n%2: r.font.name='Consolas';r.font.size=Pt(10.5)

lines=SOURCE.read_text(encoding='utf-8').splitlines();i=0;eq_no=0
while i<len(lines):
    line=lines[i].strip()
    if not line: i+=1;continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?',c) for c in cells): rows.append(cells)
            i+=1
        caption_index=i
        while caption_index<len(lines) and not lines[caption_index].strip(): caption_index+=1
        if caption_index<len(lines) and re.match(r'Bảng \d+\.',lines[caption_index]):
            caption=doc.add_paragraph(lines[caption_index].strip(),'Caption')
            caption.paragraph_format.keep_with_next=True
            caption.paragraph_format.space_after=Pt(5)
            i=caption_index+1
        table=doc.add_table(rows=1,cols=len(rows[0]));table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
        widths=[5.1,11.3] if len(rows[0])==2 else [3.4,1.0,2.5,3.0,2.1,4.4]
        if len(rows[0])==6: widths=[3.4,1.2,2.3,3.0,2.1,3.0]
        for col,w in zip(table.columns,widths): col.width=Cm(w)
        borders=el('w:tblBorders')
        for edge in ['top','left','bottom','right','insideH','insideV']:
            borders.append(el('w:'+edge,**{'w:val':'single','w:sz':'4','w:color':'D9D9D9'}))
        table._tbl.tblPr.append(borders)
        for ri,rowdata in enumerate(rows):
            row=table.rows[0] if ri==0 else table.add_row()
            trpr=row._tr.get_or_add_trPr();trpr.append(el('w:cantSplit'))
            if ri==0: trpr.append(el('w:tblHeader',**{'w:val':'true'}))
            for ci,(cell,value) in enumerate(zip(row.cells,rowdata)):
                cell.width=Cm(widths[ci]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                pr=cell._tc.get_or_add_tcPr();margins=el('w:tcMar')
                for side in ['top','left','bottom','right']: margins.append(el('w:'+side,**{'w:w':'90','w:type':'dxa'}))
                pr.append(margins)
                if ri==0: pr.append(el('w:shd',**{'w:fill':'E6EDF3'}))
                p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.05
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==0 or len(rowdata)==2 else WD_ALIGN_PARAGRAPH.CENTER
                r=p.add_run(value);r.bold=ri==0;r.font.size=Pt(11)
        space=doc.add_paragraph();space.paragraph_format.space_after=Pt(0)
        space.paragraph_format.line_spacing=Pt(4)
        space.add_run().font.size=Pt(4)
        continue
    if line.startswith('$$'):
        if doc.paragraphs and doc.paragraphs[-1].text.rstrip().endswith(':'):
            doc.paragraphs[-1].paragraph_format.keep_with_next=True
        eq_no+=1;p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before=Pt(5);p.paragraph_format.space_after=Pt(7)
        om=group('m:oMath',equation(eq_no)+[f'    ({eq_no})']);p._p.append(om)
    elif line.startswith('!['):
        match=re.match(r'!\[(.*?)\]\((.*?)\)',line)
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
        run=p.add_run();inline=run.add_picture(str(BASE/match.group(2)),width=Cm(15.8))
        inline._inline.docPr.set('descr',match.group(1))
    elif line.startswith('# '):
        p=doc.add_paragraph(line[2:],'Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    elif line.startswith('## '):
        title=line[3:];p=doc.add_paragraph(title,'Heading 1')
        if title.startswith('1 Giới') or title=='Tài liệu tham khảo': p.paragraph_format.page_break_before=True
    elif line.startswith('### '): doc.add_paragraph(line[4:],'Heading 2')
    else:
        style='Caption' if re.match(r'(Hình|Bảng) \d+\.',line) else None
        p=doc.add_paragraph(style=style);text_runs(p,line)
        if line.startswith('BÁO CÁO') or line.startswith('Đề tài thực nghiệm'):
            p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after=Pt(9)
        if line.startswith('['):
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.first_line_indent=Cm(-0.6);p.paragraph_format.left_indent=Cm(0.6)
            p.paragraph_format.line_spacing=1.05;p.paragraph_format.space_after=Pt(10)
            for r in p.runs: r.font.size=Pt(11.5)
    i+=1

doc.core_properties.title='Nhận dạng chữ in tiếng Anh bằng xử lý ảnh số và so khớp mẫu'
doc.core_properties.subject='Báo cáo cuối kỳ môn Xử lý ảnh số'
doc.core_properties.author=''
doc.core_properties.keywords='OCR, Otsu, template matching, Pixel Similarity, CER'
for p in doc.paragraphs:
    for border in p._p.findall('.//'+qn('w:pBdr')): border.getparent().remove(border)
for style in doc.styles:
    for border in style.element.findall('.//'+qn('w:pBdr')): border.getparent().remove(border)
doc.save(DEST)
print(DEST)
print('Paragraphs',len(doc.paragraphs),'tables',len(doc.tables),'equations',eq_no)
