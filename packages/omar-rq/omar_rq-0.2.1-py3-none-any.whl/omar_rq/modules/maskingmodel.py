import math
import os
import random
from collections import defaultdict
from typing import Set

import gin
import torch
from torch import nn
import pytorch_lightning as L

from .codebooks import RandomProjectionQuantizer
from .finite_scalar_quantizer import FiniteScalarQuantizer


@gin.configurable
class MaskingModel(L.LightningModule):
    """
    MaskingModel
    inspired https://github.com/minzwon/musicfm/blob/b83ebedb401bcef639b26b05c0c8bee1dc2dfe71/model/musicfm_25hz.py#L125

    This model is used to train a model with a masking laguage modelling mechanism.
    net is the model that will be trained
    representation is the module that will be used to extract the features
    patch_frames is the number of frames that will be used to create a patch (default 16 x 16)
    num_codebooks is the number of codebooks that will be used (default 1)
    codebook_size is the size of the codebook (default 4096)
    mask_seconds is the number of seconds that will be masked (default 0.4)
    mask_prob is the probability that a mask will be applied (default 0.6)
    """

    def __init__(
        self,
        net: nn.Module,
        lr: float,
        weight_decay: float,
        representation: nn.Module | None,
        num_codebooks: int,
        codebook_size: int,
        codebook_dim: int,
        mask_seconds: float,
        mask_prob: float,
        seed: int,
        diff_input: bool,
        plot_tokens: bool = False,
        input_representation: nn.Module | None = None,
        masking_noise_type: str = "random_normal",
        quantizer_type: str = "random_codebook",
        quantization_targets: bool = False,
    ):
        super(MaskingModel, self).__init__()

        # global variables
        self.mask_seconds = mask_seconds
        self.mask_prob = mask_prob
        self.num_codebooks = num_codebooks
        self.codebook_dim = codebook_dim
        self.codebook_size = codebook_size
        self.net = net
        self.representation = representation
        self.lr = lr
        self.seed = seed
        self.plot_tokens = plot_tokens
        self.weight_decay = weight_decay
        self.tokens_coverage = []
        self.first_coverage = True
        self.diff_input = diff_input
        self.input_rep = input_representation
        self.masking_noise_type = masking_noise_type
        self.quantizer_type = quantizer_type
        self.quantization_targets = quantization_targets

        # downstream evaluation params
        self.downstream_embedding_layer = set([-1])

        self.predict_data = defaultdict(list)

        n_reps = 1
        if isinstance(representation, nn.ModuleList):
            n_reps = len(representation)
        self.n_reps = n_reps

        self.linear = nn.Linear(
            self.net.embed_dim, codebook_size * num_codebooks * n_reps
        )

        # debugging variables
        self.tokens_accumulator = defaultdict(list)

        # Multifeature
        if isinstance(self.representation, nn.ModuleList):
            target_reps = self.representation

            # if input_representation is provided, use it
            for rep in target_reps:
                if isinstance(rep, self.input_rep):
                    self.input_rep = rep
                    break

            # if input_representation is not among the target reps, instantiate it
            if isinstance(self.input_rep, type):
                self.input_rep = self.input_rep()

        elif self.representation is None:
            assert self.input_rep is not None, (
                "Representation is None, but input_rep is also None. This should not happen."
            )
            self.input_rep = self.input_rep()

        # Single feature
        else:
            target_reps = [self.representation]
            self.input_rep = self.representation

        self.sr = self.input_rep.sr
        self.hop_length = self.input_rep.hop_len
        self.rep_dims = self.input_rep.rep_dims
        self.patch_size = self.input_rep.patch_size

        # aux nets
        self.embedding_layer = nn.Linear(
            self.patch_size[0] * self.patch_size[1], self.net.embed_dim
        )

        # We don't need to create quantizers in inference mode
        if not self.quantization_targets:
            return

        # Create a ModuleList holding the quantizers
        self.quantizers = nn.ModuleList()
        for rep in target_reps:
            assert (
                hasattr(rep, "sr")
                and hasattr(rep, "patch_size")
                and hasattr(rep, "hop_len")
                and hasattr(rep, "rep_dims")
            ), (
                f"Representation {type(rep)} shuold have sr, patch_size, hop_len and rep_dims attributes."
            )

            input_dim = rep.patch_size[0] * rep.patch_size[1]
            self.quantizers.append(self.create_quantizers(input_dim, seed=seed))

        # loss function
        self.loss = nn.CrossEntropyLoss()

    def create_quantizers(self, input_dim: int, seed: int) -> nn.ModuleList:
        """Create quantizers based on the specified type."""
        if self.quantizer_type == "random_codebook":
            quantizers = nn.ModuleList(
                [
                    RandomProjectionQuantizer(
                        input_dim,
                        self.codebook_dim,
                        self.codebook_size,
                        seed=seed + i,
                        diff_input=self.diff_input,
                    )
                    for i in range(self.num_codebooks)
                ]
            )
        elif self.quantizer_type == "finite_scalar_quantizer":
            quantizers = nn.ModuleList(
                [
                    FiniteScalarQuantizer(dim=input_dim, seed=seed + i)
                    for i in range(self.num_codebooks)
                ]
            )
        else:
            raise NotImplementedError(
                f"Quantizer type {self.quantizer_type} not implemented."
            )
        return quantizers

    def pad_spectrogram(self, spectrogram, patch_size=16):
        B, F, T = spectrogram.shape

        # Calculate padding sizes
        pad_f = (patch_size - F % patch_size) % patch_size
        pad_t = (patch_size - T % patch_size) % patch_size

        # Apply padding (only on F and T dimensions)
        padded_spectrogram = torch.nn.functional.pad(
            spectrogram, (0, pad_t, 0, pad_f), mode="constant", value=0
        )
        return padded_spectrogram

    def plot_spectrogram_with_tokens(
        self, spectrogram, num_patches_f, num_patches_t, tokens
    ):
        from matplotlib import pyplot as plt

        plt.figure(figsize=(36, 8), dpi=300)

        plt.imshow(spectrogram, aspect="auto", cmap="viridis", origin="lower")
        plt.colorbar(label="Magnitude")
        plt.title("Spectrogram with Token Numbers")
        plt.xlabel("Time")
        plt.ylabel("Frequency")

        token_index = 0
        for i in range(num_patches_f):
            for j in range(num_patches_t):
                # Calculate the patch boundaries
                start_f = i * self.patch_size[0]
                end_f = start_f + self.patch_size[0]
                start_t = j * self.patch_size[1]
                end_t = start_t + self.patch_size[1]

                # Draw the patch boundary
                plt.plot(
                    [start_t, start_t], [start_f, end_f], color="white", linewidth=1
                )
                plt.plot([end_t, end_t], [start_f, end_f], color="white", linewidth=1)
                plt.plot(
                    [start_t, end_t], [start_f, start_f], color="white", linewidth=1
                )
                plt.plot([start_t, end_t], [end_f, end_f], color="white", linewidth=1)

                # Place the token number in the center of each patch
                center_t = (start_t + end_t) / 2
                center_f = (start_f + end_f) / 2
                plt.text(
                    center_t,
                    center_f,
                    str(tokens[token_index].item()),
                    color="red",
                    fontsize=8,
                    ha="center",
                    va="center",
                    rotation=90,
                )
                token_index += 1
        # save the plot in ../figs as pdf
        randint = random.randint(0, 100000)
        if not os.path.exists("../figs"):
            os.makedirs("figs")
        # save pdf
        plt.savefig(f"figs/spectrogram_with_tokens_{randint}.pdf")
        plt.close()

    def vit_tokenization(self, x, rep, quantizers=None):
        B, F, T = x.shape
        num_patches_f = F // rep.patch_size[0]
        num_patches_t = T // rep.patch_size[1]
        # Reshape spectrogram into patches
        patches = x.unfold(1, rep.patch_size[0], rep.patch_size[0])
        patches = patches.unfold(2, rep.patch_size[1], rep.patch_size[1])
        # Reshape to (B, num_patches_f * num_patches_t, patch_frames_f, patch_frames_t)
        patches = patches.contiguous().view(
            B, num_patches_f * num_patches_t, rep.patch_size[0], rep.patch_size[1]
        )
        # Flatten patches to tokens
        patches = patches.view(B, num_patches_f * num_patches_t, -1)

        # Apply quantization
        if quantizers:
            tokens = torch.stack(
                [quantizer(patches) for quantizer in quantizers], dim=-1
            )
            if self.plot_tokens:
                self.plot_spectrogram_with_tokens(
                    x[0].detach().cpu(),
                    num_patches_f,
                    num_patches_t,
                    tokens[0, :, 0].detach().cpu(),
                )
        else:
            tokens = None

        return patches, tokens

    def random_masking_simple(self, patches):
        B, num_patches, patch_size = patches.shape
        num_masked = int(self.mask_prob * num_patches)
        # we have a windows_random
        # Generate random mask indices
        mask_indices = torch.rand(B, num_patches).argsort(dim=1)[:, :num_masked]
        # Create a mask array with the same shape as tokens, initialized to False
        mask = torch.zeros(B, num_patches, dtype=torch.bool)
        mask[torch.arange(B).unsqueeze(1), mask_indices] = True
        masked_spec = patches.clone()
        masking_noise = torch.randn_like(masked_spec) * 0.1
        masked_spec[mask] = masking_noise[mask]
        return masked_spec, mask.to(patches.device)

    def random_masking(self, patches):
        B, num_patches, _ = patches.shape
        mx = patches.clone()

        len_masking_spec_frames = math.ceil(
            self.mask_seconds * self.sr / self.hop_length
        )
        windows_tokens = (
            len_masking_spec_frames
            // self.patch_size[1]
            * (self.rep_dims // self.patch_size[0])
        )

        # Generate random mask indices
        start_indices = (
            torch.rand(B, math.ceil(num_patches / windows_tokens)) < self.mask_prob
        )
        mask = start_indices.repeat_interleave(windows_tokens, dim=1)

        # Trim mask to fit the number of patches
        if mask.size(1) > num_patches:
            mask = mask[:, :num_patches]

        if self.masking_noise_type == "random_normal":
            # Mask with random values
            masking_noise = (torch.randn(mx.shape, dtype=patches.dtype) * 0.1).to(
                patches.device
            )  # 0 mean 0.1 std
        elif self.masking_noise_type == "shuffled_input":
            # make a copy of patches shuffled on the time axis
            masking_noise = patches[:, torch.randperm(num_patches), :]
        else:
            raise NotImplementedError(
                f"Masking noise type {self.masking_noise_type} not implemented."
            )

        # Apply masking in parallel
        mx[mask] = masking_noise[mask]
        # tensor 1 x N repeat to 16 x N
        return mx, mask.to(patches.device)

    def get_loss(self, logits, target_tokens, mask):
        # zeros boolean with the shape of logit_out
        masked_logits = logits[mask]
        masked_tokens = target_tokens[mask]
        # The loss is calculated only for the masked tokens
        losses = self.loss(masked_logits, masked_tokens)
        accuracies = (
            torch.sum(masked_logits.argmax(1) == masked_tokens) / masked_tokens.numel()
        )
        return losses, accuracies

    def forward(self, x):
        x = x[0]
        B = x.shape[0]

        if isinstance(self.representation, nn.ModuleList):
            target_tokens_l = []
            x_input = None
            for i, rep in enumerate(self.representation):
                x_rep = rep(x)
                x_rep, target_tokens = self.vit_tokenization(
                    x_rep, rep, self.quantizers[i]
                )
                target_tokens_l.append(target_tokens)

                if isinstance(rep, type(self.input_rep)):
                    x_input = x_rep

            if not x_input:
                x_rep = self.input_rep(x)
                x_input, _ = self.vit_tokenization(x_rep, self.input_rep)

            # trim to the shortest
            min_len = min([t.shape[1] for t in target_tokens_l])
            max_len = max([t.shape[1] for t in target_tokens_l])
            diff = max_len - min_len
            assert diff < 3, f"diff {diff} is too big"

            target_tokens_l = [t[:, :min_len] for t in target_tokens_l]
            target_tokens = torch.cat(target_tokens_l, dim=-1)
            x_input = x_input[:, :min_len]

            x = x_input

        else:
            x = self.representation(x)
            # get target feature tokens
            x, target_tokens = self.vit_tokenization(
                x, self.input_rep, self.quantizers[0]
            )  # B x t x (16 x 4)

        # masking
        x, mask = self.random_masking(x)

        x = self.embedding_layer(x)
        x = self.net(x)
        logits = self.linear(x)
        logits = logits.view(
            B, -1, self.codebook_size, self.num_codebooks * self.n_reps
        )
        # get loss
        losses, accuracies = self.get_loss(logits, target_tokens, mask)
        return logits, losses, accuracies, target_tokens

    def training_step(self, batch, batch_idx):
        x = batch
        logits, loss, accuracies, target_tokens = self.forward(x)
        # log tokens coverage
        first_coverage_steps = 100

        if self.first_coverage and batch_idx < first_coverage_steps:
            # collapse batch and time axes
            tokens_c = target_tokens.view(-1, self.num_codebooks)

            # log tokens
            for i in range(self.num_codebooks):
                self.tokens_accumulator[f"codebook_{i}"].extend(
                    tokens_c[:, i].cpu().tolist()
                )

        elif self.first_coverage and batch_idx == first_coverage_steps:
            import wandb

            # Print the histogram you can check it in the wandb dashboard (log section)
            for key, value in self.tokens_accumulator.items():
                self.logger.experiment.log({f"{key}_histogram": wandb.Histogram(value)})
            print(
                f"Logged histograms of token counts for the first {first_coverage_steps} steps."
            )
            self.first_coverage = False
            del self.tokens_accumulator

        self.log("train_loss", loss, prog_bar=True)
        self.log("train_acc", accuracies)
        return loss

    def validation_step(self, batch, batch_idx):
        x = batch
        logits, loss, accuracies, target_tokens = self.forward(x)
        self.log("val_loss", loss, prog_bar=True)
        self.log("val_acc", accuracies)
        return loss

    def predict_step(self, batch, batch_idx, dataloader_idx=None):
        x, filenames = batch

        embeddings = self.extract_embeddings(x).cpu()

        for i in range(len(filenames)):
            self.predict_data[filenames[i]].append(embeddings[:, i, :, :])

    def extract_embeddings(
        self,
        audio: torch.Tensor,
        layers: Set[int] | None = None,
    ):
        """Extract audio embeddings using the model.

        Parameters:
            audio (torch.Tensor): 1D audio tensor.
            layers (set): List of layer indices to extract embeddings from.
            By default, it extracts embeddings from the last layer.

        Output:
            torch.Tensor: Extracted embeddings.
                Even in the case of aggregation or single layer embeddings,
                the output tensor will have the same shape (L, B, T, C,)
                where L = len(layer), B is the number of chunks
                T is the number of melspec frames the model can accomodate
                C = model output dimension. No aggregation is applied.

        """

        # If a layer is not provided, use the layer specified at initialization
        if layers is None:
            layers = self.downstream_embedding_layer

        layers = set(layers)
        assert isinstance(layers, set), "Layer must be a set."

        # assert no nan values in audio
        assert not torch.isnan(audio).any(), "Input audio contains NaN values."

        # Compute the representation
        x = self.input_rep(audio)  # (F, Tm)

        # TODO: what if in Frequency axis we need to aggregate?

        assert x.shape[1] == self.patch_size[0], (
            f"Frequency patching is not implemented yet!"
            f"Expected {self.patch_size[1]} but got {x.shape[0]}"
        )

        assert x is not None, "Representation not found."

        # Embed the representation
        x, _ = self.vit_tokenization(x, self.input_rep)  # (B, N, P1*P2)
        x = self.embedding_layer(x)  # (B, N, Cin)

        # TODO: support multiple layers
        x = self.net(x, layers=layers)  # (B, N, Cout)

        if len(layers) == 1:
            x = x.unsqueeze(0)  # (L, B, N, Cout)

        return x

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(
            self.parameters(), lr=self.lr, weight_decay=self.weight_decay
        )
        return optimizer
