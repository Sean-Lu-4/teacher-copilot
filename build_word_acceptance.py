"""Reproducible Word samples using the same export path as the teacher UI."""
import base64
from pathlib import Path
from teacher_copilot.review_app import ReviewStore
from teacher_copilot.worksheets import TOPIC_CONTENTS


def main():
    root = Path(__file__).resolve().parent / 'outputs'
    out = root / 'word_export_acceptance'
    out.mkdir(parents=True, exist_ok=True)
    store = ReviewStore(root)
    for difficulty, minutes in [('basic', 10), ('exam', 20)]:
        state = store.mutate(dict(action='generate', settings=dict(topic='csa-arrays',
            contents=TOPIC_CONTENTS['csa-arrays'], difficulty=difficulty, minutes=minutes, purpose='homework')))
        for audience in ['student', 'teacher']:
            result = store.mutate(dict(action='export', format='docx', audience=audience,
                run=state['run'], version=state['version']))
            path = out / f'arrays-{minutes}min-{audience}.docx'
            path.write_bytes(base64.b64decode(result['download']))
            print(path)


if __name__ == '__main__':
    main()
