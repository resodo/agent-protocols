"""Exercise lifecycle transitions with real subprocesses and isolated fake providers."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import test_claude_structured_review as original_tests

SCRIPT, csr, run_git = original_tests.SCRIPT, original_tests.csr, original_tests.run_git


FAKE = r'''#!/usr/bin/env python3
import json, os, signal, subprocess, sys, time
from pathlib import Path
base = Path(__file__).parent
if '--version' in sys.argv:
    print(json.loads((base / 'options.json').read_text()).get('version', 'fake-provider 1.0'))
    raise SystemExit(0)
options = json.loads((base / 'options.json').read_text())
(base / 'argv.json').write_text(json.dumps(sys.argv))
resume = '--resume' in sys.argv or 'resume' in sys.argv
codex = 'exec' in sys.argv
session = '12345678-1234-4234-8234-123456789abc'
if resume and options.get('missing'):
    print('No conversation found', file=sys.stderr)
    raise SystemExit(1)
if resume and options.get('mismatch'):
    session = '87654321-1234-4234-8234-123456789abc'
if not options.get('no_session'):
    event = {'type':'thread.started','thread_id':session} if codex else {'type':'system','subtype':'hook_started','session_id':session}
    print(json.dumps(event), flush=True)
if not options.get('no_stdin'):
    sys.stdin.read()
if not resume and not options.get('finish'):
    if options.get('ignore_term'): signal.signal(signal.SIGTERM, signal.SIG_IGN)
    if options.get('child'):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])
        (base / 'child.pid').write_text(str(child.pid))
    print('{"partial":', end='', flush=True)
    if options.get('close_pipes'):
        os.close(1); os.close(2)
    time.sleep(120)
text = '### Reviewer pass 1 (impl-plan, reviewer)\n\nNo blocking issues. Prior evidence retained.'
if codex:
    print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':text}}), flush=True)
    if '--output-last-message' in sys.argv:
        Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(text)
    print(json.dumps({'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':5}}), flush=True)
else:
    print(json.dumps({'type':'assistant','message':{'content':[{'type':'text','text':text}]}}), flush=True)
    print(json.dumps({'type':'result','subtype':'success','is_error':False,'result':text,'session_id':session}), flush=True)
'''


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.helper = original_tests.ClaudeStructuredReviewTests()
        self.helper.setUp()
        self.addCleanup(self.helper.tearDown)
        self.root = self.helper.root
        self.repo = self.helper.init_target_repo()
        self.protocol = self.helper.init_protocol_dir()
        self.bin = self.root / 'fake-provider'
        self.bin.write_text(FAKE)
        self.bin.chmod(0o755)
        self.options()
        self.initial = self.root / 'attempt'

    def options(self, **options):
        (self.root / 'options.json').write_text(json.dumps(options))

    def config(self, backend='claude', write=False):
        return self.helper.config_for(self.repo, self.protocol,
            mode=csr.MODE_WRITE if write else csr.MODE_PRINT,
            topic='recovery' if write else None,
            extra=['--reviewer-backend', backend, '--claude-bin', str(self.bin),
                   '--codex-bin', str(self.bin), '--timeout-sec', '1',
                   '--run-log-dir', str(self.initial)])

    def timeout(self, config=None):
        config = config or self.config()
        started = time.monotonic()
        with self.assertRaisesRegex(csr.RunnerError, 'timed out') as raised:
            csr.run(config)
        self.assertEqual(raised.exception.exit_code, 2)
        self.assertLess(time.monotonic() - started, 10)
        state = csr.read_json(self.initial / 'metadata.json')
        self.assertEqual(state['outcome'], 'timeout')
        self.assertTrue(state['cleanup_complete'])
        return config

    def resumed(self, config):
        return replace(config, run_log_dir=None, resume_run=self.initial, timeout_sec=10)

    def test_profiles_default_and_override_for_both_backends(self):
        for backend in ('claude', 'codex'):
            for tier, limit in [('normal',1800), ('auto',1800), ('hard',3600)]:
                extra=['--reviewer-backend', backend, '--review-tier', tier]
                if tier=='hard': extra += ['--tier-reason','recovery correctness']
                config=self.helper.config_for(self.repo,self.protocol,extra=extra)
                self.assertEqual(config.timeout_sec,limit)
                self.assertEqual(config.timeout_source,'profile')
                explicit=self.helper.config_for(self.repo,self.protocol,extra=extra+['--timeout-sec','17'])
                self.assertEqual(explicit.timeout_sec,17)
                self.assertEqual(explicit.timeout_source,'explicit --timeout-sec')

    def test_both_backends_timeout_resume_and_exactly_one_commit(self):
        for backend in ('claude','codex'):
            with self.subTest(backend=backend):
                self.initial=self.root/backend
                config=self.timeout(self.config(backend,write=True))
                head=run_git(self.repo,'rev-parse','HEAD')
                csr.run(self.resumed(config))
                latest=Path(csr.read_json(self.initial/'chain.json')['latest_attempt'])
                state=csr.read_json(latest/'metadata.json')
                self.assertEqual(state['outcome'],'success')
                self.assertTrue(state['session_observed'])
                self.assertEqual(state['attempt_number'],2)
                self.assertGreater(state['cumulative_elapsed_sec'],state['elapsed_sec'])
                self.assertEqual(run_git(self.repo,'rev-list','--count',f'{head}..HEAD'),'1')
                self.assertEqual(csr.read_json(self.initial/'metadata.json')['outcome'],'timeout')
                argv=json.loads((self.root/'argv.json').read_text())
                self.assertIn('12345678-1234-4234-8234-123456789abc',argv)
                if backend=='codex':
                    self.assertIn('sandbox_mode="workspace-write"',argv)
                    self.assertNotIn('--sandbox',argv)
                else:
                    self.assertIn('--permission-mode',argv)
                    self.assertIn('--resume',argv)
                with self.assertRaisesRegex(csr.RunnerError,'stale attempt'):
                    csr.run(self.resumed(config))
                with self.assertRaisesRegex(csr.RunnerError,'not resumable: outcome=success'):
                    csr.run(replace(self.resumed(config),resume_run=latest))
                self.assertEqual(run_git(self.repo,'rev-list','--count',f'{head}..HEAD'),'1')

    def test_resume_rejects_each_nonterminal_or_finalization_state(self):
        config=self.timeout()
        path=self.initial/'metadata.json'
        original=csr.read_json(path)
        for outcome in ('running','finalizing','success','failed','error'):
            csr.atomic_json(path,{**original,'outcome':outcome})
            with self.subTest(outcome=outcome), self.assertRaisesRegex(csr.RunnerError,f'not resumable: outcome={outcome}'):
                csr.run(self.resumed(config))
        self.assertFalse((self.initial/'attempts').exists())

    def test_missing_session_unverified_cleanup_and_invalid_uuid(self):
        config=self.timeout()
        path=self.initial/'metadata.json'
        original=csr.read_json(path)
        for changes,error in [({'session_id':None},'no valid captured'),({'session_id':'--last'},'no valid captured'),({'cleanup_complete':False},'cleanup was not verified')]:
            csr.atomic_json(path,{**original,**changes})
            with self.assertRaisesRegex(csr.RunnerError,error): csr.run(self.resumed(config))
        self.assertFalse((self.initial/'attempts').exists())

    def test_target_and_reviewer_fingerprint_changes_rejected(self):
        config=self.timeout()
        for changed in (replace(config,focus='Different scope'),replace(config,model='other-model'),replace(config,effort='high')):
            with self.assertRaisesRegex(csr.RunnerError,'target or reviewer constraints changed'):
                csr.run(self.resumed(changed))
        (self.protocol/'SKILL.md').write_text('Changed protocol')
        with self.assertRaisesRegex(csr.RunnerError,'target or reviewer constraints changed'): csr.run(self.resumed(config))

    def test_dirty_and_committed_target_changes_rejected(self):
        config=self.timeout()
        (self.repo/'docs/plan.md').write_text('# Changed\n')
        with self.assertRaisesRegex(csr.RunnerError,'worktree must be clean'): csr.run(self.resumed(config))
        run_git(self.repo,'add','.')
        run_git(self.repo,'commit','-m','changed target')
        with self.assertRaisesRegex(csr.RunnerError,'target or reviewer constraints changed'): csr.run(self.resumed(config))

    def test_concurrent_resume_and_stale_stop_rejected(self):
        config=self.timeout()
        with self.assertRaisesRegex(csr.RunnerError,'cannot accompany --resume-run'):
            csr.run(replace(config,resume_run=self.initial))
        with csr.chain_lock(self.initial):
            with self.assertRaisesRegex(csr.RunnerError,'already running'): csr.run(self.resumed(config))
        csr.run(self.resumed(config))
        with self.assertRaisesRegex(csr.RunnerError,'stale attempt'): csr.request_stop(self.initial,'stop')

    def test_missing_provider_history_or_wrong_session_never_writes(self):
        for backend,option in [('claude','missing'),('codex','mismatch')]:
            with self.subTest(backend=backend):
                self.initial=self.root/backend
                self.options()
                config=self.timeout(self.config(backend,write=True))
                head=run_git(self.repo,'rev-parse','HEAD')
                self.options(**{option:True})
                with self.assertRaisesRegex(csr.RunnerError,'did not confirm|did not resume'):
                    csr.run(self.resumed(config))
                latest=Path(csr.read_json(self.initial/'chain.json')['latest_attempt'])
                self.assertEqual(csr.read_json(latest/'metadata.json')['outcome'],'failed')
                self.assertEqual(run_git(self.repo,'rev-parse','HEAD'),head)
                self.assertEqual(run_git(self.repo,'status','--porcelain'),'')

    def test_failure_between_append_and_commit_is_terminal(self):
        config=self.timeout(self.config(write=True))
        target=self.repo/'docs/plan.md'
        original=target.read_text()
        head=run_git(self.repo,'rev-parse','HEAD')
        def fail(config,text):
            target.write_text(original+text)
            raise OSError('injected before commit')
        with mock.patch.object(csr,'append_and_commit_review',fail):
            with self.assertRaisesRegex(csr.RunnerError,'injected before commit'): csr.run(self.resumed(config))
        latest=Path(csr.read_json(self.initial/'chain.json')['latest_attempt'])
        self.assertEqual(csr.read_json(latest/'metadata.json')['outcome'],'error')
        target.write_text(original)  # Remove the dirty-state precondition to exercise eligibility itself.
        with self.assertRaisesRegex(csr.RunnerError,'not resumable: outcome=error'):
            csr.run(replace(self.resumed(config),resume_run=latest))
        self.assertEqual(run_git(self.repo,'rev-parse','HEAD'),head)

    def test_late_signal_during_finalization_is_recorded_not_replayed(self):
        self.options(finish=True)
        config=self.config(write=True)
        original=csr.append_and_commit_review
        def append(config,text):
            os.kill(os.getpid(),signal.SIGTERM)
            csr.atomic_json(self.initial/'stop-request.json',{'reason':'late request race'})
            original(config,text)
        with mock.patch.object(csr,'append_and_commit_review',append): csr.run(config)
        state=csr.read_json(self.initial/'metadata.json')
        self.assertEqual(state['outcome'],'success')
        self.assertEqual(state['late_signals'],[signal.SIGTERM])
        self.assertEqual(state['late_stop_request']['reason'],'late request race')
        with self.assertRaisesRegex(csr.RunnerError,'not resumable'): csr.run(self.resumed(config))

    def launch(self):
        output=(self.root/'runner.log').open('w')
        self.addCleanup(output.close)
        argv=[sys.executable,str(SCRIPT),'--worktree',str(self.repo),'--protocol-dir',str(self.protocol),
              '--mode','print-review','--type','impl-plan','--artifact','docs/plan.md','--focus','Review the plan.',
              '--reviewer-backend','claude','--review-tier','normal','--claude-bin',str(self.bin),
              '--timeout-sec','20','--run-log-dir',str(self.initial)]
        proc=subprocess.Popen(argv,stdout=output,stderr=output)
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            state=csr.read_json(self.initial/'metadata.json')
            if state.get('session_observed'): return proc, state
            if proc.poll() is not None: self.fail((self.root/'runner.log').read_text())
            time.sleep(.05)
        self.fail('session was not captured while running')

    def test_stop_command_and_signals_cleanup_and_can_resume(self):
        for mode,code in [('stop',3),(signal.SIGINT,130),(signal.SIGTERM,143)]:
            with self.subTest(mode=mode):
                self.initial=self.root/str(mode)
                self.options(child=True)
                proc,state=self.launch()
                self.assertEqual(state['outcome'],'running')
                if mode=='stop':
                    self.assertEqual(csr.main(['--stop-run',str(self.initial),'--stop-reason','Controlled test stop']),0)
                else: proc.send_signal(mode)
                self.assertEqual(proc.wait(timeout=15),code)
                terminal=csr.read_json(self.initial/'metadata.json')
                self.assertTrue(terminal['cleanup_complete'])
                self.assertFalse(csr.group_is_executing(terminal['reviewer_pgid']))
                self.assertEqual(terminal['outcome'],'stopped' if mode=='stop' else 'interrupted')
                csr.run(self.resumed(self.config()))

    def test_no_live_runner_stop_does_not_signal_recorded_pid(self):
        self.timeout()
        path=self.initial/'metadata.json'
        state=csr.read_json(path)
        csr.atomic_json(path,{**state,'outcome':'running','runner_pid':os.getpid()})
        with self.assertRaisesRegex(csr.RunnerError,'no live runner'): csr.request_stop(self.initial,'stop')
        self.assertFalse((self.initial/'stop-request.json').exists())

    def test_graceful_stop_escalates_when_reviewer_ignores_sigterm(self):
        self.options(ignore_term=True, child=True)
        self.timeout()
        state=csr.read_json(self.initial/'metadata.json')
        self.assertTrue(state['cleanup_complete'])
        self.assertFalse(csr.group_is_executing(state['reviewer_pgid']))

    def test_uncaptured_session_cannot_resume(self):
        self.options(no_session=True)
        config=self.timeout()
        self.assertIsNone(csr.read_json(self.initial/'metadata.json')['session_id'])
        with self.assertRaisesRegex(csr.RunnerError,'no valid captured session ID'):
            csr.run(self.resumed(config))

    def test_binary_version_change_rejected(self):
        config=self.timeout()
        self.options(version='fake-provider 2.0')
        with self.assertRaisesRegex(csr.RunnerError,'target or reviewer constraints changed'):
            csr.run(self.resumed(config))

    def test_cleanup_verification_failure_is_not_resumable(self):
        self.options(finish=True)
        config=self.config()
        with mock.patch.object(csr,'group_is_executing',side_effect=csr.RunnerError('cannot verify reviewer process-group cleanup')):
            with self.assertRaisesRegex(csr.RunnerError,'cannot verify'):
                csr.run(config)
        self.assertEqual(csr.read_json(self.initial/'metadata.json')['outcome'],'failed')
        with self.assertRaisesRegex(csr.RunnerError,'not resumable: outcome=failed'):
            csr.run(self.resumed(config))

    def test_timeout_with_partial_line_closed_pipes_and_blocked_stdin(self):
        for options in ({'child':True},{'close_pipes':True},{'no_stdin':True}):
            with self.subTest(options=options):
                self.initial=self.root/next(iter(options))
                self.options(**options)
                config=self.config()
                if options.get('no_stdin'): config=replace(config,focus='x'*200000)
                self.timeout(config)
                self.assertFalse(csr.group_is_executing(csr.read_json(self.initial/'metadata.json')['reviewer_pgid']))


if __name__=='__main__': unittest.main()
