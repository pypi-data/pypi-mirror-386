__all__ = ["AudioData", "CollateProcessor"]
from lt_utils.common import *
import torch
from torch import Tensor, LongTensor
from torch.nn import functional as F
from lt_tensor.masking_utils import length_to_mask


class AudioData:
    text: Optional[str] = None

    def __init__(
        self,
        wave: Tensor,
        duration: float,
        audio_path: str,
        sample_rate: float,
        speaker_id: str,
        speech_id: int = -1,
        text_path: Optional[str] = None,
        text: Optional[str] = None,
    ):
        self.wave = wave
        self.wave_length = wave.size(-1)
        self.duration = duration
        self.sample_rate = sample_rate
        self.audio_path = audio_path
        self.text_path = text_path
        self.speaker_id = speaker_id
        self.speech_id = max(int(speech_id), -1)
        if text:
            self.text = text
        if text_path:
            self.text_file = Path(text_path).name

    def get_duration(self):
        return self.wave.size(-1) / self.sample_rate

    def get_duration_as_tensor(self):
        return torch.as_tensor(self.get_duration())

    def _cbrt_check_text(
        self,
        text: Optional[str],
        text_required: bool = False,
        should_be_equal: Optional[bool] = None,
    ):
        if self.text is None or text is None:
            return not text_required

        if should_be_equal is None:
            # we dont check
            return True

        if should_be_equal:
            return text == self.text

        return text != self.text

    def can_be_reference_to(
        self,
        speaker_id: str,
        speech_id: int = -1,
        text: Optional[str] = None,
        text_required: bool = False,
        should_text_be_equal: Optional[bool] = None,
        should_speaker_be_equal: Optional[bool] = None,
        can_share_same_id: bool = False,
    ):
        """Used to get the same speaker or different speaker to train voice changers or TTS that uses voice-cloning features."""
        are_speakers_equal = speaker_id == self.speaker_id

        if should_speaker_be_equal is not None:
            if should_speaker_be_equal:
                if not are_speakers_equal:
                    return False
            else:
                if are_speakers_equal:
                    return False

        if not self._cbrt_check_text(text, text_required, should_text_be_equal):
            return False

        if not are_speakers_equal:
            # no reason to investigate further in this case.
            return True

        if can_share_same_id or self.speech_id == -1 or speech_id == -1:
            # case true we dont need to check.
            return True

        return speech_id != self.speaker_id

    def can_be_reference_to_other(
        self,
        other: "AudioData",
        text_required: bool = False,
        should_text_be_equal: Optional[bool] = None,
        should_speaker_be_equal: Optional[bool] = None,
        can_share_same_id: bool = False,
    ):
        return self.can_be_reference_to(
            other.speaker_id,
            other.speech_id,
            other.text,
            text_required,
            should_text_be_equal,
            should_speaker_be_equal,
            can_share_same_id,
        )


_COMP_Q_SAMPLE_TP: TypeAlias = Callable[
    [Tensor, Optional[Union[int, Tensor]]], Tuple[Tensor, Tensor, Tensor]
]


class CollateProcessor:
    largest_wave: int = 0
    largest_mel: int = 0
    largest_text: int = 0
    largest_reference: int = 0
    largest_reference_mel: int = 0
    reference_mels: Optional[List[Tensor]] = None
    device = torch.device("cpu")

    def __init__(
        self,
        wave: List[Tensor],
        mel: List[Tensor],
        pad_id: int,
        compute_mel_fn: Callable[[Tensor], Tensor],
        scheduler_q_sample_fn: _COMP_Q_SAMPLE_TP,
        input_ids: Optional[List[LongTensor]] = None,
        reference: Optional[List[Tensor]] = None,
        device: Optional[Union[str, torch.device]] = None,
    ):
        if device is not None:
            self.to(device)
        self.batch_size = len(wave)
        self.pad_id = pad_id
        self._wave = wave
        self._mel = mel
        self._input_ids = input_ids
        self.n_mels = mel[0].size(-2)

        self.compute_mel_fn: Callable[[Tensor], Tensor] = compute_mel_fn
        self.scheduler_q_sample_fn: _COMP_Q_SAMPLE_TP = scheduler_q_sample_fn
        if self._input_ids is not None:
            self.largest_text = max(self.lengths)
        self.largest_wave = int(self.durations_wave.max().item())
        self.largest_mel = int(self.durations.max().item())
        self.reference = reference

        if self.reference is not None:
            self.largest_reference = max([x.size(-1) for x in self.reference])
        # self.lengths = lengths

    def to(self, device: Union[str, torch.device]):
        if isinstance(device, torch.device):
            self.device = device
        else:
            self.device = torch.device(device)

    def _diffusion_step(
        self,
        target: Tensor,
        t: Optional[Union[int, Tensor]] = None,
        get_xt_mel: bool = False,
        get_eps_mel: bool = False,
    ):
        xt_mel = None
        eps_mel = None
        xt, eps, t = self.scheduler_q_sample_fn(target, t)
        if get_xt_mel:
            xt_mel = self.compute_mel_fn(xt)
        if get_eps_mel:
            eps_mel = self.compute_mel_fn(eps)
        return xt, eps, t, xt_mel, eps_mel

    def get_diffusion(
        self,
        t: Optional[Union[Tensor, int]] = None,
        get_xt_mel: bool = False,
        get_eps_mel: bool = False,
    ):
        l_xt: List[Tensor] = []
        l_eps: List[Tensor] = []
        l_t: List[Tensor] = []

        l_eps_mel: List[Tensor] = []
        l_xt_mel: List[Tensor] = []

        for wave in self._wave:
            xt, eps, _t, xt_mel, eps_mel = self._diffusion_step(
                target=wave,
                t=t,
                get_xt_mel=get_xt_mel,
                get_eps_mel=get_eps_mel,
            )
            pad = self.largest_wave - eps.size(-1)
            l_xt.append(F.pad(xt, (0, pad)).squeeze())
            l_t.append(_t)
            l_eps.append(F.pad(eps, (0, pad)).squeeze())

            if get_xt_mel:
                l_xt_mel.append(
                    F.pad(xt_mel, (0, self.largest_mel - xt_mel.size(-1))).squeeze()
                )

            if get_eps_mel:
                l_eps_mel.append(
                    F.pad(eps_mel, (0, self.largest_mel - eps_mel.size(-1))).squeeze()
                )

        # outputs
        xt_out = torch.stack(l_xt).view(self.batch_size, 1, -1).to(self.device)
        eps_out = torch.stack(l_eps).view_as(xt_out).to(self.device)
        t_out = torch.stack(l_t).view(self.batch_size, -1).to(self.device)

        xt_mel_out = None
        eps_mel_out = None
        if get_xt_mel:
            xt_mel_out = torch.stack(l_xt_mel).to(self.device)
        if get_eps_mel:
            eps_mel_out = torch.stack(l_eps_mel).to(self.device)
        return dict(
            xt=xt_out,
            eps=eps_out,
            t=t_out,
            xt_mel=xt_mel_out,
            eps_mel=eps_mel_out,
        )

    def get_diffusion_mel(self, t: Optional[Union[Tensor, int]] = None):
        """Similar to 'get_diffusion', but here we target the mel-spec instead"""
        l_xt: List[Tensor] = []
        l_eps: List[Tensor] = []
        l_t: List[Tensor] = []

        for mel in self._mel:
            xt, eps, _t = self.scheduler_q_sample_fn(mel, t)

            l_xt.append(F.pad(xt, (0, self.largest_mel - xt.size(-1))).squeeze())
            l_eps.append(F.pad(eps, (0, self.largest_mel - eps.size(-1))).squeeze())
            l_t.append(_t)

        # outputs
        xt_out = torch.stack(l_xt).to(self.device)
        eps_out = torch.stack(l_eps).to(self.device)
        t_out = torch.stack(l_t).view(self.batch_size, -1).to(self.device)

        return dict(
            xt=xt_out,
            eps=eps_out,
            t=t_out,
        )

    @property
    def wave(self):
        return (
            torch.stack(
                [
                    F.pad(x, (0, self.largest_wave - x.size(-1))).squeeze()
                    for x in self._wave
                ]
            )
            .view(self.batch_size, 1, -1)
            .to(self.device)
        )

    @property
    def mel(self):
        return (
            torch.stack(
                [
                    F.pad(x, (0, self.largest_mel - x.size(-1))).squeeze()
                    for x in self._mel
                ]
            )
            .view(self.batch_size, self.n_mels, -1)
            .to(self.device)
        )

    @property
    def durations(self):
        return torch.as_tensor(
            [x.size(-1) for x in self._mel],
            dtype=torch.float,
            device=self.device,
        )

    @property
    def durations_wave(self):
        return torch.as_tensor(
            [x.size(-1) for x in self._wave],
            dtype=torch.float,
            device=self.device,
        )

    @property
    def input_ids(self):
        if self._input_ids is None:
            return None
        return (
            torch.stack(
                [
                    F.pad(x, (0, self.largest_text - x.size(-1)), value=self.pad_id)
                    for x in self._input_ids
                ]
            )
            .view(self.batch_size, -1)
            .long()
            .to(self.device)
        )

    @property
    def lengths(self):
        # for lstm/rnn packing sequences, so its not a tensor
        # but a list with the non-padded sizes
        if self._input_ids is None:
            return None
        return [x.size(-1) for x in self._input_ids]

    def get_input_ids(self, get_lengths_mask: bool = True, get_input_mask: bool = True):
        if self._input_ids is None:
            return None

        lengths = self.lengths
        input_ids = self.input_ids
        mask = None
        lengths_mask = None
        if get_lengths_mask:
            lengths_mask = length_to_mask(lengths, 1).to(self.device)
        if get_input_mask:
            mask = input_ids.eq(self.pad_id)
        return dict(
            lengths=self.lengths,
            input_ids=self.input_ids,
            mask=mask,
            lengths_mask=lengths_mask,
        )

    def get_reference(self, tp: Literal["wave", "mel"] = "mel"):
        assert self.reference is not None, "Reference not available!"
        assert tp in ["wave", "mel"], f"Invalid type '{tp}'. Use either 'wave' or 'mel'"
        if tp == "wave":
            return torch.stack(
                [
                    F.pad(x, (0, self.largest_reference - x.size(-1))).squeeze()
                    for x in self.reference
                ],
                dim=0,
            ).to(self.device)

        if not self.reference_mels:
            self.reference_mels = [self.compute_mel_fn(x) for x in self.reference]
            self.largest_reference_mel = max([x.size(-1) for x in self.reference_mels])
        return torch.stack(
            [
                F.pad(x, (0, self.largest_reference_mel - x.size(-1))).squeeze()
                for x in self.reference_mels
            ],
            dim=0,
        ).to(self.device)
