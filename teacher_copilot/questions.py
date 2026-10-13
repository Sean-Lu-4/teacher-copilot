"""Versioned question records and review state, independent of the generator.

Content stays in its established format, without rewriting code or answer text.
Review state is never inferred from a structural validation pass.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from .storage import atomic_json, fingerprint

SCHEMA_VERSION = 1
REQUIRED_TEXT = ('id', 'title', 'origin', 'code', 'task', 'answer', 'rubric', 'intervention')
REQUIRED_LISTS = ('objectives', 'reasoning', 'errors')


def content_hash(content):
    return fingerprint(json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(',', ':')))


def validate_content(content):
    if not isinstance(content, dict):
        raise ValueError('Question content must be an object.')
    for name in REQUIRED_TEXT:
        if not isinstance(content.get(name), str) or not content[name].strip():
            raise ValueError(f'Question requires nonempty {name}.')
    for name in REQUIRED_LISTS:
        value = content.get(name)
        if not isinstance(value, list) or not value or any(not isinstance(v, str) or not v.strip() for v in value):
            raise ValueError(f'Question requires a nonempty list of {name}.')
    if type(content.get('level')) is not int or not 1 <= content['level'] <= 4:
        raise ValueError('Difficulty level must be 1 through 4.')
    if type(content.get('minutes')) is not int or content['minutes'] <= 0:
        raise ValueError('Question minutes must be a positive integer.')
    if 'marks' in content and (type(content['marks']) is not int or not 1 <= content['marks'] <= 100):
        raise ValueError('每题分值必须是 1 至 100 的整数。')
    if 'options' in content:
        options = content['options']
        if (not isinstance(options, dict) or len(options) < 2
                or any(not isinstance(v, str) or not v.strip() for v in options.values())):
            raise ValueError('Multiple choice questions require at least two nonempty options.')
        if content.get('answer_key') not in options:
            raise ValueError('Answer key must name an existing option.')
        distractors = content.get('distractors')
        if (not isinstance(distractors, dict) or set(distractors) != set(options) - {content['answer_key']}
                or any(not isinstance(v, str) or not v.strip() for v in distractors.values())):
            raise ValueError('Every incorrect option requires an explanation.')
    elif 'answer_key' in content or 'distractors' in content:
        raise ValueError('Answer keys and distractors require options.')


def pending_validation():
    return dict(teacher_review='pending', technical_review='pending', difficulty_trial='pending')


def create_record(content, bank_version, provenance):
    record = dict(schema_version=SCHEMA_VERSION, bank_version=bank_version,
                  content=deepcopy(content), provenance=deepcopy(provenance),
                  revision=1, locked=False, validation=pending_validation(), history=[])
    record['content_hash'] = content_hash(record['content'])
    validate_record(record)
    return record


def validate_record(record):
    if not isinstance(record, dict) or record.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('Unsupported question schema version.')
    validate_content(record.get('content'))
    if record.get('content_hash') != content_hash(record['content']):
        raise ValueError('Question content changed outside the revision workflow.')
    if not isinstance(record.get('bank_version'), str) or not record['bank_version'].strip():
        raise ValueError('Question bank version is required.')
    if type(record.get('revision')) is not int or record['revision'] < 1:
        raise ValueError('Invalid revision.')
    if type(record.get('locked')) is not bool or not isinstance(record.get('history'), list):
        raise ValueError('Invalid question history or lock state.')
    provenance = record.get('provenance')
    if not isinstance(provenance, dict) or provenance.get('kind') not in {'original', 'textbook', 'adapted'}:
        raise ValueError('Provenance must be original, textbook, or adapted.')
    sources = provenance.get('sources')
    if not isinstance(sources, list):
        raise ValueError('Provenance sources must be a list.')
    if provenance['kind'] != 'original' and not sources:
        raise ValueError('Textbook and adapted questions need actual source references.')
    for source in sources:
        if (not isinstance(source, dict) or not isinstance(source.get('file'), str)
                or not source['file'].strip() or type(source.get('page')) is not int or source['page'] < 1):
            raise ValueError('Each source needs a file name and positive PDF page number.')
    if provenance['kind'] == 'adapted' and not str(provenance.get('changes', '')).strip():
        raise ValueError('Adapted questions must describe their changes.')
    validation = record.get('validation')
    if (not isinstance(validation, dict) or set(validation) != set(pending_validation())
            or any(v not in {'pending', 'passed', 'failed'} for v in validation.values())):
        raise ValueError('Invalid review status.')
    return record


def _event(record, action, actor, detail):
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError('A reviewer/editor name is required.')
    record['history'].append(dict(action=action, actor=actor, detail=detail,
                                  revision=record['revision'], at=datetime.now(timezone.utc).isoformat()))


def revise(record, changes, actor, reason):
    validate_record(record)
    if record['locked']:
        raise ValueError('Unlock this question explicitly before editing it.')
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError('A revision reason is required.')
    if not isinstance(changes, dict) or not changes:
        raise ValueError('Provide content fields to change.')
    if 'id' in changes and changes['id'] != record['content']['id']:
        raise ValueError('Question identity cannot change during a revision.')
    result = deepcopy(record)
    result['content'].update(deepcopy(changes))
    result['revision'] += 1
    result['content_hash'] = content_hash(result['content'])
    result['validation'] = pending_validation()
    _event(result, 'revise', actor, dict(reason=reason, previous_content=deepcopy(record['content']),
                                       previous_validation=deepcopy(record['validation'])))
    return validate_record(result)


def set_locked(record, locked, actor):
    validate_record(record)
    if type(locked) is not bool:
        raise ValueError('Lock state must be true or false.')
    result = deepcopy(record)
    result['locked'] = locked
    _event(result, 'lock' if locked else 'unlock', actor, {})
    return validate_record(result)


def review(record, check, status, actor, evidence):
    validate_record(record)
    if check not in pending_validation() or status not in {'passed', 'failed'}:
        raise ValueError('Unknown review check or status.')
    if not isinstance(evidence, str) or not evidence.strip():
        raise ValueError('Record the evidence for this review.')
    result = deepcopy(record)
    result['validation'][check] = status
    _event(result, 'review', actor, dict(check=check, status=status, evidence=evidence))
    return validate_record(result)


def save_questions(path, records):
    for record in records:
        validate_record(record)
    ids = [r['content']['id'] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError('Question IDs must be unique.')
    atomic_json(path, dict(schema_version=SCHEMA_VERSION, questions=records))


def load_questions(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != SCHEMA_VERSION or not isinstance(data.get('questions'), list):
        raise ValueError('Unsupported question file.')
    records = [validate_record(r) for r in data['questions']]
    if len({r['content']['id'] for r in records}) != len(records):
        raise ValueError('Question IDs must be unique.')
    return records
