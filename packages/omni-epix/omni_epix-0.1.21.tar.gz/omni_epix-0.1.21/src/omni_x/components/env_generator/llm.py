import tempfile
from dataclasses import dataclass
from pathlib import Path

from omni_x.core import EnvGenerator, Run, Task, log
from omni_x.utils.llm.base import InstructorClient
from omni_x.utils.llm.logging import log_llm_call
from omni_x.utils.llm.prompts import EnvOutput, build_env_fix_messages, build_env_gen_messages
from omni_x.utils.sandbox import SandboxConfig, run_sandboxed


class LLMEnvGenerator(EnvGenerator):
    """Generate environment code using an LLM.

    Uses successful parent tasks as examples, builds prompts, calls LLM, and updates the task.
    If the generated code fails smoke testing, feeds error back to LLM for up to max_fix_attempts.
    """

    @dataclass(frozen=True)
    class Config:
        substrate_description: str
        max_fix_attempts: int
        smoke_test_steps: int
        smoke_test_script: Path
        sandbox: SandboxConfig
        llm: InstructorClient.Config

    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = InstructorClient(config.llm)

    def __call__(self, run: Run, task: Task) -> None:
        assert task.description is not None, "Task must have description before generating environment"  # type narrow

        parents = [run.archive.get(idx) for idx in task.parents or []]
        example_tasks = [t for t in parents if t.success is not None and t.success]

        # initial env generation
        messages = build_env_gen_messages(
            substrate_desc=self.config.substrate_description,
            task_description=task.description,
            example_tasks=example_tasks,
        )

        result, completion = self.client.create_with_completion(response_model=EnvOutput, messages=messages)
        generated_code = result.code

        metadata = log_llm_call(
            log_dir=run.resolve_path(run.paths.llm_log_dir, task.id),
            task_id=task.id,
            step="env_generator",
            result=result,
            completion=completion,
        )
        task.metadata.setdefault("llm_calls", []).append(metadata)

        # smoke test loop - try to fix compile/runtime errors
        for attempt in range(max(self.config.max_fix_attempts + 1, 1)):
            smoke_test_passed, error_traceback = self._run_smoke_test(
                generated_code, run=run, task=task, attempt=attempt
            )

            if smoke_test_passed:
                task.code = generated_code
                log(f"Smoke test passed attempt {attempt + 1}", run=run, task=task)
                return
            log(f"Smoke test failed attempt {attempt + 1}/{self.config.max_fix_attempts + 1}", run=run, task=task)

            if attempt >= self.config.max_fix_attempts:
                log("Max fix attempts reached. Discarding task.", run=run, task=task)
                task.done = True
                return

            fix_messages = build_env_fix_messages(
                substrate_desc=self.config.substrate_description,
                task_description=task.description,
                previous_code=generated_code,
                error_traceback=error_traceback,
                example_tasks=example_tasks,
            )

            result, completion = self.client.create_with_completion(response_model=EnvOutput, messages=fix_messages)
            generated_code = result.code

            code_log_file = run.resolve_path(run.paths.smoke_test_log_dir, task.id) / f"attempt_{attempt + 1}.py"
            code_log_file.parent.mkdir(parents=True, exist_ok=True)
            code_log_file.write_text(generated_code)
            fix_metadata = log_llm_call(
                log_dir=run.resolve_path(run.paths.llm_log_dir, task.id),
                task_id=task.id,
                step=f"env_generator_fix_{attempt + 1}",
                result=result,
                completion=completion,
            )
            task.metadata.setdefault("llm_calls", []).append(fix_metadata)

    def _run_smoke_test(self, code: str, run: Run, task: Task, attempt: int) -> tuple[bool, str]:
        """Run smoke test on generated code.

        Returns:
            (success, error_traceback): success is True if smoke test passed, error_traceback contains stderr if failed
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as f:
            f.write(code)
            f.flush()
            env_file = f.name

            if self.config.sandbox.enabled:
                env_file_arg = "/workspace/env.py"
                mounts = {Path(env_file): (Path("/workspace/env.py"), "ro")}
            else:
                env_file_arg = env_file
                mounts = {}

            result = run_sandboxed(
                script=self.config.smoke_test_script,
                args=["--env-file", env_file_arg, "--num-steps", str(self.config.smoke_test_steps)],
                config=self.config.sandbox,
                mounts=mounts,
                check=False,
                is_module=True,
                log_file=run.resolve_path(run.paths.smoke_test_log_dir, task.id) / f"attempt_{attempt + 1}.log",
            )
            return result.returncode == 0, result.stderr or ""
