import math
import torch
import warnings
import numpy as np
from io import BytesIO
from torch import Tensor
from lt_utils.common import *
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objs._figure import Figure
from lt_tensor.tensor_ops import to_torch_tensor, to_numpy_array


def time_weighted_avg(data: np.ndarray, alpha: float = 0.9) -> np.ndarray:
    """
    Compute time-weighted moving average for smoothing.
    Args:
        data: [T] or [N, T] tensor (time series)
        alpha: smoothing factor (0 < alpha < 1), higher = smoother
    Returns:
        smoothed tensor of same shape
    """
    data = np.asanyarray(data).squeeze()
    if data.ndim == 1:
        out = np.zeros_like(data)
        out[0] = data[0]
        for t in range(1, len(data)):
            out[t] = alpha * out[t - 1] + (1 - alpha) * data[t]
        return out
    elif data.ndim == 2:
        out = np.zeros_like(data)
        out[:, 0] = data[:, 0]
        for t in range(1, data.shape[1]):
            out[:, t] = alpha * out[:, t - 1] + (1 - alpha) * data[:, t]
        return out
    else:
        raise ValueError("Data must be 1D or 2D time series")


def time_weighted_ema(data: Union[Tensor, np.ndarray], alpha: float = 0.5):
    """
    Compute the time-weighted Exponential Moving Average (EMA) for a given data array.

    Parameters:
    - data: array-like, the input data to smooth.
    - alpha: float, the smoothing factor (0 < alpha ≤ 1). Higher alpha discounts older observations faster.

    Returns:
    - ema: numpy array, the smoothed data.
    """
    data = to_numpy_array(data)
    ema = np.zeros_like(data)
    alpha = min(max(float(alpha), 0.00001), 0.99999)
    ema[0] = data[0]  # Initialize with the first data point
    for t in range(1, len(data)):
        ema[t] = alpha * data[t] + alpha * ema[t - 1]
    return ema


def plot_view(
    data: Dict[str, List[Any]],
    title: str = "Loss",
    xaxis_title="Step/Epoch",
    yaxis_title="Loss",
    template="plotly_dark",
    smoothing: Optional[Literal["ema", "avg"]] = None,
    alpha: float = 0.5,
    *args,
    **kwargs,
):
    fig: Figure = go.Figure()
    for mode, values in data.items():
        if values:
            if not smoothing:
                items = values
            elif smoothing == "avg":
                items = time_weighted_avg(values, kwargs.get("smoothing_alpha", alpha))
            else:
                items = time_weighted_ema(values, kwargs.get("smoothing_alpha", alpha))
            fig.add_trace(go.Scatter(y=items, name=mode.capitalize()))
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        template=template,
    )
    return fig


CMAP_TP: TypeAlias = Literal[
    "aggrnyl",
    "agsunset",
    "blackbody",
    "bluered",
    "blues",
    "blugrn",
    "bluyl",
    "brwnyl",
    "bugn",
    "bupu",
    "burg",
    "burgyl",
    "cividis",
    "darkmint",
    "electric",
    "emrld",
    "gnbu",
    "greens",
    "greys",
    "hot",
    "inferno",
    "jet",
    "magenta",
    "magma",
    "mint",
    "orrd",
    "oranges",
    "oryel",
    "peach",
    "pinkyl",
    "plasma",
    "plotly3",
    "pubu",
    "pubugn",
    "purd",
    "purp",
    "purples",
    "purpor",
    "rainbow",
    "rdbu",
    "rdpu",
    "redor",
    "reds",
    "sunset",
    "sunsetdark",
    "teal",
    "tealgrn",
    "turbo",
    "viridis",
    "ylgn",
    "ylgnbu",
    "ylorbr",
    "ylorrd",
    "algae",
    "amp",
    "deep",
    "dense",
    "gray",
    "haline",
    "ice",
    "matter",
    "solar",
    "speed",
    "tempo",
    "thermal",
    "turbid",
    "armyrose",
    "brbg",
    "earth",
    "fall",
    "geyser",
    "prgn",
    "piyg",
    "picnic",
    "portland",
    "puor",
    "rdgy",
    "rdylbu",
    "rdylgn",
    "spectral",
    "tealrose",
    "temps",
    "tropic",
    "balance",
    "curl",
    "delta",
    "oxy",
    "edge",
    "hsv",
    "icefire",
    "phase",
    "twilight",
    "mrybm",
    "mygbm",
]


def plot_token_heatmap_grid(
    tokens_ids: List[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    decoded_tokens: List[str] = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    token_scores: List[float] = [
        0.9206,
        0.911,
        0.7963,
        0.9423,
        0.2089,
        0.2474,
        0.9381,
        0.0112,
        0.8727,
        0.7906,
    ],
    c_map: CMAP_TP = "deep",
    n_cols: int = 5,
    title: str = "Token Heatmap",
    template="plotly_dark",
):
    import math

    n_tokens = len(tokens_ids)
    n_rows = math.ceil(n_tokens / n_cols)

    # Pad so grid is rectangular
    pad_size = n_rows * n_cols - n_tokens
    tokens_ids = tokens_ids + [None] * pad_size
    decoded_tokens = decoded_tokens + [""] * pad_size
    token_scores = token_scores + [np.nan] * pad_size

    # Reshape into grid
    ids_grid = np.array(tokens_ids).reshape(n_rows, n_cols)
    txts_grid = np.array(decoded_tokens).reshape(n_rows, n_cols)
    scores_grid = np.array(token_scores).reshape(n_rows, n_cols)

    # Build hover text
    hover_grid = np.empty_like(txts_grid, dtype=object)
    for i in range(n_rows):
        for j in range(n_cols):
            if ids_grid[i, j] is None:
                hover_grid[i, j] = ""
            else:
                hover_grid[i, j] = (
                    f"Token: {txts_grid[i, j]}<br>"
                    f"ID: {ids_grid[i, j]}<br>"
                    f"Score: {scores_grid[i, j]:.4f}"
                )

    # Create heatmap
    fig: Figure = go.Figure(
        data=go.Heatmap(
            z=scores_grid,
            text=txts_grid,  # show tokens in cells
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverinfo="text",
            customdata=hover_grid,
            hovertemplate="%{customdata}<extra></extra>",
            colorscale=c_map,
            colorbar=dict(title="Score"),
        )
    )

    fig.update_layout(
        title=title,
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False, autorange="reversed"),
        height=300 + n_rows * 30,
        template=template,
    )
    return fig


def get_image(
    image_tensor: Tensor,
    c_map: Optional[CMAP_TP] = None,
    width: Optional[Number] = None,
    height: Optional[Number] = None,
    title: Optional[str] = None,
    color_first: bool = True,
    return_plot: bool = False,
    template: Optional[Union[Literal["plotly_dark"]]] = None,
    scale_factor: Number = 1.0,
    x_axes_visible: bool = False,
    y_axes_visible: bool = False,
):
    import PIL.Image

    image_tensor = torch.as_tensor(image_tensor)

    image_tensor = image_tensor.clone().detach().cpu()
    if image_tensor.ndim == 4:
        # dont process batched
        image_tensor = image_tensor[0, ...]
    if color_first:
        image_tensor = image_tensor.permute(1, 2, 0)
    H, W, C = image_tensor.shape
    image_tensor = image_tensor.numpy(force=True)

    top_space = 2
    if isinstance(title, str):
        if not title.strip():
            title = None
        else:
            top_space = 48

    if width is None:
        width = W
    if height is None:
        height = H

    image = px.imshow(
        image_tensor,
        color_continuous_scale=c_map,
        title=title,
        width=width,
        height=height,
    )
    image.update_layout(
        width=width * scale_factor,
        height=height * scale_factor,
        margin={"l": 2, "r": 2, "t": top_space, "b": 2},
        template=template,
    )
    image.update_xaxes(visible=x_axes_visible)
    image.update_yaxes(visible=y_axes_visible)
    if return_plot:
        return image
    return PIL.Image.open(BytesIO(image.to_image()))


def show_spectrogram_multiple(
    audios: List[Tensor],
    titles: Optional[List[str]] = None,
    sample_rate: int = 24000,
    n_fft: int = 1024,
    hop_length: int = 256,
    win_length: int = 1024,
    center: bool = True,
    c_map: CMAP_TP = "viridis",
    top_db: Optional[float] = 80.0,
    floor_db: Optional[float] = None,
    window: str = "hann",
    periodic: bool = False,
    alpha: float = 1.0,
    beta: float = 1.0,
    cols: int = 1,
    size_fig: float = 12,
    height_factor: float = 3.14,
    power: float = 1.0,
    template: Union[str, Any] = "plotly_dark",
):
    from lt_tensor.processors.audio.misc import SpectrogramSTFT

    # safety checks
    n = len(audios)
    rows = int(np.ceil(n / cols))
    if titles is None:
        titles = [f"Spectrogram {i+1}" for i in range(n)]

    # --- subplot structure
    fig: Figure = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=titles,
        horizontal_spacing=0.125,
        vertical_spacing=0.08,
    )

    # --- spectrogram calculator
    get_spec = SpectrogramSTFT(
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=win_length,
        window=window,
        periodic=periodic,
        alpha=alpha,
        beta=beta,
        center=center,
        top_db=top_db,
        floor_db=floor_db,
        power=power,
    )

    # --- loop through all audios
    for i, audio in enumerate(audios):
        if isinstance(audio, Tensor):
            audio = audio.clone().detach().squeeze().cpu().float()
        else:
            audio = torch.as_tensor(audio).squeeze().cpu().float()

        with torch.no_grad():
            spec_db = get_spec(audio).numpy(force=True)

        # time and freq axes
        time_axis = np.arange(spec_db.shape[1]) * hop_length / sample_rate
        freq_axis = np.linspace(0, sample_rate / 2, spec_db.shape[0])

        # determine subplot position
        row = i // cols + 1
        col = i % cols + 1

        fig.add_trace(
            go.Heatmap(
                z=spec_db,
                x=time_axis,
                y=freq_axis,
                colorscale=c_map,
                colorbar=dict(title=dict(text="dB", side="right")),
                showscale=(i == n - 1),  # show scale only on last plot
                zsmooth="best",
            ),
            row=row,
            col=col,
        )

    # layout styling
    y_size = size_fig / height_factor
    fig.update_layout(
        width=int(size_fig * 100),
        height=int(y_size * 100 * rows),
        title="Multi-panel Spectrograms",
        template=template,
        margin={"l": 32, "r": 32, "t": 128, "b": 64},
    )

    fig.update_xaxes(title="Time [s]")
    fig.update_yaxes(title="Frequency [Hz]")

    return fig


def show_spectrogram(
    audio: Tensor,
    sample_rate: int = 24000,
    n_fft: int = 2048,
    hop_length: int = 512,
    win_length: int = 2048,
    size_fig: float = 12,
    center: bool = True,
    c_map: CMAP_TP = "viridis",
    height_factor: float = 3.14,
    window: str = "hann",
    periodic: bool = False,
    alpha: float = 1.0,
    beta: float = 1.0,
    top_db: Optional[float] = 80.0,
    floor_db: Optional[float] = None,
    x_axes_visible: bool = True,
    y_axes_visible: bool = True,
    power: float = 1.0,
    template: Union[str, Any] = "plotly_dark",
):
    from lt_tensor.processors.audio.misc import SpectrogramSTFT

    # --- prepare audio tensor
    if isinstance(audio, Tensor):
        audio = audio.clone().detach().squeeze().cpu().float()
    else:
        audio = torch.as_tensor(audio).squeeze().cpu().float()

    # --- compute spectrogram
    get_spec = SpectrogramSTFT(
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=win_length,
        window=window,
        periodic=periodic,
        alpha=alpha,
        beta=beta,
        center=center,
        top_db=top_db,
        floor_db=floor_db,
        power=power,
    )

    with torch.no_grad():
        spec = get_spec(audio)
        spec_db = get_spec.amplitude_to_db(spec).numpy(force=True)

    # --- axes
    time_axis = np.arange(spec_db.shape[1]) * hop_length / sample_rate
    freq_axis = np.linspace(0, sample_rate / 2, spec_db.shape[0])

    # --- figure
    y_size = size_fig / height_factor
    fig: Figure = go.Figure(
        data=go.Heatmap(
            z=spec_db,
            x=time_axis,
            y=freq_axis,
            colorscale=c_map,
            colorbar=dict(title=dict(text="dB", side="right")),
            zsmooth="best",
        )
    )

    fig.update_layout(
        title="Spectrogram (dB)",
        xaxis_title="Time [s]",
        yaxis_title="Frequency [Hz]",
        width=int(size_fig * 100),
        height=int(y_size * 100),
        template=template,
        margin={"l": 2, "r": 2, "t": 48, "b": 2},
    )

    fig.update_yaxes(scaleanchor=None, scaleratio=None)
    fig.update_xaxes(showgrid=False, visible=x_axes_visible)
    fig.update_yaxes(showgrid=False, visible=y_axes_visible)
    return fig


def show_mel_spectrogram(
    audio: Tensor,
    mel_fn: Optional[Callable[[Tensor], Tensor]] = None,
    sample_rate: int = 24000,
    n_mels: int = 80,
    n_fft: int = 1024,
    win_length: int = 1024,
    hop_length: int = 256,
    size_fig: float = 12,
    c_map: CMAP_TP = "viridis",
    height_factor: float = 3.14,
    window: str = "hann",
    periodic: bool = False,
    alpha: float = 1.0,
    beta: float = 1.0,
    f_min: float = 0.0,
    f_max: Optional[float] = None,
    top_db: float = 80.0,
    x_axes_visible: bool = True,
    y_axes_visible: bool = True,
    power: Number = 1,
    template: Union[str, Any] = "plotly_dark",
    normalizer: Optional[Callable[[Tensor], Tensor]] = None,
    min_max_norm: bool = True,
):
    from lt_tensor.processors.audio.misc import MelSpectrogram
    from lt_tensor.processors.audio.filtering import amplitude_to_db

    # --- prepare audio tensor
    if isinstance(audio, Tensor):
        audio = audio.clone().detach().squeeze().cpu().float()
    else:
        audio = torch.as_tensor(audio).squeeze().squeeze().cpu().float()
    if not f_max:
        f_max = sample_rate / 2
    # --- compute spectrogram
    if mel_fn is None:
        mel_fn = MelSpectrogram(
            sample_rate=sample_rate,
            n_mels=n_mels,
            n_fft=n_fft,
            hop_length=hop_length,
            win_length=win_length,
            window=window,
            periodic=periodic,
            alpha=alpha,
            beta=beta,
            f_min=f_min,
            f_max=f_max,
            power=power,
            normalize_min_max=min_max_norm,
        )

    with torch.no_grad():
        spec_db = mel_fn(audio)
        if normalizer is not None:
            spec_db = normalizer(spec_db)
        else:
            spec_db = amplitude_to_db(spec_db, top_db=top_db)
        spec_db = spec_db.numpy(force=True)

    # --- axes
    time_axis = np.arange(spec_db.shape[1]) * hop_length / sample_rate
    freq_axis = np.linspace(0, sample_rate / 2, spec_db.shape[0])

    # --- figure
    y_size = size_fig / height_factor
    fig: Figure = go.Figure(
        data=go.Heatmap(
            z=spec_db,
            x=time_axis,
            y=freq_axis,
            colorscale=c_map,
            colorbar=dict(title=dict(text="dB", side="right")),
            zsmooth="best",
        )
    )

    fig.update_layout(
        title="Spectrogram (dB)",
        xaxis_title="Time [s]",
        yaxis_title="Frequency [Hz]",
        width=int(size_fig * 100),
        height=int(y_size * 100),
        template=template,
        margin={"l": 2, "r": 2, "t": 48, "b": 2},
    )

    fig.update_yaxes(scaleanchor=None, scaleratio=None)
    fig.update_xaxes(showgrid=False, visible=x_axes_visible)
    fig.update_yaxes(showgrid=False, visible=y_axes_visible)
    return fig


def show_tempogram(
    audio: Tensor,
    sample_rate: int = 24000,
    hop_length: int = 256,
    win_length: int = 1024,
    center: bool = True,
    size_fig: Number = 12,
    c_map: Optional[CMAP_TP] = "magma",
    height_factor: float = 3.14,
    force_close: bool = False,
):
    import librosa
    import matplotlib.pyplot as plt

    y_size = size_fig / height_factor
    if isinstance(audio, Tensor):
        audio_np = audio.clone().detach().flatten().cpu().numpy(force=True)
    else:
        audio_np = np.asarray(audio)

    onset_env = librosa.onset.onset_strength(
        y=audio_np, sr=sample_rate, hop_length=hop_length
    )
    tempogram_ref = librosa.feature.tempogram(
        onset_envelope=onset_env,
        sr=sample_rate,
        hop_length=hop_length,
        win_length=win_length,
        center=center,
    )
    # === Visualization ===
    fig, axs = plt.subplots(1, 1, figsize=(size_fig, y_size))
    librosa.display.specshow(
        tempogram_ref,
        sr=sample_rate,
        hop_length=hop_length,
        x_axis="time",
        y_axis="tempo",
        ax=axs,
        cmap=c_map,
    )
    axs.set_title("Tempogram")

    plt.tight_layout()
    if force_close:
        plt.close(fig)
    return fig
