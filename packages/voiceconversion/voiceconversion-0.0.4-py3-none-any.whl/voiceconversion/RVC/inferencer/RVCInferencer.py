import torch
import json
from voiceconversion.const import EnumInferenceTypes
from safetensors import safe_open
from voiceconversion.common.deviceManager.DeviceManager import DeviceManager
from voiceconversion.RVC.inferencer.Inferencer import Inferencer
from .rvc_models.infer_pack.models import SynthesizerTrnMs256NSFsid
from voiceconversion.common.SafetensorsUtils import load_model


class RVCInferencer(Inferencer):
    def load_model(self, file: str):
        device_manager = DeviceManager.get_instance()
        dev = device_manager.device
        is_half = device_manager.use_fp16()
        self.set_props(EnumInferenceTypes.pyTorchRVC, file)

        # Keep torch.load for backward compatibility, but discourage the use of this loading method
        if file.endswith('.safetensors'):
            with safe_open(file, 'pt', device=str(dev) if dev.type == 'cuda' else 'cpu') as cpt:
                config = json.loads(cpt.metadata()['config'])
                model = SynthesizerTrnMs256NSFsid(*config, is_half=is_half).to(dev)
                load_model(model, cpt, strict=False)
        else:
            cpt = torch.load(file, map_location=dev if dev.type == 'cuda' else 'cpu')
            model = SynthesizerTrnMs256NSFsid(*cpt["config"], is_half=is_half).to(dev)
            model.load_state_dict(cpt["weight"], strict=False)

        model.eval().remove_weight_norm()

        if is_half:
            model = model.half()

        self.model = model
        return self

    def infer(
        self,
        feats: torch.Tensor,
        pitch_length: torch.Tensor,
        pitch: torch.Tensor,
        pitchf: torch.Tensor,
        sid: torch.Tensor,
        skip_head: int,
        return_length: int,
        formant_length: int,
    ) -> torch.Tensor:
        assert pitch is not None or pitchf is not None, "Pitch or Pitchf is not found."

        res = self.model.infer(
            feats,
            pitch_length,
            pitch,
            pitchf,
            sid,
            skip_head=skip_head,
            return_length=return_length,
            formant_length=formant_length
        )
        res = res[0][0, 0]
        return torch.clip(res, -1.0, 1.0, out=res)
