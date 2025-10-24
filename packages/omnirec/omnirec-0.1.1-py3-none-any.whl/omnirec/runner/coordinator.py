import hashlib
import json
import subprocess
import sys
import tempfile
import traceback
from os import PathLike
from pathlib import Path
from threading import Event, Thread
from typing import IO, Any, Iterable, Optional, TypeVar

import omnirec_runner
import pandas as pd
import rpyc
from omnirec_runner.runner import RunnerInfo, RunnerService

from omnirec.data_variants import DataVariant, FoldedData, SplitData
from omnirec.recsys_data_set import RecSysDataSet
from omnirec.runner.envs import Env
from omnirec.runner.evaluation import Evaluator
from omnirec.runner.plan import ExperimentPlan
from omnirec.runner.progress import Phase, RunProgress
from omnirec.util import util
from omnirec.util.cert import Side, ensure_certs, get_cert_pth, get_key_pth

logger = util._root_logger.getChild("coordinator")
runner_logger = util._root_logger.getChild("runner")


_RUNNER_REGISTRY: dict[str, RunnerInfo] = {}


# TODO (Python 3.12+): Replace TypeVar with inline generic syntax `class Box[T](...)`
T = TypeVar("T", bound=DataVariant)


class Coordinator:
    def __init__(
        self,
        checkpoint_dir: PathLike | str = Path("./checkpoints"),
        tmp_dir: Optional[PathLike | str] = None,
    ) -> None:
        """Initialize the Coordinator for orchestrating recommendation algorithm experiments.
        The Coordinator manages the execution of experiments across multiple datasets, algorithms,
        and configurations. It handles environment isolation, checkpointing, progress tracking,
        and communication with framework-specific runners.

        Args:
            checkpoint_dir (PathLike | str, optional): Directory for storing persistent experiment data
                including model checkpoints, predictions, and progress files. Directory is created if it
                doesn't exist. Defaults to "./checkpoints".
            tmp_dir (Optional[PathLike | str], optional): Directory for temporary files such as intermediate
                CSV exports. If None, a temporary directory is created automatically and cleaned up on exit.
                Defaults to None.

        Note:
            - Automatically registers default runners (LensKit, RecBole, RecPack) on initialization
            - Generates SSL certificates for secure RPC communication with runner subprocesses
            - The checkpoint directory structure is: `checkpoint_dir/dataset-hash/config-hash/`
        """
        self._checkpoint_dir = Path(checkpoint_dir)
        if tmp_dir:
            self._tmp_dir = Path(tmp_dir)
        else:
            self._tmp_dir_obj: Optional[tempfile.TemporaryDirectory[str]] = (
                tempfile.TemporaryDirectory()
            )
            self._tmp_dir = Path(self._tmp_dir_obj.name)

        self._out_reader: Optional[OutputReader] = None
        self._err_reader: Optional[OutputReader] = None

        self._register_default_runners()
        ensure_certs()

    def __del__(self):
        if self._tmp_dir_obj:
            self._tmp_dir_obj.cleanup()

    def _register_default_runners(self):
        runner_dir = Path(omnirec_runner.__file__).parent.resolve()

        # TODO: Add other runner:
        # TODO: Maybe move this to a config file or smth and dont hard code
        self.register_runner(
            "LensKit",
            RunnerInfo(
                runner_dir / "lenskit_runner.py",
                [
                    "PopScorer",
                    "ItemKNNScorer",
                    "UserKNNScorer",
                    "ImplicitMFScorer",
                    "BiasedMFScorer",
                    "FunkSVDScorer",
                ],
                "3.11",
                ["lenskit==2025.2.0", "binpickle", "numba"],
            ),
        )

        self.register_runner(
            "RecBole",
            RunnerInfo(
                runner_dir / "recbole_runner.py",
                [
                    "Pop",
                    "ItemKNN",
                    "BPR",
                    "NeuMF",
                    "ConvNCF",
                    "DMF",
                    "FISM",
                    "NAIS",
                    "SpectralCF",
                    "GCMC",
                    "NGCF",
                    "LightGCN",
                    "DGCF",
                    "LINE",
                    "MultiVAE",
                    "MultiDAE",
                    "MacridVAE",
                    "CDAE",
                    "ENMF",
                    "NNCF",
                    "RecVAE",
                    "EASE",
                    "SLIMElastic",
                    "SGL",
                    "ADMMSLIM",
                    "NCEPLRec",
                    "SimpleX",
                    "NCL",
                    "Random",
                    "DiffRec",
                    "LDiffRec",
                ],
                "3.11",
                [
                    "recbole==1.2.1",
                    "numpy==1.26.4",
                    "torch==2.5.1",
                ],
            ),
        )

        self.register_runner(
            "RecPack",
            RunnerInfo(
                runner_dir / "recpack_runner.py",
                ["SVD", "NMF", "ItemKNN"],
                "3.12",
                ["recpack==0.3.6"],
            ),
        )
        self.register_runner(
            "Elliot",
            RunnerInfo(
                runner_dir / "elliot_runner.py",
                [
                    "ItemKNN",
                    "UserKNN",
                    "AMF",
                    "SlopeOne",
                    "MultiDAE",
                    "MultiVAE",
                    "LightGCN",
                    "NGCF",
                    "MostPop",
                    "BPRMF",
                    "BPRMF_batch",
                    "FM",
                    "FunkSVD",
                    "NonNegMF",
                    "PureSVD",
                    "SVDpp",
                    "WRMF",
                    "ConvMF",
                    "DeepFM",
                    "DMF",
                    "GMF",
                    "ItemAutoRec",
                    "NeuMF",
                    "UserAutoRec",
                ],
                "3.8",
                [
                    # patched elliot version
                    "git+https://github.com/moritz-baumgart/elliot.git",
                ],
            ),
        )

    def register_runner(self, name: str, info: RunnerInfo):
        if name in _RUNNER_REGISTRY:
            logger.critical(
                f"A runner with the name {name} is already registered. Choose a different one!"
            )
            sys.exit(1)

        _RUNNER_REGISTRY[name] = info
        logger.debug(f"Runner {name} registered")

    def run(
        self,
        datasets: RecSysDataSet[T] | Iterable[RecSysDataSet[T]],
        config: ExperimentPlan,
        evaluator: Evaluator,  # TODO: Make optional
    ) -> Evaluator:
        """Execute recommendation algorithm experiments across datasets and configurations.
        Orchestrates the complete experiment lifecycle: environment setup, model training,
        prediction generation, and evaluation. Supports automatic checkpointing and resuming
        of interrupted experiments.

        Args:
            datasets (RecSysDataSet[T] | Iterable[RecSysDataSet[T]]): Single dataset or list of datasets
                to run experiments on. Datasets must contain either SplitData (train/val/test) or
                FoldedData (cross-validation folds). Use preprocessing steps to create these splits.
            config (ExperimentPlan): Experiment configuration specifying algorithms and their hyperparameters.
                Each algorithm in the plan will be executed with all specified parameter combinations.
            evaluator (Evaluator): Evaluator instance containing metrics to compute on predictions.
                Results are accumulated across all experiments and accessible via `evaluator.get_tables()`.

        Returns:
            Evaluator: The same evaluator instance passed in, now containing results from all experiments.
                Use `evaluator.get_tables()` to retrieve formatted result tables.

        Raises:
            SystemExit: If the experiment plan is empty or if runner/algorithm validation fails.

        Note:
            - Each algorithm runs in an isolated Python environment with framework-specific dependencies
            - Progress is checkpointed after each phase (Fit, Predict, Eval) for fault tolerance
            - Identical dataset/config combinations are cached and skipped automatically
            - For cross-validation (FoldedData), experiments run sequentially across all folds
            - Runner subprocesses are automatically started and terminated for each algorithm
        """
        # TODO: Force fit, pred, eval parameters to overwrite status tracker
        # TODO: Dataset Normalization stuff etc. beforehand
        exception_occurred = False

        if not isinstance(datasets, Iterable):
            datasets = [datasets]

        algorithm_configs = config._get_configs()
        if len(algorithm_configs) == 0:
            logger.critical(
                "Empty configuration. You have to add at least one experiment!"
            )
            sys.exit(1)

        self._evaluator = evaluator
        self._results_path = self._checkpoint_dir / "results.json"
        if self._results_path.exists():
            self._evaluator.load_results(self._results_path)

        for current_algo, current_config_list in algorithm_configs:
            try:
                host, port = self.start_runner(current_algo)

                logger.info("Connecting to runner...")
                conn = rpyc.ssl_connect(
                    host,
                    port,
                    get_key_pth(Side.Client),
                    get_cert_pth(Side.Client),
                    config={"sync_request_timeout": 600},
                )
                root: RunnerService = conn.root

                for current_dataset in datasets:
                    for current_config in current_config_list:
                        dataset_namehash = f"{current_dataset._meta.name}-{self.dataset_hash(current_dataset)[:8]}"
                        config_namehash = f"{current_algo}-{self.config_hash(current_algo, current_config)[:8]}"
                        current_checkpoint_dir = (
                            self._checkpoint_dir / dataset_namehash / config_namehash
                        )
                        current_checkpoint_dir.mkdir(parents=True, exist_ok=True)
                        logger.debug(f"Using checkpoint dir: {current_checkpoint_dir}")

                        current_tmp_dir = (
                            self._tmp_dir / dataset_namehash / config_namehash
                        )

                        current_tmp_dir.mkdir(parents=True, exist_ok=True)
                        logger.debug(f"Using tmp dir: {current_tmp_dir}")

                        progress = RunProgress.load_or_create(
                            self._checkpoint_dir, (dataset_namehash, config_namehash)
                        )

                        if isinstance(current_dataset._data, FoldedData):

                            def get_next_fold():
                                return progress.get_next_fold_or_init(
                                    dataset_namehash, config_namehash
                                )

                            def reset_phase():
                                progress.reset_phase(dataset_namehash, config_namehash)

                            def advance_fold():
                                progress.advance_fold(dataset_namehash, config_namehash)

                            next_fold = get_next_fold()

                            for fold in range(
                                next_fold, len(current_dataset._data.folds)
                            ):
                                fold_data = current_dataset._data.folds[fold]

                                files = self.get_file_paths(
                                    current_checkpoint_dir, current_tmp_dir, fold
                                )
                                util.splits_to_csv(files[:3], fold_data)

                                self.run_split(
                                    root,
                                    progress,
                                    current_algo,
                                    current_config,
                                    current_dataset._meta.name,
                                    dataset_namehash,
                                    config_namehash,
                                    *files,
                                    fold,
                                )

                                advance_fold()
                                reset_phase()
                        elif isinstance(current_dataset._data, SplitData):
                            files = self.get_file_paths(
                                current_checkpoint_dir, current_tmp_dir
                            )
                            util.splits_to_csv(files[:3], current_dataset._data)

                            self.run_split(
                                root,
                                progress,
                                current_algo,
                                current_config,
                                current_dataset._meta.name,
                                dataset_namehash,
                                config_namehash,
                                *files,
                            )
                        else:
                            logger.critical(
                                "Invalid dataset variant. Dataset has to be either FoldedData or SplitData. Apply a datasplit beforehand"
                            )
                            sys.exit(1)

            except Exception:
                traceback.print_exc()
                exception_occurred = True
            finally:
                if exception_occurred:
                    self.stop()
                else:
                    self.stop(logger.info)
                # print(self._proc.returncode) # TODO: Handle bad return code?

        self._evaluator.save_results(self._results_path)
        return self._evaluator

    def start_runner(self, algorithm: str) -> tuple[str, str]:
        runner_name, algo_name = Coordinator.split_runner_algo(algorithm)
        runner_info = _RUNNER_REGISTRY.get(runner_name)
        if not runner_info:
            logger.critical(
                f'No runner found with name "{runner_name}! Did you register it first?"'
            )
            sys.exit(1)

        if not runner_info.runner_path.exists():
            logger.critical(f"Runner path {runner_info.runner_path} does not exist!")
            sys.exit(1)

        if algo_name not in runner_info.algorithms:
            logger.critical(
                f'Runner "{runner_name}" does not provide an algorithm named "{algo_name}"'
            )
            sys.exit(1)

        env = Env(
            f"{runner_name}_env", runner_info.python_version, *runner_info.packages
        )
        env.create()

        args = [
            env.py_path,
            "-u",
            runner_info.runner_path,
            get_key_pth(Side.Server),
            get_cert_pth(Side.Server),
        ]
        logger.info("Starting runner...")
        self._proc = subprocess.Popen(
            args,
            cwd=runner_info.runner_path.parent,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            if self._proc.stdout is None:
                raise ValueError("stdout attribute was None")

            host, port = self._proc.stdout.readline().rstrip("\n").split(" ")
        except Exception as e:
            logger.critical(f"Exception occurred while starting runner: {e}")
            self.log_output()
            self.stop()

            sys.exit(1)

        self._out_reader = OutputReader(runner_name, self._proc.stdout)
        self._err_reader = OutputReader(runner_name, self._proc.stderr, is_err=True)

        logger.info(f"Runner started with pid: {self._proc.pid}")

        return host, port

    def run_split(
        self,
        root: RunnerService,
        progress: "RunProgress",
        algorithm: str,
        algo_config: dict[str, Any],
        dataset_name: str,
        dataset_namehash: str,
        config_namehash: str,
        train_file: Path,
        val_file: Path,
        test_file: Path,
        predictions_file: Path,
        current_checkpoint_dir: Path,
        current_tmp_dir: Path,
        fold: Optional[int] = None,
    ):
        runner_name, algo_name = Coordinator.split_runner_algo(algorithm)
        logger.debug(
            f"Running split with parameters: {root=}, {progress=}, {algo_name=}, {algo_config=}, {train_file=}, {val_file=}, {test_file=}, {predictions_file=}, {current_checkpoint_dir=}, {current_tmp_dir=}"
        )

        root._config(
            algo_name,
            json.dumps(algo_config),
            dataset_name,
            str(train_file.resolve()),
            str(val_file.resolve()),
            str(test_file.resolve()),
            str(predictions_file.resolve()),
            str(current_checkpoint_dir.resolve()),
            str(current_tmp_dir.resolve()),
        )

        def get_phase() -> Phase:
            return progress.get_next_phase(dataset_namehash, config_namehash)

        def advance_phase():
            progress.advance_phase(dataset_namehash, config_namehash)

        did_progress = False

        # TODO: Info log in else case
        if get_phase() <= Phase.Fit:
            did_progress = True
            self.log_phase_info(dataset_name, algo_name, "'Fit'")
            root._fit()

            advance_phase()

        if get_phase() <= Phase.Predict:
            did_progress = True
            self.log_phase_info(dataset_name, algo_name, "'Predict'")
            root._predict()

            advance_phase()

        if get_phase() <= Phase.Eval:
            did_progress = True
            # TODO: Load predictions.json and do unified evaluation
            self.log_phase_info(dataset_name, algo_name, "'Evaluate'")
            # TODO: Save and load evaluations for checkpointing
            predictions = pd.DataFrame(json.loads(predictions_file.read_text()))
            test = pd.read_csv(test_file)
            self._evaluator.run_evaluation(
                dataset_namehash, config_namehash, predictions, test, fold
            )

            advance_phase()

        if get_phase() <= Phase.Done:
            if did_progress:
                logger.info(f"{dataset_name}/{algo_name} done!")
            else:
                logger.info(
                    f"All phases for {dataset_name}/{algo_name} already complete, skipping..."
                )

    def log_phase_info(self, dataset_name: str, algo_name: str, phase: str):
        logger.info(f"Running phase {phase} for {dataset_name}/{algo_name}")

    @staticmethod
    def dataset_hash(dataset: RecSysDataSet[T]) -> str:
        json_str = json.dumps(dataset.num_interactions())
        return hashlib.sha256(json_str.encode()).hexdigest()

    @staticmethod
    def config_hash(algo_name: str, config: dict[str, Any]) -> str:
        json_str = json.dumps((algo_name, config))
        return hashlib.sha256(json_str.encode()).hexdigest()

    @staticmethod
    def split_runner_algo(runner_algo: str):
        try:
            runner_name, algo_name = runner_algo.split(".")
            return runner_name, algo_name
        except Exception:
            logger.critical(
                'Error while parsing algorithm name. Specify algorithm parameter as "<runnerName>.<algorithmName>"'
            )
            sys.exit(1)

    @staticmethod
    def get_file_paths(
        checkpoint_dir: Path, tmp_dir: Path, fold: Optional[int] = None
    ) -> tuple[Path, Path, Path, Path, Path, Path]:
        if fold is not None:
            checkpoint_dir /= f"fold_{fold}"
            checkpoint_dir.mkdir(parents=True, exist_ok=True)

            tmp_dir /= f"fold_{fold}"
            tmp_dir.mkdir(parents=True, exist_ok=True)
        return (
            tmp_dir / "train.csv",
            tmp_dir / "val.csv",
            tmp_dir / "test.csv",
            checkpoint_dir / "predictions.json",
            checkpoint_dir,
            tmp_dir,
        )

    def stop(self, logger_fn=logger.critical):
        logger_fn("Stopping runner...")
        # FIXME: self._proc might be None here
        self._proc.terminate()
        try:
            self._proc.wait(5)
        except subprocess.TimeoutExpired:
            logger_fn("Runner did not respond, killing...")
            self._proc.kill()
            self._proc.wait()

        for reader in (self._out_reader, self._err_reader):
            if reader is not None:
                reader.stop(self._checkpoint_dir)

    def log_output(self):
        for name, io in (("stdout", self._proc.stdout), ("stderr", self._proc.stderr)):
            if io is not None:
                logger.debug(f"Runner {name}:")
                for line in io.readlines():
                    line = line.rstrip("\n")
                    logger.debug(f"> {line}")


class OutputReader:
    def __init__(self, runner_name: str, pipe: Optional[IO[str]], is_err=False) -> None:
        self._runner_name = runner_name
        self._is_err = is_err
        self._done_event = Event()
        self._output: list[str] = []

        self._start(pipe)

    def _start(self, pipe: Optional[IO[str]]):
        if pipe is None:
            return

        Thread(target=self._read, args=(pipe,), daemon=True).start()

    def _read(self, pipe: IO[str]):
        for line in pipe:
            # TODO: Check if we have \n at the of line and strip/log without line break. Also see below when writing to file
            self._output.append(line)
            if self._is_err:
                runner_logger.debug(f"Runner sterr: {line.rstrip('\n')}")
            else:
                runner_logger.debug(f"Runner stdout: {line.rstrip('\n')}")
        self._done_event.set()

    def stop(self, out_dir: Path):
        self._done_event.wait()

        if self._is_err:
            out_file = out_dir / "err.log"
        else:
            out_file = out_dir / "out.log"

        with open(out_file, "a") as out_file_h:
            out_file_h.writelines(self._output)
