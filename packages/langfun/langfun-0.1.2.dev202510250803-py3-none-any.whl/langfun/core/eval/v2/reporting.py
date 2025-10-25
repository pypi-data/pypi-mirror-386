# Copyright 2024 The Langfun Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Reporting evaluation results."""

import os
import threading
import time
import traceback
from typing import Annotated

from langfun.core.eval.v2 import example as example_lib
from langfun.core.eval.v2 import experiment as experiment_lib
import pyglove as pg

Runner = experiment_lib.Runner
Experiment = experiment_lib.Experiment
Example = example_lib.Example


_SUMMARY_FILE = 'summary.html'
_EVALULATION_DETAIL_FILE = 'index.html'


class HtmlReporter(experiment_lib.Plugin):
  """Plugin for periodically generating HTML reports for the experiment."""

  summary_interval: Annotated[
      int,
      'The interval of writing summary in seconds.'
  ] = 60

  experiment_report_interval: Annotated[
      int,
      'The interval of writing report for inidividual experiments in seconds.'
  ] = 120

  def _on_bound(self):
    super()._on_bound()
    self._last_summary_time = 0
    self._last_experiment_report_time = {}
    self._update_thread = None
    self._stop_update = False
    self._stop_update_experiment_ids = set()
    self._summary_lock = None
    self._experiment_index_lock = None

  def on_run_start(
      self,
      runner: Runner,
      root: Experiment
  ) -> None:
    self._last_experiment_report_time = {leaf.id: 0 for leaf in root.leaf_nodes}
    self._stop_update = False
    self._stop_update_experiment_ids = set()
    self._summary_lock = threading.Lock()
    self._experiment_index_lock = {
        leaf.id: threading.Lock() for leaf in root.leaf_nodes
    }
    self._update_thread = threading.Thread(
        target=self._update_thread_func, args=(runner,)
    )
    self._update_thread.start()

  def on_run_complete(
      self,
      runner: Runner,
      root: Experiment
  ) -> None:
    self._stop_update = True
    self._maybe_update_summary(runner, force=True)

  def on_run_abort(
      self,
      runner: Runner,
      root: Experiment,
      error: BaseException
  ) -> None:
    self._stop_update = True
    self._maybe_update_summary(runner, force=True)

  def _update_thread_func(self, runner: Runner):
    while not self._stop_update:
      self._maybe_update_summary(runner, background=False)
      for leaf in runner.current_run.experiment.leaf_nodes:
        if leaf.id in self._stop_update_experiment_ids:
          continue
        self._maybe_update_experiment_html(runner, leaf, background=False)
        if leaf.progress.is_stopped:
          self._stop_update_experiment_ids.add(leaf.id)
      time.sleep(5)

  def on_experiment_start(
      self,
      runner: Runner,
      experiment: Experiment
  ) -> None:
    if experiment.is_leaf:
      self._maybe_update_experiment_html(runner, experiment)

  def on_experiment_complete(
      self, runner: Runner, experiment: Experiment
  ):
    if experiment.is_leaf:
      self._maybe_update_experiment_html(runner, experiment, force=True)

  def on_experiment_abort(
      self,
      runner: Runner,
      experiment: Experiment,
      error: BaseException
  ) -> None:
    del error
    assert experiment.is_leaf
    self._maybe_update_experiment_html(runner, experiment, force=True)

  def on_example_complete(
      self, runner: Runner, experiment: Experiment, example: Example
  ):
    self._save_example_html(runner, experiment, example)
    self._maybe_update_experiment_html(runner, experiment)
    self._maybe_update_summary(runner)

  def _maybe_update_summary(
      self,
      runner: Runner,
      background: bool = True,
      force: bool = False) -> None:
    """Maybe update the summary of current run."""
    run = runner.current_run
    def _summary():
      html = run.experiment.to_html(
          collapse_level=None,
          extra_flags=dict(
              current_run=run, interactive=False, card_view=True,
          )
      )
      with self._summary_lock:
        html.save(os.path.join(run.output_root, _SUMMARY_FILE))

    if force or (time.time() - self._last_summary_time > self.summary_interval):
      self._last_summary_time = time.time()
      if background:
        runner.background_run(_summary)
      else:
        _summary()

  def _maybe_update_experiment_html(
      self,
      runner: Runner,
      experiment: Experiment,
      force: bool = False,
      background: bool = True,
  ) -> None:
    def _save():
      index_html_path = runner.current_run.output_path_for(
          experiment, _EVALULATION_DETAIL_FILE
      )
      try:
        with pg.timeit() as t:
          html = experiment.to_html(
              collapse_level=None,
              extra_flags=dict(
                  current_run=runner.current_run,
                  interactive=False,
                  card_view=False,
              ),
          )
          with self._experiment_index_lock[experiment.id]:
            html.save(index_html_path)
          experiment.info(
              f'Updated {index_html_path!r} in {t.elapse:.2f} seconds.',
          )
      except BaseException as e:  # pylint: disable=broad-except
        experiment.error(
            f'Failed to generate {index_html_path!r}. '
            f'Error: {e}, Stacktrace: \n{traceback.format_exc()}.',
        )
        raise e

    if force or (
        time.time() - self._last_experiment_report_time[experiment.id]
        > self.experiment_report_interval
    ):
      self._last_experiment_report_time[experiment.id] = time.time()
      if background:
        runner.background_run(_save)
      else:
        _save()

  def _save_example_html(
      self, runner: Runner, experiment: Experiment, example: Example
  ) -> None:
    """Saves the example in HTML format."""
    current_run = runner.current_run
    def _generate():
      try:
        with pg.timeit() as t:
          html = example.to_html(
              collapse_level=None,
              enable_summary_tooltip=False,
              extra_flags=dict(
                  # For properly rendering the next link.
                  num_examples=getattr(experiment, 'num_examples', None)
              ),
          )
          html.save(
              runner.current_run.output_path_for(
                  experiment, f'{example.id}.html'
              )
          )
        experiment.info(
            f'\'{example.id}.html\' generated in {t.elapse:.2f} seconds. '
        )
      except BaseException as e:  # pylint: disable=broad-except
        experiment.error(
            f'Failed to generate \'{example.id}.html\'. '
            f'Error: {e}, Stacktrace: \n{traceback.format_exc()}.',
        )
        raise e

    def _copy():
      src_file = current_run.input_path_for(experiment, f'{example.id}.html')
      dest_file = current_run.output_path_for(experiment, f'{example.id}.html')

      if src_file == dest_file:
        return

      if not pg.io.path_exists(src_file):
        experiment.warning(
            f'Skip copying \'{example.id}.html\' as '
            f'{src_file!r} does not exist.'
        )
        return

      try:
        with pg.timeit() as t, pg.io.open(src_file, 'r') as src:
          content = src.read()
          with pg.io.open(dest_file, 'w') as dest:
            dest.write(content)
        experiment.info(
            f'\'{example.id}.html\' copied in {t.elapse:.2f} seconds.'
        )
      except BaseException as e:  # pylint: disable=broad-except
        experiment.error(
            f'Failed to copy {src_file!r} to {dest_file!r}. Error: {e}.'
        )
        raise e

    generate_example_html = current_run.generate_example_html
    if (generate_example_html == 'all'
        or (generate_example_html == 'new' and example.newly_processed)
        or (isinstance(generate_example_html, list)
            and example.id in generate_example_html)):
      op = _generate
    else:
      op = _copy
    runner.background_run(op)
