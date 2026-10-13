"""Create offline exam export samples for teacher review."""
from pathlib import Path
from teacher_copilot.worksheets import assemble_exam
from teacher_copilot.docx_export import build_docx


def main():
    settings, records = assemble_exam(dict(
        purpose='exam', topic='csa-calls', contents=['parameters', 'calls', 'returns', 'tracing'],
        difficulty='mixed', minutes=45, question_count=5, total_marks=20,
        question_types=['trace', 'write', 'concept']))
    root = Path(__file__).parent / 'outputs' / 'exam_export_acceptance'
    root.mkdir(parents=True, exist_ok=True)
    for audience in ['student', 'teacher']:
        path = root / f'Methods-exam-{audience}.docx'
        path.write_bytes(build_docx({'worksheet_settings': settings}, records, audience))
        print(path)


if __name__ == '__main__':
    main()
