__all__ = ["RandomAudioModifier", "BandFilter", "MelSpectrogram", "SpectrogramSTFT"]
import random
from lt_utils.common import *
from lt_utils.misc_utils import default
from lt_tensor.common import *
from .core import AudioProcessor
import torchaudio
from torchaudio.functional.filtering import (
    flanger,
    highpass_biquad,
    treble_biquad,
    lowpass_biquad,
    bass_biquad,
)
from lt_tensor.tensor_ops import normalize_minmax, log_norm
from lt_tensor.misc_utils import get_window


class RandomAudioModifier:
    def __init__(
        self,
        audio_processor: AudioProcessor,
        p: float = 0.999,
        use_noise: bool = False,
        use_distortions: bool = True,
        min_aug_per_cycle: int = 5,
        max_aug_per_cycle: int = 5,
    ):
        self.ap = audio_processor
        self.sample_rate = self.ap.cfg.sample_rate
        self.p = p
        self.use_noise = use_noise
        self.use_distortions = use_distortions
        self.min_aug_per_cycle = min_aug_per_cycle
        self.max_aug_per_cycle = max_aug_per_cycle
        # self.set_aug()
        self.noises = [
            self.add_gaussian,
            self.add_pink,
            self.add_impulse,
            self.radio_chop,
            self.band_drop,
        ]
        self.augs = [
            self.pitch_shift,
            self.tremble_bq,
            self.bass_bq,
            self.highpass_bq,
            self.lowpass_bq,
        ]

    def set_aug(self):
        self.aug_fns = []
        if self.use_noise:
            self.aug_fns.extend(
                [
                    self.add_gaussian,
                    self.add_pink,
                    self.add_impulse,
                    self.radio_chop,
                    self.band_drop,
                ]
            )
        if self.use_distortions:
            _aug_fns = [
                self.pitch_shift,
                self.tremble_bq,
                self.bass_bq,
                self.highpass_bq,
                self.lowpass_bq,
            ]
            if self.use_noise:
                for _ in range(3):
                    for item in _aug_fns.copy():
                        self.aug_fns.append(item)

    def pitch_shift(self, x: Tensor):
        return self.ap.pitch_shift(
            x, n_steps=random.choice([random.randint(-5, -1), random.randint(1, 5)])
        ).view(1, -1)

    def tremble_bq(self, x: Tensor):
        return treble_biquad(x, self.ap.cfg.sample_rate, gain=random.uniform(0.25, 15))

    def bass_bq(self, x: Tensor):
        return bass_biquad(x, self.ap.cfg.sample_rate, gain=random.uniform(0.25, 15))

    def highpass_bq(self, x: Tensor):
        return highpass_biquad(
            x, self.ap.cfg.sample_rate, cutoff_freq=random.uniform(200, 3000)
        )

    def lowpass_bq(self, x: Tensor):
        return lowpass_biquad(
            x, self.ap.cfg.sample_rate, cutoff_freq=random.uniform(200, 3000)
        )

    @staticmethod
    def add_gaussian(x: Tensor):
        noise = torch.randn_like(x) * random.uniform(0.001, 0.05)
        return x + noise

    @staticmethod
    def add_pink(x):
        # approximate pink noise via 1/f filter
        n = x.shape[-1]
        freqs = torch.fft.rfftfreq(n)
        pink_filter = torch.clamp(1 / torch.sqrt(freqs + 1e-6), 0, 5)
        pink_noise = torch.fft.irfft(torch.fft.rfft(torch.randn_like(x)) * pink_filter)
        pink_noise = pink_noise / pink_noise.abs().max()
        return x + pink_noise * random.uniform(0.001, 0.05)

    @staticmethod
    def add_impulse(x: Tensor):
        noise = torch.zeros_like(x)
        for _ in range(random.randint(2, 11)):
            idx = random.randint(0, len(x) - 1)
            noise[idx] = random.uniform(-0.5, 0.5)
        return x + noise

    @staticmethod
    def radio_chop(x: Tensor):
        # simulate packet loss / glitchy transmission
        n = x.shape[-1]
        chop_len = random.randint(int(0.01 * n), int(0.125 * n))
        start = random.randint(0, n - chop_len)
        x[start : start + chop_len] *= random.uniform(0.0, 0.2)
        return x

    @staticmethod
    def band_drop(x: Tensor):
        # drop a random frequency band
        X = torch.fft.rfft(x)
        n = X.shape[-1]
        band = random.randint(n // 20, n // 5)
        start = random.randint(0, n - band)
        X[..., start : start + band] *= 1e-5
        return torch.fft.irfft(X)

    def __call__(self, audio: Tensor):
        if random.random() > self.p:
            return audio
        augs = []
        if self.use_noise:
            augs.extend(self.noises)
        if self.use_distortions:
            augs.extend(self.augs)

        audio_min, audio_max = audio.min().item(), audio.max().item()
        for _ in range(random.randint(self.min_aug_per_cycle, self.max_aug_per_cycle)):
            audio = random.choice(augs)(audio)
        return normalize_minmax(audio, audio_min, audio_max)


class BandFilter(Model):
    def __init__(
        self,
        type_fn: Literal[
            "band",
            "lowpass",
            "highpass",
            "allpass",
            "bandpass",
            "bandreject",
            "bass",
            "treble",
            "equalizer",
        ] = "band",
        sr: Number = 24000,
        q_factor: float = 0.707,
        central_freq: float = 3072.0,
        gain: float = 1.0,
        noise_csg: bool = False,
        requires_grad: bool = True,
        gain_requires_grad: bool = True,
        *args,
        **kwargs,
    ) -> None:
        """
        Args:
            central_freq: (float, optional): Will be used as either central freq or cutoff_freq
                                            case type_fn is set to `lowpass`or `highpass`
            noise_csg: (bool, optional): Is used as 'noise' argument for 'band_biquad', and as 'const_skirt_gain' for 'bandpass_biquad'.
        """
        super().__init__()
        _valid_fn = [
            "band",
            "lowpass",
            "highpass",
            "allpass",
            "bandpass",
            "bandreject",
            "bass",
            "treble",
            "equalizer",
        ]
        assert type_fn in _valid_fn, (
            f'Invalid type_fn: {type_fn}. It must be: "' + '", '.join(_valid_fn) + '".'
        )
        self.sr = sr
        self.noise_csg = noise_csg

        # initial guardrails:

        central_freq = float(max(central_freq, 1e-4))
        q_factor = float(max(q_factor, 1e-4))

        self.central_freq = nn.Parameter(
            torch.as_tensor(central_freq),
            requires_grad=requires_grad,
        )
        self.Q_factor = nn.Parameter(
            torch.as_tensor(q_factor),
            requires_grad=requires_grad,
        )
        self.type_fn = type_fn
        self.gain = nn.Parameter(
            torch.as_tensor(float(gain)),
            requires_grad=gain_requires_grad and self.type_fn == "bass",
        )
        # to avoid NaN and zero values we clamp
        # both central frequencies[min,max] and q factor[min]
        self.register_buffer("cf_min", torch.as_tensor(1e-3))
        self.register_buffer("cf_max", torch.as_tensor((sr / 2)))
        self.register_buffer("q_min", torch.as_tensor(1e-3))

        match self.type_fn:
            case "allpass":
                self.fn = lambda x, cf, Q: torchaudio.functional.allpass_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                )
            case "bandreject":
                self.fn = lambda x, cf, Q: torchaudio.functional.bandreject_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                )
            case "lowpass":
                self.fn = lambda x, cf, Q: torchaudio.functional.lowpass_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                )
            case "highpass":
                self.fn = lambda x, cf, Q: torchaudio.functional.highpass_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                )
            case "bass":
                self.fn = lambda x, cf, Q: torchaudio.functional.bass_biquad(
                    x,
                    self.sr,
                    self.gain,
                    cf,
                    Q,
                )
            case "treble":
                self.fn = lambda x, cf, Q: torchaudio.functional.treble_biquad(
                    x,
                    self.sr,
                    self.gain,
                    cf,
                    Q,
                )
            case "equalizer":
                self.fn = lambda x, cf, Q: torchaudio.functional.equalizer_biquad(
                    x,
                    self.sr,
                    cf,
                    self.gain,
                    Q,
                )
            case "bandpass":
                self.fn = lambda x, cf, Q: torchaudio.functional.bandpass_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                    self.noise_csg,
                )
            case _:
                self.fn = lambda x, cf, Q: torchaudio.functional.band_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                    self.noise_csg,
                )

    def forward(self, x: Tensor):
        cf = self.central_freq.clamp(self.cf_min, self.cf_max)
        Q = self.Q_factor.clamp_min(self.q_min)
        return self.fn(x, cf, Q)


class SpectrogramSTFT(Model):
    def __init__(
        self,
        n_fft: int = 1024,
        hop_length: int = 256,
        win_length: int = 1024,
        window: str = "hann",
        periodic: bool = False,
        alpha: float = 1.0,
        beta: float = 1.0,
        center: bool = True,
        power: float = 1.0,
        amplitude_ref: Union[
            float, Tensor, Literal["min", "max"], Callable[[Tensor], Tensor]
        ] = "max",
        top_db: Optional[float] = None,
        floor_db: Optional[float] = None,
    ):
        super().__init__()
        self.register_buffer(
            "window",
            get_window(
                win_length,
                window_type=window,
                periodic=periodic,
                alpha=alpha,
                beta=beta,
            ),
        )
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.win_length = win_length
        self.center = center
        self.power = power
        self.amplitude_ref = amplitude_ref
        self.top_db = top_db
        self.floor_db = floor_db
        from lt_tensor.processors.audio.filtering import amplitude_to_db

        self._amp_to_db = amplitude_to_db

    def amplitude_to_db(self, spectrogram: Tensor):
        return self._amp_to_db(
            spectrogram,
            ref=self.amplitude_ref,
            top_db=self.top_db,
            floor_db=self.floor_db,
        )

    def forward(self, audio: Tensor):
        return (
            (
                torch.stft(
                    audio,
                    n_fft=self.n_fft,
                    hop_length=self.hop_length,
                    win_length=self.win_length,
                    window=self.window,
                    center=self.center,
                    return_complex=True,
                )
            )
            .abs()
            .pow(self.power)
        )


class MelSpectrogram(Model):
    def __init__(
        self,
        sample_rate: int = 24000,
        n_mels: int = 80,
        n_fft: int = 1024,
        hop_length: int = 256,
        win_length: int = 1024,
        window: str | Any = "hann",
        periodic: bool = False,
        alpha: float = 1.0,
        beta: float = 1.0,
        f_min: float = 0,
        f_max: Optional[float] = None,
        power: float = 0.5,
        *args,
        **kwargs,
    ):
        super().__init__()

        self._mel_padding = (n_fft - hop_length) // 2
        self.n_fft = n_fft
        self.n_ffft = n_fft // 2 + 1  # freqs fft
        self.hop_length = hop_length
        self.win_length = win_length
        self.power = power
        self.register_buffer(
            "window",
            get_window(
                win_length=win_length,
                window_type=window,
                periodic=periodic,
                requires_grad=False,
                alpha=alpha,
                beta=beta,
            ),
        )
        self.register_buffer(
            "mel_filter_bank",
            torchaudio.functional.melscale_fbanks(
                n_freqs=self.n_ffft,
                f_min=f_min,
                f_max=f_max,
                n_mels=n_mels,
                sample_rate=sample_rate,
                mel_scale="slaney",
            ).transpose(-1, -2),
        )

    def compute_stft(self, audio: Tensor):
        return torch.stft(
            audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.win_length,
            window=self.window,
            center=False,
            return_complex=True,
        )

    def forward(self, wave: Tensor):
        wave = wave.squeeze()
        B = 1 if wave.ndim < 2 else wave.shape[0]
        wave = wave.view(B, -1)
        wave = F.pad(
            wave,
            (self._mel_padding, self._mel_padding),
            mode="reflect",
        )
        spec = self.compute_stft(wave).abs().pow(self.power)
        results = torch.matmul(self.mel_filter_bank, spec)
        return results.squeeze()
