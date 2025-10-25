__all__ = ["StyleEncoder", "DurationPredictor", "TextEncoder"]

from lt_utils.common import *
from lt_tensor.common import *
import torch.nn.functional as F
from lt_tensor.model_zoo.convs import ConvBase, is_conv


class Conv1dNorm(ConvBase):
    def __init__(
        self,
        channels: int,
        kernel_size: int = 1,
        dilation: int = 1,
        eps: float = 1e-5,
        dropout: float = 0.05,
        stride: int = 1,
        activation=nn.LeakyReLU(0.1),
        groups: int = 1,
        mask_value: float = 0.0,
        bias: bool = True,
        norm: Optional[Literal["weight_norm", "spectral_norm"]] = "weight_norm",
    ):
        super().__init__()
        self.channels = channels
        self.mask_value = mask_value
        self.activation = activation
        self.eps = eps

        self.cnn = self.get_1d_conv(
            channels,
            kernel_size=kernel_size,
            dilation=dilation,
            groups=groups,
            stride=stride,
            padding=(kernel_size - dilation) // 2,
            bias=bias,
            norm=norm,
        )
        self.norm = nn.LayerNorm(channels, eps, elementwise_affine=True, bias=True)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: Tensor, mask: Optional[Tensor] = None):
        if mask is not None:
            x.masked_fill_(mask, self.mask_value)
        x = self.cnn(x).transpose(-2, -1)
        x = self.norm(x).transpose(-2, -1)
        x = self.activation(x)
        x = self.dropout(x)
        return x


class DurationPredictor(ConvBase):
    def __init__(
        self,
        dim: int,
        hidden: int = 128,
        norm: Optional[Literal["weight_norm", "spectral_norm"]] = "weight_norm",
    ):
        super().__init__()
        self.net = nn.Sequential(
            self.get_1d_conv(dim, hidden, 3, padding=1, norm=norm),
            nn.LeakyReLU(0.1),
            nn.BatchNorm1d(hidden),
            self.get_1d_conv(hidden, hidden, 3, padding=1, norm=norm),
            nn.LeakyReLU(0.1),
            self.get_1d_conv(hidden, 1, 1, norm=norm, bias=False),
        )
        for m in self.net:
            if is_conv(m):
                nn.init.orthogonal_(m.weight)

    def expand_embeddings(x: Tensor, durations: Tensor):
        expanded = []
        durations = durations.clamp_min(torch.ones_like(durations))
        for b in range(x.size(0)):
            expanded.append(torch.repeat_interleave(x[b], durations[b].long(), dim=0))
        return torch.stack(expanded)

    def forward(self, x: Tensor):
        # x: [B, T, emb]
        B, _, _ = x.shape
        return self.net(x.transpose(1, 2)).view(B, -1).exp()


class TextEncoder(Model):
    def __init__(
        self,
        vocab_size: int,
        d_model: int = 256,
        kernel_sizes: List[int] = (3, 3, 3, 3),
        padding_id: int = 0,
        mask_value: Number = 0.0,
        activation: nn.Module = nn.LeakyReLU(0.1),
        norm: Optional[Literal["weight_norm", "spectral_norm"]] = "weight_norm",
    ):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=padding_id)
        self.mask_value = mask_value
        self.cnn = nn.ModuleList()
        for k in kernel_sizes:
            self.cnn.append(
                Conv1dNorm(
                    d_model, k, activation=activation, norm=norm, mask_value=mask_value
                )
            )

        self.rnn = nn.LSTM(
            d_model,
            d_model,
            1,
            batch_first=True,
            bidirectional=True,
        )
        self.proj_out = nn.Sequential(
            nn.LeakyReLU(0.1),
            nn.Linear(d_model * 2, d_model),
        )
        self.duration_pred = DurationPredictor(d_model, hidden=d_model, norm=norm)

    def forward(
        self,
        input_ids: Tensor,
        lengths: List[int] = None,
        mask: Optional[Tensor] = None,
    ):
        B, T = input_ids.size(0), input_ids.size(-1)
        x: Tensor = self.embedding(input_ids.view(B, T))  # [B, T, emb]
        x = x.transpose(-1, -2)  # [B, emb, T]

        for c in self.cnn:
            x = c(x, mask)

        if mask is not None:
            x.masked_fill_(mask, self.mask_value)

        x = x.transpose(-1, -2)

        if lengths is None:
            lengths = [T]
        elif isinstance(lengths, Tensor):
            lengths = lengths.clone().detach().cpu().long().tolist()

        packed = nn.utils.rnn.pack_padded_sequence(
            x,
            lengths,
            batch_first=True,
            enforce_sorted=False,
        )
        self.rnn.flatten_parameters()
        out_packed = self.rnn(packed)[0]
        x = nn.utils.rnn.pad_packed_sequence(out_packed, batch_first=True)[0]
        x = self.proj_out(x)
        dur = self.duration_pred(x)
        x = x.transpose(-1, -2)
        if mask is not None:
            x.masked_fill_(mask, self.mask_value)
        return x, dur


class StyleEncoder(ConvBase):
    def __init__(
        self,
        n_mels: int = 80,
        hidden: int = 128,
        out_dim: int = 64,
        fc_bias: bool = True,
        norm: Optional[Literal["weight_norm", "spectral_norm"]] = "weight_norm",
        activation: nn.Module = nn.LeakyReLU(0.1),
    ):
        super().__init__()
        self.n_mels = n_mels
        self.hidden = hidden
        pad = lambda k, d: ((k - 1) * d) // 2
        self.net = nn.Sequential(
            self.get_1d_conv(
                n_mels, hidden, kernel_size=3, stride=2, padding=1, norm=norm
            ),
            activation,
            self.get_1d_conv(
                hidden, hidden, kernel_size=5, dilation=2, padding=pad(5, 2), norm=norm
            ),
            activation,
            self.get_1d_conv(
                hidden, hidden, kernel_size=3, stride=2, padding=1, norm=norm
            ),
            activation,
            nn.AdaptiveAvgPool1d(1),
        )
        self.fc = nn.Linear(hidden, out_dim, bias=fc_bias)

    def forward(self, mel: Tensor) -> Tensor:
        B = 1 if mel.ndim < 3 else mel.size(0)
        mel = self.net(mel.view(B, self.n_mels, -1)).view(B, self.hidden)  # [B, h]
        return self.fc(mel)  # [B, dim_out]
