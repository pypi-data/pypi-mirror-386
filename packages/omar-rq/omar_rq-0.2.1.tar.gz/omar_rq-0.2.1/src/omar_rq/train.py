from argparse import ArgumentParser
from pathlib import Path
import traceback

import gin.torch
import pytorch_lightning as L
from pytorch_lightning import Trainer
from pytorch_lightning.loggers import WandbLogger

from .cosineannealingscheduler import CosineAnnealingCallback
from .data import DATASETS
from .modules import MODULES
from .nets import NETS
from .utils import gin_config_to_readable_dictionary, build_module, build_dev_datamodule
from .callbacks import GinConfigSaverCallback


# Register all modules, datasets and networs with gin
for net_name, net in NETS.items():
    gin.external_configurable(net, net_name)

for module_name, module in MODULES.items():
    gin.external_configurable(module, module_name)

for data_name, data in DATASETS.items():
    gin.external_configurable(data, data_name)


@gin.configurable
def train(
    module: L.LightningModule,
    datamodule: L.LightningDataModule,
    params: dict,
    wandb_params: dict,
    config_path: Path,
    ckpt_path: Path = None,
) -> None:
    """Train a model using the given module, datamodule and netitecture"""

    # get the lightning wandb logger wrapper and log the config
    gin_config_dict = gin_config_to_readable_dictionary(gin.config._OPERATIVE_CONFIG)
    wandb_logger = WandbLogger(**wandb_params)
    wandb_logger.log_hyperparams(gin_config_dict)

    # log the number of parameters in the network (required to compute scaling laws)
    # tb_logger.experiment.config["param_count"] = net.get_parameter_count()

    # create callbacks
    cosine_annealing_callback = CosineAnnealingCallback(total_steps=params["max_steps"])
    config_save_callback = GinConfigSaverCallback(config_path)
    callbacks = [cosine_annealing_callback, config_save_callback]

    # create the trainer and fit the model
    trainer = Trainer(logger=wandb_logger, callbacks=callbacks, **params)
    # If a checkpoint is provided, load it and continue training
    trainer.fit(model=module, datamodule=datamodule, ckpt_path=ckpt_path)


if __name__ == "__main__":
    parser = ArgumentParser("Train SSL models using gin config")
    parser.add_argument(
        "train_config",
        type=Path,
        help="Path to the gin config file for training.",
    )

    args = parser.parse_args()

    try:
        gin.parse_config_file(args.train_config, skip_unknown=True)

        module, ckpt_path = build_module()
        datamodule = build_dev_datamodule()

        gin.finalize()

        train(module, datamodule, config_path=args.train_config, ckpt_path=ckpt_path)
    except Exception:
        traceback.print_exc()
