"""Optional PyTorch LSTM baseline for chronological sequence classification."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class LSTMConfig:
    sequence_length: int = 32
    hidden_size: int = 16
    epochs: int = 20
    learning_rate: float = 1e-3
    seed: int = 42


def fit_lstm_classifier(
    features: pd.DataFrame,
    target: pd.Series,
    train_size: int,
    config: LSTMConfig = LSTMConfig(),
) -> pd.Series:
    """Fit on the chronological prefix and return out-of-sample probabilities.

    PyTorch is intentionally optional. Install the ``ml`` project extra before
    calling this function. Scaling statistics are learned from the train set only.
    """
    try:
        import torch
        from torch import nn
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("LSTM support requires: pip install -e '.[ml]'") from exc

    if not config.sequence_length < train_size < len(features):
        raise ValueError("train_size must leave sequences in both train and test sets")
    clean = features.astype(float).replace([np.inf, -np.inf], np.nan)
    if clean.isna().any().any() or target.isna().any():
        raise ValueError("features and target must not contain NaN or infinity")
    mean, std = clean.iloc[:train_size].mean(), clean.iloc[:train_size].std().replace(0, 1)
    scaled = ((clean - mean) / std).to_numpy(dtype=np.float32)
    labels = target.astype(np.float32).to_numpy()

    def sequences(start: int, stop: int):
        indexes = range(max(start, config.sequence_length), stop)
        xs = np.stack([scaled[i - config.sequence_length : i] for i in indexes])
        ys = np.asarray([labels[i] for i in indexes], dtype=np.float32)
        return torch.from_numpy(xs), torch.from_numpy(ys), list(indexes)

    train_x, train_y, _ = sequences(0, train_size)
    test_x, _, test_indexes = sequences(train_size, len(clean))
    torch.manual_seed(config.seed)

    class Model(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(clean.shape[1], config.hidden_size, batch_first=True)
            self.output = nn.Linear(config.hidden_size, 1)

        def forward(self, values):
            encoded, _ = self.lstm(values)
            return self.output(encoded[:, -1]).squeeze(-1)

    model = Model()
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    loss_function = nn.BCEWithLogitsLoss()
    model.train()
    for _ in range(config.epochs):
        optimizer.zero_grad()
        loss = loss_function(model(train_x), train_y)
        loss.backward()
        optimizer.step()
    model.eval()
    with torch.no_grad():
        probability = torch.sigmoid(model(test_x)).numpy()
    return pd.Series(probability, index=features.index[test_indexes], name="probability")
