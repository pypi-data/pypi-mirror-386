from __future__ import annotations

from lt_tensor.processors.audio.core import AudioProcessor, AudioProcessorConfig
from lt_tensor.training_utils.datasets_templates import DatasetBase
from lt_utils.file_ops import (
    load_text,
    find_dirs,
    find_files,
    get_file_name,
    is_pathlike,
    is_dir,
    is_file,
)
from lt_utils.common import *
from torch import Tensor, LongTensor
from torch.nn import functional as F
from typing import TYPE_CHECKING
import torch
import random
from lt_tensor.misc_utils import set_seed
from typing_extensions import override
from lt_tensor.noise_tools import NoiseScheduler
from contextlib import nullcontext
from .data_structs import AudioData
from .utils import *
import numpy as np

if TYPE_CHECKING:
    from tokenizers import Tokenizer
    from lt_tensor.tokenizer.tokenizer_wrapper import TokenizerWP


__all__ = ["AudioDataset"]


class AudioDataset(DatasetBase):
    """A template dataset for dataset that uses the 'libri' style"""

    data: List[AudioData] = []
    chunk_size: int = None
    fixed_size: bool = False
    _bad_files: List[str] = []
    _files_loaded: List[str] = []
    total_duration: float = 0.0
    tokenizer_has_pad: bool = False
    pad_token_id: int = 0

    def __init__(
        self,
        ap_config=AudioProcessorConfig(
            sample_rate=24000,
            n_fft=1024,
            hop_length=256,
            win_length=1024,
            n_mels=96,
            f_max=8000,
        ),
        tokenizer: Optional[Union["Tokenizer", "TokenizerWP"]] = None,
        diffusion: bool = False,
        diffusion_steps: int = 50,
        diff_beta_start: float = 0.0001,
        diff_beta_end: float = 0.05,
        *,
        mode: Literal["vocoder", "tts", "vc-tts", "style-tts"] = "vocoder",
        duration_per_track: float = 7200,
        chunk_size: int = 8192,
        norm_mel: bool = True,
        norm_wave: bool = True,
        mel_norm_tp: Literal["log_norm", "range_norm"] = "log_norm",
        diffusion_over_padded: bool = False,  # if true the diffusion noise will be applied over the padded sections of the audio.
    ):
        super().__init__()
        assert mode in [
            "vocoder",
            "tts",
            "vc-tts",
            "style-tts",
        ], f'Invalid mode {mode}. choose either "tts", "diffusion", "vc-tts" or "style-tts"'
        assert (
            mode != "tts" or tokenizer is not None
        ), 'In order to use `mode="tts"`, it will be required a tokenizer for the texts.'
        self.ap = AudioProcessor(ap_config)
        self.cfg = ap_config
        self.mel_norm_tp = mel_norm_tp
        self.tokenizer = tokenizer
        if tokenizer is not None:
            if hasattr(tokenizer, "pad"):
                if callable(tokenizer.pad):
                    try:
                        tokenizer.pad([torch.randn(1, 23), torch.randn(1, 45)])
                        self.tokenizer_has_pad = True
                    except:
                        pass
            if not self.tokenizer_has_pad:
                if hasattr(tokenizer, "pad_token_id"):
                    self.pad_token_id = tokenizer.pad_token_id
                elif hasattr(tokenizer, "pad_token"):
                    try:
                        self.pad_token_id = int(tokenizer.pad_token)
                    except:
                        self.pad_token_id = int(
                            torch.as_tensor(tokenizer.encode(tokenizer.pad_token))
                            .flatten()
                            .item()
                        )
                elif hasattr(tokenizer, "pad_id"):
                    self.pad_token_id = int(tokenizer.pad_id)

        self.mode: Literal["vocoder", "tts", "vc-tts", "style-tts"] = mode
        self.diffusion = diffusion
        self.norm_wave = norm_wave
        self.norm_mel = norm_mel
        self.duration_per_track = duration_per_track
        self.chunk_size = max(int(chunk_size), 8)
        if self.chunk_size % 8 != 0:
            self.chunk_size = int(self.chunk_size + self.chunk_size % 8)
        self.diffusion_over_padded = diffusion_over_padded
        self.scheduler = NoiseScheduler(
            max_steps=diffusion_steps,
            beta_start=diff_beta_start,
            beta_end=diff_beta_end,
        )

    def load_audio(
        self,
        file: PathLike,
        top_db: Optional[float] = None,
        noise_reduction: float = 0,
    ) -> Tensor:
        return self.ap.load_audio(
            file,
            top_db=top_db,
            mono=True,
            duration=self.duration_per_track if self.mode == "vocoder" else None,
            normalize=self.norm_wave,
            noise_reduction=noise_reduction,
        ).view(1, -1)

    def _try_find_text_file(self, audio_file: str, postfix: str = ""):
        possible_name = (
            get_file_name(audio_file, keep_extension=False) + postfix + ".txt"
        )
        possible_dir = Path(audio_file).parent / possible_name
        return possible_dir, possible_dir.exists()
        load_text, find_dirs, find_files

    def encode_text(
        self,
        text: str,
        pad_size: Optional[int] = None,
    ):
        tokens = torch.as_tensor(self.tokenizer.encode(text))
        if pad_size and tokens.size(-1) < pad_size:
            tokens = F.pad(tokens, (0, pad_size - tokens.size(-1)), value=0)
        return tokens.long()

    def decode_text(self, tokens: Union[Tensor, List[int]]):
        if isinstance(tokens, Tensor):
            tokens = tokens.clone().detach().flatten().long().tolist()
        return self.tokenizer.decode(tokens)

    def load_text(
        self,
        text_file: PathLike,
        encoding: str = "utf-8",
        encoding_errors: Literal["ignore", "strict"] = "ignore",
    ):
        return load_text(
            text_file,
            encoding=encoding,
            errors=encoding_errors,
            default_value="",
        )

    def get_audio_duration(self, wave: Tensor):
        return wave.size(-1) / self.cfg.sample_rate

    def add_to_dataset(
        self,
        audio_file: PathLike,
        audio: Tensor,
        text_file: Optional[str] = None,
        text: Optional[str] = None,
    ):
        duration = self.get_audio_duration(audio)
        self.data.append(
            AudioData(
                wave=audio,
                duration=duration,
                text=text,
                audio_path=audio_file,
                text_path=text_file,
            )
        )
        self._files_loaded.append(Path(audio_file).name)
        self.total_duration += duration

    def load_dir(
        self,
        path: PathLike,
        min_duration: Number = 1.0,
        max_duration: Optional[Number] = None,  # only relevant to tts
        max_files: int = 999_999,
        min_files_per_dir: int = 5,
        max_files_per_dir: int = 100_000,
        show_progress: bool = True,
        text_file_postfix: str = ".original",
        text_encoding: Optional[
            Union[str, Literal["utf-8", "ascii", "unicode-escape", "latin-1"]]
        ] = "utf-8",
        text_errors: Union[str, Literal["strict", "ignore"]] = "ignore",
        top_db: Optional[float] = None,
        noise_reduction: float = 0,
        do_vad: bool = False,  # remove some of the silence portions of the audio
    ):
        max_files = int(max(max_files, 1))
        min_duration = max(min_duration, 0.1)
        found_files = [
            x
            for x in self.ap.find_audios(path)
            if Path(x).name not in self._files_loaded
        ]
        # stats:
        accepted = 0
        total_found = len(found_files)
        total_found_postfix = format(total_found, ",").replace(",", ".")
        old_time = self.total_duration
        # easier info collect
        old_files = len(self.data)

        def get_info():
            return {
                "data": len(self.data) - old_files,
                "time": self.total_duration - old_time,
                "total_data": len(self.data),
                "total_time": self.total_duration,
            }

        new_data = find_load_validate_audios(
            ap=self.ap,
            root_dir=path,
            black_list=self._files_loaded,
            min_time=min_duration,
            max_time=max_duration,
            max_audios=max_files,
            max_audios_per_dir=max_files_per_dir,
            min_audios_per_dir=min_files_per_dir,
            normalize=self.cfg.normalized,
            top_db=top_db,
            noise_reduction=noise_reduction,
            mono=True,
            show_progress=show_progress,
            search_text_file="tts" in self.mode,
            requires_text_file="tts" in self.mode,
            text_file_postfix=text_file_postfix,
            text_encoding=text_encoding,
            text_errors=text_errors,
            do_vad=do_vad,
        )
        if new_data:
            for data in new_data:
                self.data.append(data)
                self.total_duration += data.duration
        return get_info()

    def compute_mel(self, wave: Tensor) -> Tensor:
        B = 1 if wave.ndim < 2 else wave.size(0)
        return self.ap.compute_mel(
            wave,
            norm=self.norm_mel,
            norm_type=self.mel_norm_tp,
        ).view(B, self.cfg.n_mels, -1)

    @override
    def sample(self, seed: Optional[int] = None, *args, **kwargs):
        total = len(self)
        if not total:
            raise RuntimeError("The dataset is empty!")
        item_ids: List[int] = torch.arange(0, total).tolist()
        if seed is not None:
            set_seed(seed)
        idx = random.choice(item_ids)
        data = self.data[idx]
        if self.mode != "vocoder":
            return data
        return self.ap.audio_splitter(data.wave, chunk_size=self.chunk_size)

    def samples(
        self,
        number: int = 1,
        seed: Optional[int] = None,
        show_progress: bool = False,
        auto_adjust: bool = False,
        randomized: bool = False,
        *args,
        **kwargs,
    ):
        total = len(self)
        if not total:
            raise RuntimeError("The dataset is empty!")
        number = int(max(number, 1))

        if total < number:
            if not auto_adjust:
                raise RuntimeError(
                    f"The dataset does not contain {number} of items available. It only has {len(self.data)}."
                )
            number = total
        items_ids: List[int] = torch.arange(0, total).tolist()
        if not randomized:
            item_ids = items_ids[:number]
        else:
            if seed is not None:
                set_seed(seed)
            item_ids = random.sample(items_ids, k=number)
        if self.mode != "vocoder":
            return [self.__getitem__(i) for i in item_ids]

        fragmented = []
        if show_progress:
            from tqdm import tqdm

            progress = tqdm(items_ids, "Processing data")
        else:
            progress = items_ids

        for i in progress:
            fragmented.extend(
                self.ap.audio_splitter(self.data[i].wave, chunk_size=self.chunk_size)
            )
        return fragmented

    def _try_find_reference_to(self, target: AudioData):
        seq = torch.arange(0, len(self.data), 1).flatten().tolist()
        random.shuffle(seq)
        for i in seq:
            if target.can_be_reference_to_other(
                self.data[i],
                text_required=False,
                should_speaker_be_equal=self.mode == "style-tts",
                can_share_same_id=True,
            ):
                return self.data[i].wave, True
        return torch.zeros(1, self.chunk_size * 2), False

    def _collate_diffusion(self, batch: Sequence[AudioData]):
        B = len(batch)
        if self.mode != "vocoder":
            tokens = [self.encode_text(x.text) for x in batch]
            mels = [self.compute_mel(x.wave) for x in batch]
            lengths = [x.size(-1) for x in tokens]
            largest_text = max(lengths)
            largest_audio = max([x.wave.size(-1) for x in batch])
            largest_mel = max([x.size(-1) for x in mels])

            if self.tokenizer_has_pad:
                inp_ids: Tensor = self.tokenizer.pad(tokens)
            else:
                inp_ids: Tensor = torch.stack(
                    [
                        F.pad(
                            x, (0, largest_text - x.size(-1)), value=self.pad_token_id
                        )
                        for x in tokens
                    ],
                    dim=0,
                )
            waves = [F.pad(x.wave, (0, largest_audio - x.wave.size(-1))) for x in batch]

            _waves = waves if self.diffusion_over_padded else [x.wave for x in batch]
            # we will try to cover all possible use-cases, so this may be slower than it should
            xt = []  # xt = noised wave
            eps = []  # eps = noise
            t = []  # t = time-step
            xt_mel = []  # = noised mel
            eps_mel = []  # = noise mel
            references = None
            if self.mode in ["vc-tts", "style-tts"]:
                reference_mel: List[Tensor] = []
                _largest_ref_mel = 0
                for x in batch:
                    ref = self._try_find_reference_to(x)[0]
                    reference_mel.append(self.compute_mel(ref))
                    if reference_mel[-1].size(-1) > _largest_ref_mel:
                        _largest_ref_mel = reference_mel[-1].size(-1)
                references = (
                    torch.stack(
                        [
                            F.pad(x, (0, _largest_ref_mel - x.size(-1)))
                            for x in reference_mel
                        ]
                    ).view(B, self.cfg.n_mels, -1),
                )

            for w in _waves:
                _xt, _eps, _t = self.scheduler.q_sample(w)
                _xt_mel = self.compute_mel(_xt)
                _eps_mel = self.compute_mel(_eps)
                if not self.diffusion_over_padded:
                    # xt padding
                    _xt = F.pad(_xt, (0, largest_audio - _xt.size(-1)))
                    _xt_mel = F.pad(_xt_mel, (0, largest_mel - _xt_mel.size(-1)))
                    # eps padding
                    _eps = F.pad(_eps, (0, largest_audio - _eps.size(-1)))
                    _eps_mel = F.pad(_eps_mel, (0, largest_mel - _eps_mel.size(-1)))

                xt.append(_xt)
                eps.append(_eps)
                t.append(_t)
                xt_mel.append(_xt_mel)
                eps_mel.append(_eps_mel)
            return dict(
                input_ids=inp_ids.view(B, -1),
                wave=torch.stack(waves).view(B, 1, -1),
                xt=torch.stack(xt).view(B, 1, -1),
                eps=torch.stack(eps).view(B, 1, -1),
                t=torch.stack(t).view(B, -1),
                mel=torch.stack(
                    [F.pad(x, (0, largest_mel - x.size(-1))) for x in mels]
                ).view(B, self.cfg.n_mels, -1),
                xt_mel=torch.stack(xt_mel).view(B, self.cfg.n_mels, -1),
                eps_mel=torch.stack(eps_mel).view(B, self.cfg.n_mels, -1),
                reference=references,
                lengths=lengths,
            )
        waves = [self.ap.random_segment(x.wave) for x in batch]
        xt = []  # noised wave
        eps = []  # noise
        t = []  # time-step
        xt_mel = []  # noised mel
        eps_mel = []  # noise mel
        for wave in waves:
            _xt, _eps, _t = self.scheduler.q_sample(wave)
            _xt_mel = self.compute_mel(_xt)
            _eps_mel = self.compute_mel(_eps)
            # it does not make difference here, so we dont need to pad regardless:
            xt.append(_xt)
            eps.append(_eps)
            t.append(_t)
            xt_mel.append(_xt_mel)
            eps_mel.append(_eps_mel)
        return dict(
            wave=torch.stack(waves, dim=0).view(B, 1, -1),
            xt=torch.stack(xt).view(B, 1, -1),
            eps=torch.stack(eps).view(B, 1, -1),
            t=torch.stack(t).view(B, -1),
            mel=torch.stack([self.compute_mel(x) for x in waves]).view(
                B, self.cfg.n_mels, -1
            ),
            xt_mel=torch.stack(xt_mel).view(B, self.cfg.n_mels, -1),
            eps_mel=torch.stack(eps_mel).view(B, self.cfg.n_mels, -1),
        )

    def _collate_base(self, batch: Sequence[AudioData]):
        B = len(batch)
        if self.mode != "vocoder":
            tokens = [self.encode_text(x.text) for x in batch]
            mels = [self.compute_mel(x.wave) for x in batch]
            lengths = [x.size(-1) for x in tokens]
            largest_text = max(lengths)
            largest_audio = max([x.wave.size(-1) for x in batch])
            largest_mel = max([x.size(-1) for x in mels])
            # reference
            references = None
            if self.mode in ["vc-tts", "style-tts"]:
                reference_mel: List[Tensor] = []
                _largest_ref_mel = 0
                for x in batch:
                    ref = self._try_find_reference_to(x)[0]
                    reference_mel.append(self.compute_mel(ref))
                    if reference_mel[-1].size(-1) > _largest_ref_mel:
                        _largest_ref_mel = reference_mel[-1].size(-1)
                references = (
                    torch.stack(
                        [
                            F.pad(x, (0, _largest_ref_mel - x.size(-1)))
                            for x in reference_mel
                        ]
                    ).view(B, self.cfg.n_mels, -1),
                )

            if self.tokenizer_has_pad:
                inp_ids: Tensor = self.tokenizer.pad(tokens)
            else:
                inp_ids: Tensor = torch.stack(
                    [
                        F.pad(
                            x, (0, largest_text - x.size(-1)), value=self.pad_token_id
                        )
                        for x in tokens
                    ],
                    dim=0,
                )
            return dict(
                input_ids=inp_ids.view(B, -1),
                wave=torch.stack(
                    [F.pad(x.wave, (0, largest_audio - x.wave.size(-1))) for x in batch]
                ).view(B, 1, -1),
                mel=torch.stack(
                    [F.pad(x, (0, largest_mel - x.size(-1))) for x in mels]
                ).view(B, self.cfg.n_mels, -1),
                references=references,
                lengths=lengths,
            )
        waves = [self.ap.random_segment(x.wave) for x in batch]
        return dict(
            wave=torch.stack(waves, dim=0).view(B, 1, -1),
            mel=torch.stack([self.compute_mel(x) for x in waves]).view(
                B, self.cfg.n_mels, -1
            ),
        )

    @override
    def collate_fn(self, batch: Sequence[AudioData]):
        if self.diffusion:
            return self._collate_diffusion(batch)
        return self._collate_base(batch)
