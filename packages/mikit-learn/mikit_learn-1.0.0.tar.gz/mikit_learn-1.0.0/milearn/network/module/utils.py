import logging

import pytorch_lightning as pl
from lightning.pytorch.utilities import rank_zero
from pytorch_lightning import seed_everything


def silence_and_seed_lightning(seed: int = 42, level: int = logging.ERROR) -> None:
    """Silence PyTorch Lightning logs and set random seeds for reproducibility.

    This function:
      1. Reduces verbosity of Lightning loggers.
      2. Silences `rank_zero` logging helpers to avoid clutter in distributed training.
      3. Seeds all relevant random number generators including worker threads.

    Args:
        seed (int): Random seed to set for reproducibility.
        level (int): Logging level for silenced loggers (default: logging.ERROR).
    """
    # 1. Silence standard loggers
    modules = [
        "lightning.pytorch",  # global lightning logs
        "lightning.pytorch.accelerators.cuda",  # GPU availability
        "lightning.pytorch.accelerators.tpu",  # TPU availability
        "lightning.pytorch.accelerators.hpu",  # HPU availability
        "lightning.pytorch.utilities.seed",  # <- the seed message
    ]
    for m in modules:
        logging.getLogger(m).setLevel(level)

    # 2. Silence rank_zero log helpers
    rank_zero.rank_zero_info = lambda *a, **k: None
    rank_zero.rank_zero_warn = lambda *a, **k: None
    rank_zero.rank_zero_debug = lambda *a, **k: None
    rank_zero.rank_zero_only = lambda f, *a, **k: None

    # 3. Seed everything
    seed_everything(seed, workers=True, verbose=False)


class TrainLogging(pl.Callback):
    """PyTorch Lightning callback to log training and validation loss per
    epoch.

    Prints a formatted message at the end of each training epoch:
        Epoch <current>/<max> | train_loss=<value> | val_loss=<value>
    """

    def on_train_epoch_end(self, trainer, pl_module):
        """Called at the end of each training epoch to log losses.

        Args:
            trainer (pl.Trainer): the current PyTorch Lightning trainer.
            pl_module (pl.LightningModule): the model being trained.
        """
        metrics = trainer.callback_metrics
        train_loss = metrics.get("train_loss", 0.0)
        val_loss = metrics.get("val_loss", 0.0)

        # Align epoch numbers and losses
        print(
            f"Epoch {trainer.current_epoch+1:3d}/{trainer.max_epochs:<3d} | "
            f"train_loss={train_loss:5.3f} | "
            f"val_loss={val_loss:5.3f}"
        )
