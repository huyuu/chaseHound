import time
from pathlib import Path
from threading import Thread

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src_python.ChaseHoundMain import ChaseHoundMain
from src_python.config_loader import RunConfig


class _ChaseRunner(Thread):
    """Background thread responsible for executing a ChaseHound run.

    We run the heavy *ChaseHoundMain.run* loop in a separate thread so that the
    file-watcher can continue responding to new configuration files while a run
    is ongoing.  If multiple YAML files are dropped into the *configs/* folder
    we queue them sequentially (one thread at a time) – adjust to your needs.
    """

    def __init__(self, config_path: Path, results_dir: Path):
        super().__init__(daemon=True)
        self.config_path = config_path
        self.results_dir = results_dir

    def run(self):
        # Load configuration – not yet used by *ChaseHoundMain* but parsed for
        # future extension.
        run_cfg = RunConfig.from_yaml(self.config_path)

        # Instantiate your main engine.
        engine = ChaseHoundMain()

        # TODO: Pass *run_cfg* to *engine* once its API supports it.
        print(f"[Watcher] Starting ChaseHound run for config '{self.config_path.name}' …")
        try:
            engine.run()
        except Exception as exc:  # noqa: BLE001
            print(f"[Watcher] Run for '{self.config_path.name}' failed: {exc}")
            raise
        finally:
            # Persist a simple marker so that Streamlit (or any other consumer)
            # knows the job has finished. Replace with richer output as needed.
            self.results_dir.mkdir(exist_ok=True)
            result_file = self.results_dir / f"{self.config_path.stem}_finished.flag"
            result_file.write_text("completed")
            print(f"[Watcher] Run for '{self.config_path.name}' completed. Results flag written to '{result_file}'.")


class ConfigEventHandler(FileSystemEventHandler):
    """React to new YAML files appearing in the configs directory."""

    def __init__(self, results_dir: Path):
        super().__init__()
        self.results_dir = results_dir

    def on_created(self, event):  # noqa: D401
        """Handle new file creation events."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix.lower() not in {".yml", ".yaml"}:
            return

        # Kick off a background thread to handle the run.
        _ChaseRunner(config_path=path, results_dir=self.results_dir).start()


def main():  # noqa: D401
    """Entry-point that starts watching the *configs/* folder."""
    config_dir = Path("configs")
    results_dir = Path("results")

    config_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    event_handler = ConfigEventHandler(results_dir=results_dir)

    observer = Observer()
    observer.schedule(event_handler, str(config_dir), recursive=False)
    observer.start()

    print(f"[Watcher] Monitoring '{config_dir.resolve()}' for new configuration files … Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Watcher] Stopping observer …")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main() 