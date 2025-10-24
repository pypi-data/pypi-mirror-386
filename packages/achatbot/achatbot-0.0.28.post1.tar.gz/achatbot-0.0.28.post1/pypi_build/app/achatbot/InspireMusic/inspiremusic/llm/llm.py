# Copyright (c) 2024 Alibaba Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Dict, Optional, Callable, List, Generator
import torch
from torch import nn
from torch.nn.utils.rnn import pad_sequence, unpad_sequence
from inspiremusic.utils.common import IGNORE_ID
from inspiremusic.transformer.label_smoothing_loss import LabelSmoothingLoss
from inspiremusic.utils.common import th_accuracy, DTYPES
from torch import Tensor
from math import log
from einops import rearrange, reduce, repeat
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SinusoidalEmbedding(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def forward(self, x: Tensor) -> Tensor:
        device, half_dim = x.device, self.dim // 2
        emb = torch.tensor(log(10000) / (half_dim - 1), device=device)
        emb = torch.exp(torch.arange(half_dim, device=device) * -emb)
        emb = rearrange(x, "i -> i 1") * rearrange(emb, "j -> 1 j")
        return torch.cat((emb.sin(), emb.cos()), dim=-1).to(torch.float16)

class LLM(torch.nn.Module):
    def __init__(
            self,
            text_encoder_input_size: int,
            llm_input_size: int,
            llm_output_size: int,
            audio_token_size: int,
            llm: torch.nn.Module,
            sampling: Callable,
            text_encoder_conf: Dict = None,
            length_normalized_loss: bool = True,
            lsm_weight: float = 0.0,
            frozen_input_embed: bool = False,
            dtype: str = "fp16",
            **kwargs,
    ):
        super().__init__()
        self.dtype = DTYPES.get(dtype, torch.float32)
        self.llm_input_size = llm_input_size
        self.audio_token_size = audio_token_size
        # 1. build text token inputs related modules

        if llm is None:
            self.text_embedding = torch.nn.Embedding(text_token_size, text_encoder_input_size)
        else:
            self.text_embedding = llm.model.model.embed_tokens
            if frozen_input_embed:
                print("Freezing input embedding layer")
                for p in self.text_embedding.parameters():
                    p.requires_grad = False
        self.chorus_embedding = torch.nn.Embedding(5, llm_input_size)  # intro, chorus, verse1, verse2 , outro

        self.text_encoder_conf = text_encoder_conf
        self.text_encoder = self.build_encoder(text_encoder_conf)
        self.infer_cfg_ratio = kwargs.get("infer_cfg_ratio", None)
        logging.info(f"infer_cfg_ratio: {self.infer_cfg_ratio}")
        self.train_cfg_ratio = kwargs.get("train_cfg_ratio", None)
        logging.info(f"train_cfg_ratio: {self.train_cfg_ratio}")
        # 2. build audio token language model related modules
        self.sos_eos = 0
        self.task_id = 1

        self.llm_embedding = torch.nn.Embedding(2, llm_input_size)
        self.llm = llm
        self.llm_decoder = nn.Linear(llm_output_size, audio_token_size + 1)
        self.criterion_ce = LabelSmoothingLoss(
                size=audio_token_size + 1,
                padding_idx=IGNORE_ID,
                smoothing=lsm_weight,
                normalize_length=length_normalized_loss,
        )

        # 3. [Optional] build audio token related modules
        self.speech_embedding = torch.nn.Embedding(audio_token_size, llm_input_size)
        self.spk_embed_affine_layer = torch.nn.Linear(192, llm_input_size)
        self.num_codebooks = 4
        # 4. sampling method
        self.sampling = sampling
        self.time_embedding = SinusoidalEmbedding(llm_input_size)

    def cfg_dropout(self, text_token, text_token_len, p):
        # Classifier-Free Guidance Dropout
        B = text_token.size(0)
        num_samples_to_mask = int(p * B)
        if num_samples_to_mask == 0:
            num_samples_to_mask = 1
        indices_to_mask = torch.randperm(B, device=text_token.device)[:num_samples_to_mask]
        text_token[indices_to_mask] = 0
        text_token_len[indices_to_mask] = 0

        return text_token, text_token_len

    def build_encoder(self, encoder_conf=None):
        if encoder_conf is None:
            assert hasattr(self, "encoder_conf"), \
                "function param encoder_conf is None and model doesn't has encoder_conf attribute either."
            encoder_conf = self.encoder_conf

        encoder_name = encoder_conf.pop("name", "transformer")
        model = None
        if encoder_name == "transformer":
            from inspiremusic.transformer.conformer_encoder import ConformerEncoder
            model = ConformerEncoder(
                    **encoder_conf,
                    input_size=self.input_size,
                    use_cnn_module=False,
                    macaron_style=False,
            )
        elif encoder_name == "conformer":
            from inspiremusic.transformer.conformer_encoder import ConformerEncoder
            model = ConformerEncoder(
                    **encoder_conf,
                    input_size=self.input_size,
            )
        elif encoder_name == "llama_encoder":
            from inspiremusic.transformer.llama_encoder import LlamaEncoder
            model = LlamaEncoder(
                    **encoder_conf,
                    input_size=self.input_size,
            )
        elif "qwen" in encoder_name:
            from inspiremusic.transformer.qwen_encoder import QwenEncoder
            model = QwenEncoder(
                    **encoder_conf,
                    input_size=self.input_size,
            )

        encoder_conf["name"] = encoder_name

        return model

    def encode(self,
            text: torch.Tensor,
            text_lengths: torch.Tensor):
        if self.text_encoder is not None:
            encoder_out, encoder_mask = self.text_encoder(text, text_lengths,
                                                          decoding_chunk_size=1,
                                                          num_decoding_left_chunks=-1)
            encoder_out_lens = encoder_mask.squeeze(1).sum(1)
            encoder_out = self.text_encoder_affine_layer(encoder_out)
        else:
            encoder_out, encoder_out_lens = text, text_lengths
        return encoder_out, encoder_out_lens

    def pad_unpad_sequence(self, sos_eos_emb, embeddings, text_token,
                           text_token_len, task_id_emb, audio_token,
                           audio_token_len, seg_len):
        text_token = unpad_sequence(text_token, text_token_len.cpu(),
                                    batch_first=True)

        audio_token = unpad_sequence(audio_token, audio_token_len.cpu(),
                                     batch_first=True)

        for i in range(len(embeddings)):
            embeddings[i] = unpad_sequence(embeddings[i], seg_len.cpu(), batch_first=True)

        lm_input = [torch.concat([sos_eos_emb.squeeze(dim=0)] + [embedding[i] for embedding in embeddings] + [text_token[i], task_id_emb.squeeze(dim=0), audio_token[i]], dim=0) for i in range(len(text_token))]
        lm_input_len = torch.tensor([i.size(0) for i in lm_input], dtype=torch.int32)
        lm_input = pad_sequence(lm_input, batch_first=True, padding_value=IGNORE_ID)
        return lm_input, lm_input_len

    def forward(
            self,
            batch: dict,
            device: torch.device,
    ) -> Dict[str, Optional[torch.Tensor]]:
        """
        Args:
            text: (B, L, D)
            text_lengths: (B,)
            audio: (B, T, N) or (B, T)
            audio_lengths: (B,)
        """
        mask = True
        text_token = batch['text_token'].to(device)
        text_token_len = batch['text_token_len'].to(device)
        if "semantic_token" not in batch:
            audio_token = batch['acoustic_token'].to(device)
            audio_token_len = batch['acoustic_token_len'].to(device)
            audio_token = audio_token.view(audio_token.size(0), -1, self.num_codebooks)
            audio_token = audio_token[:, :, 0]
            audio_token_len = (audio_token_len / self.num_codebooks).long()

        else:
            audio_token = batch['semantic_token'].to(device)
            audio_token_len = batch['semantic_token_len'].to(device)

        time_start = batch['time_start'].to(device)
        time_end = batch['time_end'].to(device)
        chorus = batch['chorus'].to(device)
        # 1. encode text_token

        if self.train_cfg_ratio > 0:
            # Classifier-Free Guidance
            text_token, _ = self.cfg_dropout(text_token, text_token_len, self.train_cfg_ratio)

        # 2. Time Embedding & chorus embedding
        text_token = self.text_embedding(text_token)
        text_token, text_token_len = self.encode(text_token, text_token_len)
        if mask:
            time_mask = time_start != -1.0
            seg_len = time_mask.sum(-1)
            time_start = time_start.masked_fill(~time_mask, 0.0)
            time_end = time_end.masked_fill(~time_mask, 0.0)
            chorus = chorus.masked_fill(~time_mask, 0)
            time_start_embed = self.time_embedding(time_start.view(-1)).to(text_token.dtype)
            time_end_embed = self.time_embedding(time_end.view(-1)).to(text_token.dtype)
            time_start_embed = time_start_embed.view(chorus.size(0), chorus.size(1), -1)
            time_end_embed = time_end_embed.view(chorus.size(0), chorus.size(1), -1)
            chorus_embed = self.chorus_embedding(chorus)
            lm_target = [torch.tensor([IGNORE_ID] * (1 + 3 * seg_len[i] + text_token_len[i]) + audio_token[i,:audio_token_len[i]].tolist() + [self.audio_token_size]) for i in range(text_token.size(0))]
        else:
            time_start_embed = self.time_embedding(time_start).to(text_token.dtype)
            time_end_embed = self.time_embedding(time_end).to(text_token.dtype)
            chorus_embed = self.chorus_embedding(chorus)

            lm_target = [torch.tensor(
                [IGNORE_ID] * (4 + text_token_len[i]) + audio_token[i,:audio_token_len[i]].tolist() + [self.audio_token_size]) for i in range(text_token.size(0))]

        lm_target = pad_sequence(lm_target, batch_first=True, padding_value=IGNORE_ID).to(device)

        # 3. eos and task_id
        sos_eos_emb = self.llm_embedding.weight[self.sos_eos].reshape(1, 1, -1)
        task_id_emb = self.llm_embedding.weight[self.task_id].reshape(1, 1, -1)

        # 4. encode audio_token
        audio_token = self.speech_embedding(audio_token)

        # 5. unpad and pad
        lm_input, lm_input_len = self.pad_unpad_sequence(sos_eos_emb,
                                                         [time_start_embed,
                                                          time_end_embed,
                                                          chorus_embed],
                                                         text_token,
                                                         text_token_len,
                                                         task_id_emb,
                                                         audio_token,
                                                         audio_token_len,
                                                         seg_len)
        # 6. run lm forward
        lm_output, lm_output_mask = self.llm(lm_input.to(self.dtype), lm_input_len.to(device))
        logits = self.llm_decoder(lm_output)
        loss = self.criterion_ce(logits, lm_target)

        acc = th_accuracy(logits.view(-1, self.audio_token_size + 1), lm_target, ignore_label=IGNORE_ID)

        return {'loss': loss, 'acc': acc}

    def sampling_ids(
            self,
            weighted_scores: torch.Tensor,
            decoded_tokens: List,
            ignore_eos: bool = True,
    ):
        top_ids = self.sampling(weighted_scores, decoded_tokens)
        return top_ids

    @torch.inference_mode()
    def inference(
            self,
            text: torch.Tensor,
            text_len: torch.Tensor,
            audio_token: torch.Tensor,
            audio_token_len: torch.Tensor,
            prompt_text: torch.Tensor,
            prompt_text_len: torch.Tensor,
            prompt_audio_token: torch.Tensor,
            prompt_audio_token_len: torch.Tensor,
            embeddings: List,
            duration_to_gen: float = 30,
            task: str = "continuation",
            token_rate: int = 75,
            limit_audio_prompt_len: int = 5,
    ) -> Generator[torch.Tensor, None, None]:
        device = text.device

        if text is not None:
            text = torch.concat([prompt_text, text], dim=1)
            text_len += prompt_text_len
            infer_cfg = self.infer_cfg_ratio >= 0.0
            if infer_cfg:
                text_cfg = self.text_embedding(text.new_zeros(text.shape))
            text = self.text_embedding(text)

            # 1. encode text
            text, text_len = self.encode(text, text_len)

        # 2. encode embedding
        if embeddings is not None:
            time_start, time_end, chorus = embeddings

            if len(chorus.shape) == 1:
                time_start_embed = self.time_embedding(time_start).reshape(1, 1, -1)  # .half()
                time_end_embed = self.time_embedding(time_end).reshape(1, 1, -1)  # .half()
                chorus_embed = self.chorus_embedding(chorus).reshape(1, 1, -1)  # .half()
            else:
                time_start_embed = self.time_embedding(
                    time_start.view(-1)).reshape(1, chorus.size(1), -1)  # .half()
                time_end_embed = self.time_embedding(time_end.view(-1)).reshape(1, chorus.size(1), -1)  # .half()
                chorus_embed = self.chorus_embedding(chorus)  # .half()

        # 3. concat llm_input
        sos_eos_emb = self.llm_embedding.weight[self.sos_eos].reshape(1, 1, -1)
        task_id_emb = self.llm_embedding.weight[self.task_id].reshape(1, 1, -1)

        if audio_token_len:
            audio_token = audio_token[:, :(limit_audio_prompt_len * token_rate)]
            audio_token_emb = self.speech_embedding(audio_token)
        else:
            audio_token_emb = torch.zeros(1, 0, self.llm_input_size, dtype=text.dtype).to(device)

        if prompt_audio_token_len:
            prompt_audio_token_emb = self.speech_embedding(prompt_audio_token)
        else:
            prompt_audio_token_emb = torch.zeros(1, 0, self.llm_input_size, dtype=text.dtype).to(device)
        # Check if removing prompt audio token will fail decoding.

        if task == "continuation":
            lm_input = torch.concat(
                    [sos_eos_emb, time_start_embed, time_end_embed,
                     chorus_embed, text, task_id_emb, audio_token_emb], dim=1)

            if infer_cfg:
                audio_cfg = self.speech_embedding(
                    audio_token.new_zeros(audio_token.shape))
                lm_cf_input = torch.concat(
                        [sos_eos_emb, torch.rand_like(time_start_embed),
                         torch.rand_like(time_end_embed),
                         torch.rand_like(chorus_embed), text_cfg, task_id_emb,
                         audio_cfg], dim=1)
                lm_input = torch.cat([lm_input, lm_cf_input], 0)
        else:
            lm_input = torch.concat(
                    [sos_eos_emb, time_start_embed, time_end_embed,
                     chorus_embed, text, task_id_emb], dim=1)
            if infer_cfg:
                lm_cf_input = torch.concat(
                        [sos_eos_emb, torch.rand_like(time_start_embed),
                         torch.rand_like(time_end_embed),
                         torch.rand_like(chorus_embed), text_cfg, task_id_emb],
                        dim=1)
                lm_input = torch.cat([lm_input, lm_cf_input], 0)

        # 4. cal min/max_length
        min_len = int(0.9 * duration_to_gen * token_rate)
        max_len = duration_to_gen * token_rate

        # 5. step by step decode
        out_tokens = []
        offset = 0
        state = None

        for i in range(int(max_len)):
            y_pred, _, state = self.llm.forward_one_step(lm_input.to(self.dtype), torch.ones(lm_input.shape[0], lm_input.shape[1], device=lm_input.device).to(torch.bool), cache=state)
            logits = self.llm_decoder(y_pred[:, -1])
            if infer_cfg:
                # perform context free guidance
                logits_cf = logits[1]
                logits = logits[0]
                infer_cfg_ratio = self.infer_cfg_ratio
                logits = infer_cfg_ratio * logits + (1 - infer_cfg_ratio) * logits_cf

            logp = logits.log_softmax(dim=-1)
            logp = logp.squeeze(dim=0)

            if i < int(min_len):
                logp[self.audio_token_size] = torch.tensor(float('-inf'), dtype=self.dtype)

            top_ids = self.sampling_ids(logp, out_tokens, ignore_eos=i < min_len).item()

            if top_ids == self.audio_token_size:
                break

            # # in stream mode, yield token one by one

            yield torch.tensor([[top_ids]], dtype=torch.int64, device=device)
            out_tokens.append(top_ids)
            offset += lm_input.size(1)
            lm_input = self.speech_embedding.weight[top_ids].reshape(1, 1, -1)
            if infer_cfg:
                lm_input = lm_input.repeat(2, 1, 1)
