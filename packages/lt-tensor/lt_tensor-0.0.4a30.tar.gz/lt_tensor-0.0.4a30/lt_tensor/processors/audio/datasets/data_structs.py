__all__ = ["AudioData"]
from lt_utils.common import *
import torch
from torch import Tensor


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
