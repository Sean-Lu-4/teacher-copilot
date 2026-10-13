"""Teacher Copilot: offline by default; --online explicitly enables paid APIs."""
from pathlib import Path
from datetime import datetime
import argparse
import os
import tempfile
import sys
from .config import *
from .storage import atomic_json, fingerprint
from .materials import chunk_text, split_page, clean_page, material_info, load_pdf_chunks
from .retrieval import keyword_search, select_material
from .embeddings import load_cache, cached_embedding, semantic_search
from .profiles import METHODS_CALLING, find_candidates, interleave_candidates, summarize, coverage_report, scope_instructions
from .exercises import make_plan, render_report, prompt_requirements
from .reports import retrieval_report, build_prompt
from .questions import create_record, save_questions

def positive_int(value):
    try:
        number = int(value)
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError('Enter a positive whole number.')
    if number <= 0:
        raise argparse.ArgumentTypeError('Enter a positive whole number.')
    return number


def required(value, label):
    if value is not None:
        if value.strip():
            return value.strip()
        raise ValueError(f'{label} cannot be blank.')
    while True:
        value = input(f'{label}: ').strip()
        if value:
            return value
        print('Please enter a value.')


def api_error_message(exc):
    code = getattr(exc, 'code', None)
    if code == 'insufficient_quota':
        return 'API quota exhausted. Use offline mode; completed embeddings are saved.'
    name = type(exc).__name__
    return {
        'RateLimitError': 'API rate limit reached. Try later; saved embeddings will be reused.',
        'AuthenticationError': 'API authentication failed. Check OPENAI_API_KEY.',
        'APIConnectionError': 'Cannot connect to the API. Check your network.',
        'APITimeoutError': 'API request timed out. Check outputs before trying again.',
        'NotFoundError': 'API resource/model unavailable. Check --model and account access.',
        'BadRequestError': 'API rejected the request. Check model support and request settings.',
    }.get(name, f'API request failed ({name}); saved work has been retained.')


def main(argv=None):
    # Some extracted PDF glyphs cannot be printed by older Windows consoles.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--online', action='store_true', help='Enable paid lesson generation')
    parser.add_argument('--profile', choices=['methods-calling'],
                        help='Use the agreed Grade 10 method-calling lesson and offline coverage checklist')
    parser.add_argument('--search', choices=['keyword', 'semantic'], default='keyword')
    parser.add_argument('--model', default=os.getenv('OPENAI_MODEL', 'gpt-6-luna'))
    parser.add_argument('--materials', type=Path, default=MATERIALS_FOLDER)
    parser.add_argument('--unit', type=positive_int, help='Filter the Unit number in PDF filenames')
    parser.add_argument('--material-type', choices=['all', 'lecture', 'workbook'])
    parser.add_argument('--text-cache-dir', type=Path, default=TEXT_CACHE_FOLDER)
    parser.add_argument('--cache', type=Path, default=CACHE_FILE)
    parser.add_argument('--embedding-batch-size', type=positive_int, default=BATCH_SIZE)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT_FOLDER)
    parser.add_argument('--top-k', type=positive_int, default=TOP_K)
    parser.add_argument('--context-chars', type=positive_int, default=4800)
    parser.add_argument('--max-output-tokens', type=positive_int, default=6000)
    parser.add_argument('--min-similarity', type=float, default=0.3,
                        help='Semantic relevance heuristic, not a probability')
    parser.add_argument('--subject')
    parser.add_argument('--level')
    parser.add_argument('--topic')
    parser.add_argument('--duration', type=positive_int)
    parser.add_argument('--objectives')
    args = parser.parse_args(argv)
    profile = METHODS_CALLING if args.profile else None
    if profile:
        if args.search != 'keyword':
            parser.error('Coverage profiles currently use local keyword search; omit --search semantic.')
        if args.topic is not None and args.topic != profile['topic']:
            parser.error('This profile is for method calling. Omit --topic, or omit --profile for another topic.')
        for name in ('subject', 'level', 'topic', 'duration', 'objectives'):
            if getattr(args, name) is None:
                setattr(args, name, profile[name])
        if args.unit is None:
            args.unit = 1
    if args.material_type is None:
        args.material_type = 'lecture' if profile else 'all'
    if args.search == 'semantic' and not args.online:
        parser.error('Semantic search requires --online (paid embeddings). Use keyword offline.')
    if not 0 <= args.min_similarity <= 1:
        parser.error('--min-similarity must be between 0 and 1.')
    print('TEACHER COPILOT — ' + ('ONLINE (paid APIs)' if args.online else 'OFFLINE (no API calls)'))
    course = dict(subject=required(args.subject, 'Subject'), level=required(args.level, 'Level'),
                  topic=required(args.topic, 'Topic'))
    duration = args.duration
    while duration is None:
        try:
            duration = positive_int(input('Duration in minutes: '))
        except argparse.ArgumentTypeError as exc:
            print(exc)
    course['duration'] = duration
    course['objectives'] = (args.objectives if args.objectives is not None
                            else input('Learning objectives (optional): ')).strip()
    chunks = load_pdf_chunks(args.materials, args.unit, args.material_type, args.text_cache_dir)
    client = None
    if args.online:
        from openai import OpenAI
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError('Set OPENAI_API_KEY for online mode. Offline mode needs no key.')
        client = OpenAI(max_retries=0, timeout=60.0)
    query = course['topic'] + '\n' + course['objectives']
    coverage = None
    if profile:
        coverage = find_candidates(profile, chunks, keyword_search)
        results = interleave_candidates(coverage)
    elif args.search == 'semantic':
        try:
            results = semantic_search(client, query, chunks, args.cache, args.min_similarity, args.embedding_batch_size)
        except Exception as exc:
            if type(exc).__module__.startswith('openai'):
                print(api_error_message(exc))
                return 1
            raise
    else:
        results = keyword_search(query, chunks)
    selected = select_material(results, args.top_k, args.context_chars, chunks)
    for score, c in selected:
        print(f"\n{c['file']} | page {c['page']} | chunk {c['chunk']} | score {score:.3f}")
        print(c['text'][:300])
    coverage_summary = summarize(coverage, selected) if coverage is not None else None
    scope = scope_instructions(profile, coverage_summary) if profile else ''
    exercise_plan = make_plan(course, coverage_summary) if profile else None
    if exercise_plan:
        scope += '\n' + prompt_requirements(exercise_plan)
    prompt = build_prompt(course, selected, scope)
    # A unique folder avoids overwriting any previous successful or partial output.
    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y%m%d_%H%M%S_'),
                                    dir=args.output_dir))
    (run_dir / 'retrieval_report.md').write_text(retrieval_report(course, selected, args), encoding='utf-8')
    if profile:
        (run_dir / 'coverage_report.md').write_text(
            coverage_report(profile, course, coverage_summary, args), encoding='utf-8')
        atomic_json(run_dir / 'coverage.json', dict(profile=profile['id'], items=coverage_summary))
        (run_dir / 'exercise_report.md').write_text(render_report(exercise_plan), encoding='utf-8')
        atomic_json(run_dir / 'exercise_plan.json', exercise_plan)
        records = [create_record(q, exercise_plan['version'], dict(kind='original', sources=[]))
                   for q in exercise_plan['questions']]
        save_questions(run_dir / 'questions.json', records)
    if selected:
        (run_dir / 'prompt.md').write_text(prompt, encoding='utf-8')
    metadata = dict(course=course, mode='online' if args.online else 'offline',
                    search=args.search, model=args.model, max_output_tokens=args.max_output_tokens,
                    context_characters=sum(len(c['text']) for _, c in selected),
                    unit=args.unit, material_type=args.material_type,
                    profile=args.profile,
                    exercise_bank_version=exercise_plan['version'] if exercise_plan else None,
                    sources=[dict({k: v for k, v in c.items() if k != 'page_text'}, score=s)
                             for s, c in selected], status='prepared' if selected else 'no_matches')
    atomic_json(run_dir / 'metadata.json', metadata)
    print(f'Prompt and sources saved: {run_dir}')
    if not selected:
        print('No relevant material fits the query/budget. See retrieval_report.md. No lesson generated.')
        return 1
    if not args.online:
        print('Offline preparation complete. No AI lesson was generated and no API tokens were used.')
        return 0
    try:
        response = client.responses.create(model=args.model, input=prompt,
                                           max_output_tokens=args.max_output_tokens)
    except Exception as exc:
        metadata.update(status='request_failed', error_type=type(exc).__name__,
                        error_code=str(getattr(exc, 'code', None)))
        atomic_json(run_dir / 'metadata.json', metadata)
        print(api_error_message(exc))
        return 1
    text = response.output_text or ''
    complete = response.status == 'completed' and bool(text.strip())
    (run_dir / ('lesson.md' if complete else 'lesson_partial.md')).write_text(text, encoding='utf-8')
    metadata.update(status=response.status, response_id=response.id,
                    usage=response.usage.model_dump() if response.usage else None,
                    incomplete_details=response.incomplete_details.model_dump()
                    if response.incomplete_details else None)
    atomic_json(run_dir / 'metadata.json', metadata)
    if not complete:
        print('Response is incomplete or empty. Partial output and details saved; no automatic retry.')
        return 1
    print(text)
    print(f'Lesson saved: {run_dir / "lesson.md"}')
    print(f'Token usage: {metadata["usage"]}')
    return 0


def entrypoint():
    try:
        return main()
    except (ValueError, OSError, ImportError) as exc:
        print(f'Error: {exc}')
        return 1
    except (KeyboardInterrupt, EOFError):
        print('Stopped. Completed cache entries and saved outputs are retained.')
        return 1
