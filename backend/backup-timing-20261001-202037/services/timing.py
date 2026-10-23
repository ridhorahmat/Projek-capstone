from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import json
import logging
from pathlib import Path
from time import perf_counter, time
from uuid import uuid4

_log = logging.getLogger('uvicorn.error')
_run = ContextVar('timing_run', default='-')

@contextmanager
def stage(name):
    started = perf_counter()
    _log.info('[WAKTU] %s | %s | mulai', _run.get(), name)
    status = 'selesai'
    try:
        yield
    except BaseException:
        status = 'gagal/terhenti'
        raise
    finally:
        _log.info('[WAKTU] %s | %s | %s | %.2f detik',
                  _run.get(), name, status, perf_counter() - started)

def timed_request(kind):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            req = args[0] if args else kwargs.get('req')
            label = getattr(req, 'job_id', None) or uuid4().hex[:8]
            token = _run.set(label)
            started = perf_counter()
            wall_started = time()
            try:
                with stage('TOTAL ' + kind):
                    result = function(*args, **kwargs)
                duration = perf_counter() - started
                job_id = result['job_id']
                _log.info('[WAKTU] %s | pekerjaan %s', label, job_id)
                timing_file = Path(__file__).resolve().parent.parent / 'outputs' / job_id / 'timings.json'
                # Diagnostic records must never turn a successful request into an error.
                try:
                    if kind == 'analisis':
                        timing_file.write_text(json.dumps({
                            'analysis_seconds': duration,
                            'started_at': wall_started,
                        }), encoding='utf-8')
                    elif timing_file.exists():
                        saved = json.loads(timing_file.read_text(encoding='utf-8'))
                        _log.info('[WAKTU] %s | TOTAL proses aktif (analisis + render ini): %.2f detik',
                                  job_id, saved['analysis_seconds'] + duration)
                        _log.info('[WAKTU] %s | waktu sejak mulai analisis (termasuk jeda pengguna): %.2f detik',
                                  job_id, time() - saved['started_at'])
                    else:
                        _log.info('[WAKTU] %s | total gabungan tidak tersedia: analisis lama belum dicatat', job_id)
                except (OSError, ValueError, KeyError, TypeError):
                    _log.warning('[WAKTU] %s | catatan gabungan tidak tersedia; hasil video tetap tersedia', job_id)
                return result
            finally:
                _run.reset(token)
        return wrapped
    return decorate
