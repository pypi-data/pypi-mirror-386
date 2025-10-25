import torch

from snes.models.segmenter import ModernBERTSegmenter


class FakeOutputs:
    def __init__(self, last_hidden_state):
        self.last_hidden_state = last_hidden_state


class FakeEncoder(torch.nn.Module):
    def __init__(self, hidden_size=16):
        super().__init__()
        self.config = type("cfg", (), {"hidden_size": hidden_size})()

    def forward(self, input_ids=None, attention_mask=None):  # noqa: D401
        bsz, seqlen = input_ids.shape
        x = torch.zeros((bsz, seqlen, self.config.hidden_size))
        return FakeOutputs(x)


def test_forward_shape_without_hf_download(monkeypatch):
    # Instantiate model but replace encoder to avoid HF download
    m = ModernBERTSegmenter.__new__(ModernBERTSegmenter)  # bypass __init__
    Fake = FakeEncoder()
    m.encoder = Fake
    m.classifier = torch.nn.Linear(Fake.config.hidden_size, 1)
    m.model_name = "fake"

    input_ids = torch.ones((2, 8), dtype=torch.long)
    attention_mask = torch.ones_like(input_ids)
    logits = m(input_ids=input_ids, attention_mask=attention_mask)
    assert logits.shape == (2,)

