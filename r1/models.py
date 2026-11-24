"""The ResNet-18 ensemble and its dihedral test-time views.

Semantics are ported from ``main.ipynb`` cell 24 so that the stored checkpoints reproduce
the published predictions. Inference runs on CPU unless a GPU is available.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models

from . import config


def device() -> torch.device:
    return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def build_model() -> nn.Module:
    """ResNet-18 adapted to 1 input channel and 2 classes, as trained."""
    m = models.resnet18(weights=None)
    m.conv1 = nn.Conv2d(1, 64, kernel_size=(7, 7), stride=(2, 2), padding=(3, 3), bias=False)
    m.fc = nn.Linear(m.fc.in_features, 2)
    return m


def load_ensemble(paths: list[Path] | None = None) -> list[nn.Module]:
    """Load the 5 final-epoch checkpoints and set them to eval mode."""
    torch.set_num_threads(config.torch_threads())
    paths = paths or config.ENSEMBLE_CHECKPOINTS
    dev = device()
    out = []
    for p in paths:
        m = build_model()
        missing = m.load_state_dict(torch.load(p, map_location="cpu"))
        if getattr(missing, "missing_keys", None) or getattr(missing, "unexpected_keys", None):
            raise RuntimeError(f"checkpoint {p} does not match the architecture: {missing}")
        out.append(m.to(dev).eval())
    return out


def dihedral_views(A: np.ndarray) -> list[np.ndarray]:
    """The 8 symmetries of the square: 4 rotations x optional mirror.

    A radio galaxy image has no preferred orientation, so a classifier that respects the
    physics must give the same label for all 8. Order matches the notebook, with view 0
    the identity.
    """
    views = []
    for flip in (False, True):
        B = A[:, :, ::-1] if flip else A
        for k in range(4):
            views.append(np.ascontiguousarray(np.rot90(B, k, axes=(1, 2))))
    return views


@torch.no_grad()
def predict_views(
    A: np.ndarray, models_list: list[nn.Module], batch_size: int = 128
) -> np.ndarray:
    """P(FR-II) for every (view, model) pair.

    Returns an array of shape (8, n_models, len(A)). Every downstream diagnostic -
    the TTA mean, the per-seed identity predictions, and the dihedral flip rate - is a
    reduction of this one tensor, so they cannot drift apart.
    """
    dev = device()
    views = dihedral_views(A)
    out = np.zeros((len(views), len(models_list), len(A)), dtype=np.float64)
    for vi, V in enumerate(views):
        for si, m in enumerate(models_list):
            probs = []
            for i in range(0, len(V), batch_size):
                x = torch.tensor(V[i : i + batch_size], dtype=torch.float32, device=dev).unsqueeze(1)
                probs.append(F.softmax(m(x), dim=1)[:, 1].cpu().numpy())
            out[vi, si] = np.concatenate(probs)
    return out


def tta_mean(view_probs: np.ndarray) -> np.ndarray:
    """Mean P(FR-II) over all views and models - the published candidate score."""
    return view_probs.mean(axis=(0, 1))


def identity_per_seed(view_probs: np.ndarray) -> np.ndarray:
    """P(FR-II) per model on the unrotated image, shape (n_models, n)."""
    return view_probs[0]


def ensemble_mean_per_view(view_probs: np.ndarray) -> np.ndarray:
    """Ensemble-mean P(FR-II) for each view separately, shape (8, n)."""
    return view_probs.mean(axis=1)
