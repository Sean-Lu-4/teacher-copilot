"""Import teacher-supplied PDF sources without modifying the originals.
Run locally; extracted content and PDF copies stay in gitignored materials/.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
import pymupdf


def identity(path):
    name = path.stem[3:]
    name = re.sub(r'-20\d{6}-.*', '', name)
    name = name.replace('_papersaver', '')
    return re.sub(r'[^a-z0-9]', '', name.lower())


def digest(text):
    return hashlib.sha256(re.sub(r'\s+', '', text).encode()).hexdigest()


def extract(path):
    doc = pymupdf.open(path)
    # Use coordinates to strip page headers/footers without stripping code lines.
    pages = []
    starts = []
    offset = 0
    expected = 1
    for page_no, page in enumerate(doc, 1):
        parts = []
        for block in page.get_text('blocks'):
            x, y, _, bottom, text, *_ = block
            if y < 65 or bottom > page.rect.height - 30 or not isinstance(text, str):
                continue
            match = re.match(r'^\s*(\d+)\.\s+(?=\S)', text)
            if x < 53 and match and int(match[1]) == expected:
                starts.append((expected, page_no, offset + sum(len(p) for p in parts)))
                expected += 1
            parts.append(text.replace('\xa0', ' '))
        body = ''.join(parts)
        pages.append(body)
        offset += len(body)
    doc.close()
    return pages, starts


def split_mcq(pages, starts):
    text = ''.join(pages)
    result = {}
    for i, (number, page, start) in enumerate(starts):
        end = starts[i+1][2] if i+1 < len(starts) else len(text)
        block = text[start:end].strip()
        answer = re.search(r'(?m)^Answer\s+([A-E])\s*$', block)
        question = block[:answer.start()].strip() if answer else block
        question = re.sub(r'^\d+\.\s*', '', question)
        result[number] = dict(number=number, page=page, text=question,
            answer_key=answer[1] if answer else '',
            explanation=block[answer.end():].strip() if answer else '')
    return result


def build(roots, destination):
    if any(not root.is_dir() for root in roots):
        raise ValueError('Source directory unavailable; existing import was not modified.')
    destination.mkdir(parents=True, exist_ok=True)
    (destination/'pdfs').mkdir(exist_ok=True)
    documents=[]; groups={}; warnings=[]
    for root in roots:
        for path in sorted(root.rglob('*.pdf')):
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            target=destination/'pdfs'/f'{sha}.pdf'
            if not target.exists(): shutil.copyfile(path,target)
            pages,starts=extract(path)
            item=dict(id=sha,filename=path.name,collection=root.name,
                unit=path.parent.name.replace('unit',''),kind='MCQ' if 'MCQ' in path.name else 'FRQ',
                role=path.name[:2],pages=len(pages),identity=identity(path))
            documents.append(item)
            groups.setdefault((root.name,identity(path)),{})[item['role']]=(item,pages,starts)
    rows=[]
    for (collection,name),pair in groups.items():
        tb=pair.get('TB'); sg=pair.get('SG'); main=tb or sg; meta=main[0]
        refs=[dict(document=v[0]['id'],role=k,page=1) for k,v in pair.items()]
        if meta['kind']=='FRQ':
            # Preserve the complete shared scenario and all parts as one source set.
            rows.append(dict(id='FRQ-'+digest(collection+name)[:16],kind='FRQ',unit=meta['unit'],collection=collection,
                title=re.sub(r'^(?:TB|SG)_','',meta['filename']).split('-20')[0].replace('.pdf',''),
                text=''.join(tb[1]) if tb else '',answer=''.join(sg[1]) if sg else '',
                status='paired' if tb and sg else 'missing_answer' if tb else 'guide_only',sources=refs,
                note='整组保留共同背景、所有小问和评分标准；请以原版 PDF 中的图表和代码为准。'))
            continue
        qparts=split_mcq(main[1],main[2]); answers=split_mcq(sg[1],sg[2]) if sg else {}
        if sg:
            answer_total=sum(len(re.findall(r'(?m)^Answer\s+[A-E]\s*$', p)) for p in sg[1])
            if len(answers)!=answer_total:
                warnings.append(dict(file=sg[0]['filename'],message='题目分段数与答案标记数不一致',segments=len(answers),answer_markers=answer_total))
        for num,q in qparts.items():
            a=answers.get(num,{})
            question=q['text']
            source_refs=[dict(document=main[0]['id'],role=main[0]['role'],page=q['page'])]
            if sg and sg is not main and a: source_refs.append(dict(document=sg[0]['id'],role='SG',page=a['page']))
            # Pair by identical stem as well as number to detect mismatched booklets.
            stem=lambda t: digest(re.split(r'\(A\)',t,maxsplit=1)[0])
            paired=bool(a.get('answer_key')) and stem(question)==stem(a.get('text',''))
            rows.append(dict(id='MCQ-'+digest(collection+name+str(num))[:16],kind='MCQ',unit=meta['unit'],collection=collection,
                title=f"{collection} · Unit {meta['unit']} · 第 {num} 题",number=num,text=question,
                answer=(a.get('answer_key','')+'\n'+a.get('explanation','')).strip(),answer_key=a.get('answer_key',''),
                status='paired' if paired else 'needs_review',sources=source_refs,
                note='已核对题号与题干。原图、表格和排版请查看原版 PDF。' if paired else '题干与答案对应关系待核对，请查看原版 PDF。'))
    unique={}
    for row in rows:
        key=(row['kind'],digest(row['text'])) if row['text'] else (row['id'],)
        if key in unique:
            first=unique[key];first['sources'].extend(x for x in row['sources'] if x not in first['sources'])
            first.setdefault('duplicate_titles',[]).append(row['title'])
            if first['answer'] and row['answer'] and first.get('answer_key')!=row.get('answer_key'):
                first['status']='needs_review';first['note']='重复题的答案标记存在差异，请核对原文。'
        else:unique[key]=row
    result=dict(version=1,documents=documents,questions=list(unique.values()),warnings=warnings,
        summary=dict(documents=len(documents),pdf_pages=sum(d['pages'] for d in documents),
        source_items=len(rows),unique_items=len(unique),duplicates=len(rows)-len(unique),
        mcq=sum(r['kind']=='MCQ' for r in unique.values()),frq_sets=sum(r['kind']=='FRQ' for r in unique.values())))
    (destination/'bank.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    report=['# 本地 AP 资料导入报告','',json.dumps(result['summary'],ensure_ascii=False,indent=2),'',
        'MCQ 按题号建立条目；FRQ 按完整题组保存，保留共同背景和小问。',
        '原始 PDF 全部保留。未猜测课题、难度、用时或答案；暂不加入自动随机组卷。','', '## 需要核对']
    report += [f"- {r['title']}：{r['status']}" for r in unique.values() if r['status']!='paired']
    report += [str(w) for w in warnings]
    (destination/'import_report.md').write_text('\n'.join(report),encoding='utf-8')
    print(json.dumps(result['summary'],ensure_ascii=False))
    print('warnings',len(warnings))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('roots',nargs='+',type=Path)
    parser.add_argument('--destination',type=Path,default=Path('materials/imported_bank'))
    args=parser.parse_args();build(args.roots,args.destination)
