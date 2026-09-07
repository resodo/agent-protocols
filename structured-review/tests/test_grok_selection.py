"""Provider wire fixtures and executable selection/recovery controls.

Claude quota and Grok init/result shapes were observed in the 2026-09-07
bootstrap. Codex messages are source-backed by upstream protocol/src/error.rs
(UsageLimitReachedError/QuotaExceeded), not observed account exhaustion.
All identities, reset values, and review content below are synthetic.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import time
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import test_claude_structured_review as original

csr = original.csr
git = original.run_git

FAKE = r'''#!/usr/bin/env python3
import json, sys, time
from pathlib import Path
base=Path(__file__).parent
name=Path(__file__).name
if '--version' in sys.argv:
    print(name+' test 1.0')
    raise SystemExit(0)
with (base/'calls.jsonl').open('a') as f: f.write(json.dumps({'backend':name,'argv':sys.argv})+'\n')
options=json.loads((base/'options.json').read_text())
behavior=options.get(name,'success')
resume='--resume' in sys.argv or 'resume' in sys.argv
session='12345678-1234-4234-8234-123456789abc'
def emit(event): print(json.dumps(event),flush=True)
if behavior!='no_session':
    emit({'type':'thread.started','thread_id':session} if name=='codex' else {'type':'system','subtype':'init','session_id':session,'model':'grok-4.6'})
prompt=sys.stdin.read()
if name=='grok':
    assert prompt==''
    prompt=Path(sys.argv[sys.argv.index('--prompt-file')+1]).read_text()
    assert '--session-id' not in sys.argv and '--restore-code' not in sys.argv
if behavior in ('credit','dirty_credit','moved_credit','malformed_credit'):
    if behavior=='dirty_credit': Path('docs/plan.md').write_text('dirty')
    if behavior=='moved_credit':
        import subprocess
        subprocess.run(['git','commit','--allow-empty','-m','unauthorized'],check=True,stdout=sys.stderr)
    if behavior=='malformed_credit': print('{broken',flush=True)
    if name=='claude': emit({'type':'result','subtype':'success','is_error':True,'result':"You've hit your weekly limit · resets SYNTHETIC"})
    elif name=='codex': emit({'type':'turn.failed','error':{'message':"You've hit your usage limit. Try again later."}})
    else: emit({'type':'result','subtype':'error','is_error':True,'result':'Unknown provider failure'})
    raise SystemExit(1)
if behavior in ('auth','network','rate','error'):
    message={'auth':'Authentication failed','network':'Connection failed','rate':'Rate limit exceeded','error':'Unknown error'}[behavior]
    emit({'type':'turn.failed','error':{'message':message}} if name=='codex' else {'type':'result','subtype':'error','is_error':True,'result':message})
    raise SystemExit(1)
if behavior=='timeout' and not resume: time.sleep(120)
text="### Reviewer pass 1 (impl-plan, "+name+" reviewer)\n\nNo blocking issues."
if behavior=='prose': text+=" You've hit your weekly limit · resets SYNTHETIC"
if behavior=='tool_prose': emit({'type':'user','message':{'content':[{'type':'tool_result','content':"You've hit your weekly limit · resets SYNTHETIC"}]}})
if behavior=='malformed': print('{broken',flush=True)
if behavior=='empty': text=''
if name=='codex':
    emit({'type':'item.completed','item':{'type':'agent_message','text':text}})
    Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(text)
    emit({'type':'turn.completed','usage':{'input_tokens':1,'output_tokens':1}})
else:
    emit({'type':'assistant','message':{'content':[{'type':'text','text':text}]}})
    if behavior!='truncated':
        emit({'type':'result','subtype':'success','is_error':False,'stop_reason':'max_turns' if behavior=='max_turns' else 'end_turn','result':text,'session_id':None if behavior=='no_session' else session,'usage':{'input_tokens':2,'output_tokens':3}})
'''


class GrokSelectionTests(unittest.TestCase):
    def setUp(self):
        self.helper = original.ClaudeStructuredReviewTests()
        self.helper.setUp()
        self.addCleanup(self.helper.tearDown)
        self.root = self.helper.root
        self.repo = self.helper.init_target_repo()
        self.protocol = self.helper.init_protocol_dir()
        self.options()
        for backend in csr.BACKEND_ORDER:
            path = self.root / backend
            path.write_text(FAKE)
            path.chmod(0o755)
        self.args = [
            '--worktree', str(self.repo), '--protocol-dir', str(self.protocol),
            '--mode', 'write-commit-to-plan', '--thread-file', 'docs/plan.md',
            '--artifact', 'docs/plan.md', '--topic', 'selection', '--type', 'impl-plan',
            '--focus', 'Check the plan.', '--review-tier', 'normal',
            '--coding-agent', 'codex', '--run-log-dir', str(self.root / 'logs'),
            *[arg for backend in csr.BACKEND_ORDER for arg in (f'--{backend}-bin', str(self.root / backend))],
        ]

    def options(self, **values):
        (self.root / 'options.json').write_text(json.dumps(values))

    def config(self, *extra):
        return csr.config_from_args(csr.parse_args(self.args + list(extra)), env={})

    def calls(self):
        path = self.root / 'calls.jsonl'
        return [json.loads(line)['backend'] for line in path.read_text().splitlines()] if path.exists() else []

    def test_grok_profiles_argv_help_and_override(self):
        for tier, effort, limit in [('normal', 'medium', 1800), ('hard', 'xhigh', 3600)]:
            extra = ['--reviewer-backend', 'grok', '--review-tier', tier]
            if tier == 'hard': extra += ['--tier-reason', 'Unusually difficult recovery bug']
            config = self.config(*extra)
            self.assertEqual((csr.active_model(config), csr.active_effort(config), config.timeout_sec), ('grok-4.6', effort, limit))
            argv = csr.grok_argv(config, self.helper.logs_for(self.root / 'run'))
            self.assertEqual(argv[argv.index('--reasoning-effort')+1], effort)
            self.assertIn('plan', argv)
            resumed = csr.grok_argv(replace(config, resume_session_id='12345678-1234-4234-8234-123456789abc'), self.helper.logs_for(self.root / 'run'))
            self.assertEqual(resumed[:-2], argv)
            self.assertEqual(resumed[-2], '--resume')
        override = self.config('--reviewer-backend', 'grok', '--grok-model', 'grok-4.6', '--grok-effort', 'high')
        self.assertEqual((override.grok_effort, override.effort_source), ('high', 'explicit --grok-effort'))
        with mock.patch('sys.stdout', new_callable=io.StringIO) as out, self.assertRaises(SystemExit):
            csr.parse_args(['--help'])
        self.assertIn('hardest 20%', out.getvalue())
        self.assertIn('--coding-agent', out.getvalue())

    def test_every_driver_exclusion_order(self):
        self.options(claude='credit', codex='credit')
        expected = {'claude':['codex','grok'], 'codex':['claude','grok'],
                    'grok':['claude','codex'], 'kimicode':['claude','codex','grok'],
                    'unknown':['claude','codex','grok']}
        for driver, calls in expected.items():
            (self.root / 'calls.jsonl').unlink(missing_ok=True)
            config = self.config('--coding-agent', driver, '--run-log-dir', str(self.root / driver / 'attempt'))
            # Binary paths already use driver names; allocate logs elsewhere.
            config = replace(config, run_log_dir=self.root / ('attempt-' + driver))
            if driver == 'grok':
                with self.assertRaisesRegex(csr.RunnerError, 'all three backends unavailable or excluded'):
                    csr.run(config)
            else:
                csr.run(config)
            self.assertEqual(self.calls(), calls)

    def test_kimi_selects_available_codex(self):
        self.options(claude='credit')
        csr.run(self.config('--coding-agent', 'kimicode'))
        self.assertEqual(self.calls(), ['claude', 'codex'])

    def test_identity_precedence_and_empty_rejected(self):
        env = {'CLAUDECODE':'1', 'CODEX_THREAD_ID':'x'}
        self.assertEqual(csr.coding_identity(' Grok ', env), 'grok')
        self.assertEqual(csr.coding_identity(None, {'CLAUDECODE':'1'}), 'claude')
        self.assertEqual(csr.coding_identity(None, {'CODEX_THREAD_ID':'x'}), 'codex')
        with self.assertRaisesRegex(csr.RunnerError, 'conflicting'):
            csr.coding_identity(None, env)
        with self.assertRaisesRegex(csr.RunnerError, 'nonempty'):
            csr.coding_identity(' ', {})

    def test_missing_binary_skip_and_all_missing(self):
        config = self.config('--claude-bin', str(self.root / 'absent'))
        csr.run(config)
        self.assertEqual(self.calls(), ['grok'])
        meta = csr.read_json(self.root / 'logs/metadata.json')
        self.assertIn({'backend':'claude','reason':'binary_unavailable'}, meta['selection_history'])
        with self.assertRaisesRegex(csr.RunnerError, 'all three backends unavailable or excluded'):
            csr.run(replace(config, grok_bin=str(self.root / 'absent-grok')))

    def test_pins_never_fall_back(self):
        self.options(claude='credit')
        with self.assertRaises(csr.CreditExhausted): csr.run(self.config('--reviewer-backend','claude'))
        self.assertEqual(self.calls(), ['claude'])

    def test_fallback_profile_provenance_and_single_write(self):
        self.options(claude='credit')
        head = git(self.repo, 'rev-parse', 'HEAD')
        csr.run(self.config('--grok-effort', 'high'))
        self.assertEqual(self.calls(), ['claude', 'grok'])
        self.assertEqual(git(self.repo, 'rev-list', '--count', head+'..HEAD'), '1')
        first = csr.read_json(self.root / 'logs/metadata.json')
        self.assertEqual((first['outcome'], first['reason_category']), ('failed', 'credit_exhausted'))
        self.assertTrue(first['cleanup_complete'])
        following = csr.read_json(self.root / 'logs/selection.json')
        final = csr.read_json(Path(following['next_attempt']) / 'metadata.json')
        self.assertEqual((final['backend'], final['effort'], final['effort_source']), ('grok', 'high', 'explicit --grok-effort'))
        self.assertEqual(final['token_usage'], {'input_tokens':2,'output_tokens':3})

    def test_nonquota_and_dirty_errors_do_not_fall_back(self):
        head = git(self.repo, 'rev-parse', 'HEAD')
        for behavior in ('auth','network','rate','error','dirty_credit','malformed_credit','moved_credit'):
            with self.subTest(behavior=behavior):
                self.options(claude=behavior)
                (self.root / 'calls.jsonl').unlink(missing_ok=True)
                original_text = (self.repo / 'docs/plan.md').read_text()
                with self.assertRaises(csr.RunnerError):
                    csr.run(self.config('--run-log-dir', str(self.root / ('logs-'+behavior))))
                self.assertEqual(self.calls(), ['claude'])
                if behavior == 'dirty_credit':
                    (self.repo / 'docs/plan.md').write_text(original_text)
                if behavior != 'moved_credit': self.assertEqual(git(self.repo,'rev-parse','HEAD'), head)

    def test_quota_like_prose_and_tool_output_are_not_credit(self):
        for behavior in ('prose','tool_prose'):
            self.options(claude=behavior)
            (self.root / 'calls.jsonl').unlink(missing_ok=True)
            csr.run(self.config('--run-log-dir', str(self.root / behavior)))
            self.assertEqual(self.calls(), ['claude'])
        for event in ({'type':'assistant','result':"You've hit your weekly limit · resets X",'is_error':True},
                      {'type':'result','result':"You've hit your weekly limit · resets X",'is_error':False}):
            self.assertIsNone(csr.claude_failure(event))
        self.assertEqual(csr.codex_failure({'type':'turn.failed','error':{'message':'Quota exceeded. Check your plan and billing details.'}}), 'credit_exhausted')
        self.assertIsNone(csr.codex_failure({'type':'item.completed','error':{'message':"You've hit your usage limit."}}))

    def test_grok_incomplete_error_and_malformed_results_never_write(self):
        head = git(self.repo, 'rev-parse', 'HEAD')
        for behavior in ('no_session','truncated','malformed','empty','max_turns','error'):
            self.options(grok=behavior)
            with self.subTest(behavior=behavior), self.assertRaises(csr.RunnerError):
                csr.run(self.config('--reviewer-backend','grok','--run-log-dir',str(self.root / behavior)))
            self.assertEqual(git(self.repo,'rev-parse','HEAD'), head)
            self.assertEqual(git(self.repo,'status','--porcelain'), '')

    def test_auto_resume_keeps_grok_when_claude_recovers_and_rejects_changes(self):
        self.options(claude='credit', grok='timeout')
        config = self.config('--timeout-sec','1')
        with self.assertRaisesRegex(csr.RunnerError,'timed out'): csr.run(config)
        self.assertEqual(self.calls(), ['claude','grok'])
        source = self.root / 'logs/fallback/grok'
        self.options()  # Claude is available again, but resume must not call it.
        args = [arg for arg in self.args]
        index = args.index('--run-log-dir')
        del args[index:index+2]
        args += ['--resume-run', str(source), '--timeout-sec', '10']
        for extra, error in [(['--coding-agent','kimicode'],'identity changed'),
                             (['--reviewer-backend','claude'],'backend disagrees')]:
            with self.assertRaisesRegex(csr.RunnerError,error): csr.config_from_args(csr.parse_args(args+extra),env={})
        resume = csr.config_from_args(csr.parse_args(args), env={})
        csr.run(resume)
        self.assertEqual(self.calls(), ['claude','grok','grok'])
        latest = Path(csr.read_json(source/'chain.json')['latest_attempt'])
        self.assertEqual(csr.read_json(latest/'metadata.json')['outcome'], 'success')
        with self.assertRaisesRegex(csr.RunnerError,'stale attempt'): csr.run(resume)

    def test_failed_writeback_does_not_try_another_provider(self):
        with mock.patch.object(csr,'append_and_commit_review',side_effect=OSError('injected writeback failure')):
            with self.assertRaisesRegex(csr.RunnerError,'writeback failure'): csr.run(self.config())
        self.assertEqual(self.calls(), ['claude'])

    def test_grok_stop_then_same_session_resume_and_profile_guard(self):
        self.options(grok='timeout')
        initial = self.root / 'logs'
        args = self.args + ['--reviewer-backend','grok']
        with (self.root / 'runner.log').open('w') as output:
            proc = subprocess.Popen([sys.executable,str(original.SCRIPT),*args], stdout=output, stderr=output)
            try:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    state = csr.read_json(initial/'metadata.json')
                    if state.get('session_observed'): break
                    if proc.poll() is not None: self.fail('runner exited before session capture')
                    time.sleep(0.05)
                else: self.fail('session was not captured')
                csr.request_stop(initial, 'Exercise real cooperative stop recovery')
                self.assertEqual(proc.wait(timeout=10),3)
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=10)
        state = csr.read_json(initial/'metadata.json')
        self.assertEqual(state['outcome'],'stopped')
        self.assertTrue(state['cleanup_complete'])
        config = replace(self.config('--reviewer-backend','grok'), run_log_dir=None, resume_run=initial, timeout_sec=10)
        for changes in ({'grok_model':'other'}, {'grok_effort':'high'}, {'focus':'changed'}):
            with self.assertRaisesRegex(csr.RunnerError,'constraints changed'):
                csr.run(replace(config,**changes))
        csr.run(config)
        self.assertEqual(self.calls(), ['grok','grok'])
        latest = Path(csr.read_json(initial/'chain.json')['latest_attempt'])
        final = csr.read_json(latest/'metadata.json')
        self.assertEqual(final['session_id'],state['session_id'])
        self.assertEqual(final['outcome'],'success')


if __name__ == '__main__': unittest.main()
