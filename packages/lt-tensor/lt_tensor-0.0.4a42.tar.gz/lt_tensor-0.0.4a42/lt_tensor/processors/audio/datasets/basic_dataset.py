from __future__ import annotations

from lt_tensor.processors.audio.core import AudioProcessor, AudioProcessorConfig
from lt_tensor.training_utils.datasets_templates import DatasetBase
from lt_utils.file_ops import (
    load_text,
    find_dirs,
    find_files,
    get_file_name,
)
from lt_utils.common import *
from torch import Tensor
from torch.nn import functional as F
from typing import TYPE_CHECKING
import torch
import random
from lt_tensor.misc_utils import set_seed
from typing_extensions import override
from lt_tensor.noise_tools import NoiseScheduler
from .data_structs import *
from .utils import *
from typing import Iterable
from contextlib import nullcontext

if TYPE_CHECKING:
    from tokenizers import Tokenizer
    from lt_tensor.tokenizer.tokenizer_wrapper import TokenizerWP
    from torch.utils.data import DataLoader


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
    container_cls = CollateProcessor

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
        diffusion_steps: int = 50,
        diff_beta_start: float = 0.0001,
        diff_beta_end: float = 0.05,
        *,
        mode: Literal["vocoder", "tts", "style-tts"] = "vocoder",
        duration_per_track: float = 7200,
        chunk_size: int = 8192,
        norm_mel: bool = True,
        norm_wave: bool = True,
        text_processor: Optional[Callable[[str], str]] = None,  # For example phonemizer
        mel_norm_tp: Literal["log_norm", "range_norm"] = "log_norm",
        make_references_optional: bool = False,
        device: Optional[Union[str, torch.device]] = None,
    ):
        super().__init__()
        assert mode in [
            "vocoder",
            "tts",
            "style-tts",
        ], f'Invalid mode {mode}. choose either "tts", "vocoder" or "style-tts"'
        assert (
            mode != "tts" or tokenizer is not None
        ), 'In order to use `mode="tts"`, it will be required a tokenizer for the texts.'
        self.ap = AudioProcessor(ap_config)
        self.cfg = ap_config
        self.device = device
        if device is not None:
            # we just ensure this to be valid
            # to avoid a headache later
            torch.randn(1, device=device)
        self.text_processor = text_processor
        self.mel_norm_tp = mel_norm_tp
        self.tokenizer = tokenizer
        self.make_references_optional = make_references_optional
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

        self.mode: Literal["vocoder", "tts", "style-tts"] = mode
        self.norm_wave = norm_wave
        self.norm_mel = norm_mel
        self.duration_per_track = duration_per_track
        self.chunk_size = max(int(chunk_size), 8)
        if self.chunk_size % 8 != 0:
            self.chunk_size = int(self.chunk_size + self.chunk_size % 8)
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
        # stats:
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

        tts_mode = "tts" in self.mode
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
            search_text_file=tts_mode,
            requires_text_file=tts_mode,
            text_file_postfix=text_file_postfix,
            text_encoding=text_encoding,
            text_errors=text_errors,
            do_vad=do_vad,
        )
        if new_data:
            convert_text = tts_mode and self.text_processor is not None
            if convert_text and show_progress:
                from tqdm import tqdm

                progress = tqdm(new_data, "converting texts")
            else:
                progress = new_data
            for data in progress:
                if convert_text:
                    data.text = self.text_processor(data.text)
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

    def _find_reference_to(self, target: AudioData):
        seq = torch.arange(0, len(self.data), 1).flatten().tolist()
        random.shuffle(seq)
        for i in seq:
            if target.can_be_reference_to_other(
                self.data[i],
                text_required=False,
                should_speaker_be_equal=self.mode == "style-tts",
                can_share_same_id=True,
            ):
                return self.data[i].wave
        if not self.make_references_optional:
            raise ValueError("Reference not found")
        return torch.randn(1, self.cfg.sample_rate * random.uniform(0.5, 2))

    @override
    def collate_fn(self, batch: Sequence[AudioData]):
        reference = None
        input_ids = None
        if "tts" in self.mode:
            input_ids = [self.encode_text(x.text) for x in batch]
            if self.mode == "style-tts":
                reference = [self._find_reference_to(x) for x in batch]
            wave = [x.wave for x in batch]
        elif self.mode == "vocoder":
            wave = [
                self.ap.random_segment(x.wave, chunk_size=self.chunk_size)
                for x in batch
            ]
        mel = [self.compute_mel(x) for x in wave]
        return CollateProcessor(
            wave=wave,
            mel=mel,
            compute_mel_fn=self.compute_mel,
            scheduler_q_sample_fn=self.scheduler.q_sample,
            input_ids=input_ids,
            reference=reference,
            device=self.device,
            pad_id=self.pad_token_id,
        )

    @override
    def get_dataloader(
        self,
        train_batch_size: int = 1,
        eval_batch_size: int = 1,
        train_shuffle: bool = True,
        eval_shuffle: bool = False,
        eval_ratio: float = 0.0,
        seed: Optional[int] = None,
        total_items: Optional[int] = None,
        num_workers: int = 0,
        **kwargs,
    ) -> Tuple[
        Iterable[CollateProcessor],
        Optional[Iterable[CollateProcessor]],
    ]:
        return super().get_dataloader(
            train_batch_size=train_batch_size,
            eval_batch_size=eval_batch_size,
            train_shuffle=train_shuffle,
            eval_shuffle=eval_shuffle,
            eval_ratio=eval_ratio,
            seed=seed,
            total_items=total_items,
            num_workers=num_workers,
            collate_fn=self.collate_fn,
        )
