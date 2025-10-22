import math
import random
from copy import deepcopy

import numpy as np
import pytest
import torch
from tokenizers import Tokenizer, models
from transformers import AutoTokenizer, PreTrainedTokenizerFast

from ntloss import NTLoss, NTLossDotProduct, NumberLevelLoss
from ntloss.utils import is_number

TOKENIZER = AutoTokenizer.from_pretrained("t5-small")
VOCAB_SIZE = TOKENIZER.vocab_size


def get_device(use_cpu: bool = False) -> str:
    """Get available device.

    Returns:
        Device
    """
    if not use_cpu:
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
            return "mps"
    return "cpu"


DEVICE = get_device()


def make_logits(token_logit_value_dicts):
    """
    Build a (1 x T x V) tensor filled with -inf,
    then set the logits specified in token_logit_value_dicts.
    """
    seq_len = len(token_logit_value_dicts)
    logits = torch.full((1, seq_len, VOCAB_SIZE), -np.inf, dtype=torch.float32)
    for i, tok_dict in enumerate(token_logit_value_dicts):
        for tok_id, logit in tok_dict.items():
            logits[0, i, tok_id] = logit
    return logits.to(device=DEVICE)


def dirac_logits(ids, peak_id, peak_value, vocab_size=VOCAB_SIZE):
    """Perfectly confident distribution (all mass on one token)."""
    logits = torch.full((1, 1, vocab_size), -1e6, dtype=torch.float32)
    logits[0, 0, peak_id] = 0.0
    return logits.to(device=DEVICE)


def gaussian_logits(ids, peak_id, peak_value, vocab_size=VOCAB_SIZE, sigma=1e-1):
    """
    Smooth bell curve over the reference tokens.
    """
    logits = torch.full((1, 1, vocab_size), -1e6, dtype=torch.float32)
    # Assumes that ids are ordered by their numerical value
    for idx, tok_id in enumerate(ids):
        logits[0, 0, tok_id] = -1 * np.abs((idx - peak_value) ** 2 / (2 * sigma**2))
    return logits.to(device=DEVICE)


@pytest.mark.parametrize("loss_class", [NTLoss, NTLossDotProduct])
@pytest.mark.parametrize(
    "logits_dicts,label_tokens",
    [
        # positive logits scenario
        (
            [
                {"1": 1.0, "2": 1.2, "0": 0.5, "3": 1.5},
                {"1": 1.5, "2": 1.2, "0": 0.5, "3": 1.5},
                {"1": 1.0, "2": 1.2, "0": 0.5, "3": 1.5},
            ],
            ["1", "1", "a"],
        ),
        # mixed logits scenario
        (
            [
                {"0": -4.0, "1": 2.0, "2": -1.0},
                {"0": 1.5, "1": 0.5, "2": 1.2},
                {"3": -2.0, "4": 1.0, "5": -2.5},
            ],
            ["2", "1", "3"],
        ),
    ],
)
@pytest.mark.parametrize("reduction", ["mean", "sum", "none"])
@pytest.mark.parametrize("loss_weight", [1, 0, 0.5, None])
def test_ntloss_variants(
    loss_class, logits_dicts, label_tokens, reduction, loss_weight
):
    # convert token strings to IDs
    token_logit_value_dicts = {
        # map token strings to token IDs upfront
        i: {
            TOKENIZER.convert_tokens_to_ids(tok): val
            for tok, val in logits_dicts[i].items()
        }
        for i in range(len(logits_dicts))
    }
    # build logits tensor
    # reorder into a list for our helper
    logits_list = [token_logit_value_dicts[i] for i in range(len(logits_dicts))]
    logits = make_logits(logits_list)

    # build labels tensor shape (1 x T)
    label_ids = [TOKENIZER.convert_tokens_to_ids(tok) for tok in label_tokens]
    labels = torch.tensor([label_ids], dtype=torch.long, device=logits.device)

    # set up loss weights
    if loss_weight is None:
        loss_weights = None
    else:
        loss_weights = torch.ones_like(labels) * loss_weight

    # instantiate and run
    loss_fn = loss_class(tokenizer=TOKENIZER)
    loss = loss_fn(logits, labels, reduction=reduction, loss_weights=loss_weights)

    assert torch.is_floating_point(loss), "Loss should be a floating tensor"
    if reduction != "none":
        assert isinstance(loss.item(), float), "Loss should be a Python float"
        assert not math.isnan(loss), "Loss must not be NaN"
        assert loss.item() > 0 or loss_weights.sum() == 0, "Loss must be positive"
    else:
        assert loss.shape == labels.shape, (
            "Loss and labels must have same shape if reduction is none"
        )
        assert isinstance(loss.sum().item(), float), "Loss should be a Python float"
        assert not math.isnan(loss.sum()), "Loss must not be NaN"
        assert loss.sum().item() > 0 or loss_weights.sum() == 0, "Loss must be positive"


@pytest.mark.parametrize("loss_class", [NTLoss, NTLossDotProduct])
@pytest.mark.parametrize("reweigh", [True, False])
def test_differentiability(loss_class, reweigh):
    loss_fn = loss_class(TOKENIZER, reweigh=reweigh)

    ref_tokens = [str(i) for i in range(10)] + ["A"]
    ref_ids = [TOKENIZER.convert_tokens_to_ids(t) for t in ref_tokens]

    gt_token_id = ref_ids[1]
    p_token_id = ref_ids[5]
    labels = torch.tensor([[gt_token_id]], dtype=torch.long)

    logits = torch.full(
        (1, 1, VOCAB_SIZE), -1e6, dtype=torch.float32, requires_grad=True
    )
    logits_ = torch.full((1, 1, VOCAB_SIZE), 0.0, dtype=torch.float32)
    logits_[:, :, p_token_id] = 1e6
    logits = logits + logits_

    loss = loss_fn(logits, labels)

    assert loss.grad_fn is not None, "Loss is not differentiable!"


@pytest.mark.parametrize("loss_class", [NTLoss, NTLossDotProduct])
@pytest.mark.parametrize("logit_builder", [dirac_logits, gaussian_logits])
def test_correct_minimum(loss_class, logit_builder):
    loss_fn = loss_class(TOKENIZER, reweigh=True)
    ref_tokens = [str(i) for i in range(10)] + ["A"]
    ref_ids = [TOKENIZER.convert_tokens_to_ids(t) for t in ref_tokens]

    # Guard: make sure all required tokens exist in the vocab
    assert all(i is not None and i >= 0 for i in ref_ids), "Missing token id"

    losses = torch.zeros(len(ref_ids), len(ref_ids), dtype=torch.float32)
    for i, (gt_token, gt_token_id) in enumerate(zip(ref_tokens, ref_ids)):
        labels = torch.tensor([[gt_token_id]], dtype=torch.long)
        for peak_idx, peak_id in enumerate(ref_ids):
            logits = logit_builder(ref_ids, peak_id, peak_idx)
            loss = loss_fn(logits, labels.to(device=logits.device))

            losses[i, peak_idx] = loss.item()

            if isinstance(loss_fn, NTLossDotProduct):
                yhat, nt_mass = loss_fn.predict_numbers(logits)
                assert 0 <= nt_mass <= 1
                assert 0 <= yhat <= 9

        # TODO: Ensure that if GT is number and mass is on text, loss is at least as
        # high as for worst number prediction. This is not there yet and the reason
        # why we exclude the last token
        mins = torch.argsort(losses[i, :-1], dim=0)
        expected = torch.Tensor(
            sorted(range(10), key=lambda j: (abs(j - i), j)),
        ).long()

        if i == 10:
            assert torch.allclose(
                losses[i, :], torch.zeros_like(losses[i, :]), atol=1e-8
            ), "Loss should be zero when the ground-truth token is non-numeric."
        else:
            assert torch.equal(mins, expected), (
                "For a digit ground truth, loss must be minimal when the distribution "
                "peaks over the same digit."
            )

    assert not torch.isnan(losses).any(), "Encountered NaN in loss matrix"


@pytest.mark.parametrize(
    "custom_vocab_li",
    [
        None,
        random.shuffle(list((range(0, 10, 2)))),
        random.shuffle(list(range(0, 10, 2)) + [100]),
        random.shuffle(list(range(0, 100, 10))),
    ],
)
@pytest.mark.parametrize("loss_class", [NTLoss])
@pytest.mark.parametrize("logit_builder", [dirac_logits, gaussian_logits])
@pytest.mark.parametrize("squash_factor", [0.5, 1, 2, 20])
def test_setup_distance_lookup(
    custom_vocab_li, loss_class, logit_builder, squash_factor
):
    # Make sure mapping of order of NTs in vocab is maintained for dist_matrix
    # Make sure that the distance matrix doesn't make assumptions about order of NTs

    if custom_vocab_li is not None:
        nums_in_vocab = custom_vocab_li
        custom_vocab = dict(
            [(str(n), i) for i, n in enumerate(random.shuffle(list((range(0, 10, 2)))))]
        )
        if "A" not in custom_vocab:
            custom_vocab["A"] = len(custom_vocab)
        tok = Tokenizer(models.WordLevel(vocab=custom_vocab))
        tokenizer = PreTrainedTokenizerFast(tokenizer_object=tok)
    else:
        nums_in_vocab = list(range(10))
        tokenizer = TOKENIZER

    loss_fn = loss_class(tokenizer, digit_level=False)

    num_vals = loss_fn.number_values_dense

    assert loss_fn.dist_lookup.shape[0] == loss_fn.dist_lookup.shape[1], (
        "The distance lookup matrix should be square."
    )
    assert loss_fn.dist_lookup.shape[0] == len(num_vals), (
        "The distance lookup matrix should contain distances for all number tokens "
        "in vocab."
    )

    # Check whether value at (i,j) in matrix is the expected value: the absolute
    # difference between num_vals[i] and num_vals[j]
    for i, i_val in enumerate(num_vals):
        for j, j_val in enumerate(num_vals):
            assert loss_fn.dist_lookup[i, j] == abs(i_val - j_val), (
                f"Value in cell {i}, {j} of the distance lookup matrix is not the "
                f"expected value ({loss_fn.dist_lookup[i, j]} vs {abs(i_val - j_val)})."
            )

    ref_tokens = [str(i) for i in nums_in_vocab]
    ref_ids = [TOKENIZER.convert_tokens_to_ids(t) for t in ref_tokens]

    # Check whether all num_ids have a mapping from idx in vocab to idx in dist lookup
    num_ids = torch.where(loss_fn.vocab_to_dist_idx != -1)[0]
    for i in ref_ids:
        assert i in num_ids, f"Couldn't find {i} in vocab_to_dist_idx mapping."

    # Check whether mapping from vocab to the index in dist lookup matrix is correct
    for i, ref_idx in enumerate(ref_ids):
        dist_idx = loss_fn.vocab_to_dist_idx[ref_idx]

        for j, j_val in enumerate(num_vals):
            i_val = float(ref_tokens[i])
            assert loss_fn.dist_lookup[dist_idx, j] == abs(i_val - j_val), (
                f"Value in cell {dist_idx}, {j} of the distance lookup matrix is not the "
                f"expected value ({loss_fn.dist_lookup[dist_idx, j]} vs {abs(i_val - j_val)})."
            )


@pytest.mark.parametrize("loss_class", [NTLoss])
@pytest.mark.parametrize("logit_builder", [dirac_logits, gaussian_logits])
@pytest.mark.parametrize("squash_factor", [0.5, 1, 2, 20])
def test_correct_squashing(loss_class, logit_builder, squash_factor):
    # Make sure wrong uses of the squashing factor are caught
    if squash_factor <= 1:
        with pytest.raises(
            AssertionError,
            match=r"The squash factor can't be equal to or smaller than 1*",
        ):
            loss_fn = loss_class(TOKENIZER, squash_factor=squash_factor)

        return

    loss_fn = loss_class(TOKENIZER, squash_factor=squash_factor, reweigh=False)
    ref_tokens = [str(i) for i in range(10)] + ["A"]
    ref_ids = [TOKENIZER.convert_tokens_to_ids(t) for t in ref_tokens]

    # Guard: make sure all required tokens exist in the vocab
    assert all(i is not None and i >= 0 for i in ref_ids), "Missing token id"

    # Make sure that the maximum distance in loss' distance matrix is larger than
    # nonzero minimum, with a factor equal to the squash_factor used
    inf = torch.finfo(loss_fn.dist_lookup.dtype).max
    lookup_nz = loss_fn.dist_lookup.masked_fill(loss_fn.dist_lookup == 0, inf)
    min_lookup_nz = lookup_nz.min()
    max_lookup = loss_fn.dist_lookup.max()

    computed = torch.div(max_lookup, min_lookup_nz)
    expected = torch.tensor([squash_factor], dtype=loss_fn.dist_lookup.dtype)
    assert torch.allclose(computed, expected, atol=1e-8), (
        "Distance to farthest number token should be the defined squashing factor larger ",
        f"than the distance to the closest number token ({computed} instead of {expected}).",
    )

    # Also make sure that the number token loss is thus always smaller or equal to the squashing factor
    losses = torch.zeros(len(ref_ids), len(ref_ids), dtype=torch.float32)
    for i, (gt_token, gt_token_id) in enumerate(zip(ref_tokens, ref_ids)):
        labels = torch.tensor([[gt_token_id]], dtype=torch.long)
        for peak_idx, peak_id in enumerate(ref_ids):
            logits = logit_builder(ref_ids, peak_id, peak_idx)
            loss = loss_fn(logits, labels.to(device=logits.device))
            losses[i, peak_idx] = loss.item()

    assert not torch.isnan(losses).any(), "Encountered NaN in loss matrix"

    assert torch.all(losses <= squash_factor), (
        "Loss should be smaller or equal to the squashing factor, if this is set."
    )


@pytest.mark.parametrize(
    "custom_vocab",
    [
        None,
        dict([(str(n), i) for i, n in enumerate(range(0, 10, 2))]),
        dict([(str(n), i) for i, n in enumerate(list(range(0, 10, 2)) + [100])]),
        dict([(str(n), i) for i, n in enumerate(range(0, 100, 10))]),
    ],
)
@pytest.mark.parametrize("loss_class", [NTLoss])
@pytest.mark.parametrize("logit_builder", [dirac_logits, gaussian_logits])
@pytest.mark.parametrize("squash_factor", [None, 0.5, 1, 2, 20])
def test_irregular_nt_vocab(custom_vocab, loss_class, logit_builder, squash_factor):
    if custom_vocab is not None:
        if "A" not in custom_vocab:
            custom_vocab["A"] = len(custom_vocab)
        tok = Tokenizer(models.WordLevel(vocab=custom_vocab))
        tokenizer = PreTrainedTokenizerFast(tokenizer_object=tok)
    else:
        tokenizer = TOKENIZER
    vocab_size = tokenizer.vocab_size

    # Make sure wrong uses of the squashing factor are caught
    if squash_factor is not None and squash_factor <= 1:
        with pytest.raises(
            AssertionError,
            match=r"The squash factor can't be equal to or smaller than 1*",
        ):
            loss_fn = loss_class(
                tokenizer,
                digit_level=False,
                squash_factor=squash_factor,
            )

        return

    loss_fn = loss_class(
        tokenizer,
        digit_level=False,
        squash_factor=squash_factor,
        reweigh=False,
    )
    ref_tokens = [str(i) for i in range(10)] + ["A"]
    ref_ids = [tokenizer.convert_tokens_to_ids(t) for t in ref_tokens]

    # Remove tokens not present in vocab from ref_tokens and ref_ids lists
    ref_tokens = [tok for i, tok in enumerate(ref_tokens) if ref_ids[i] is not None]
    ref_ids = [i for i in ref_ids if i is not None]

    # Make sure that the maximum distance in loss' distance matrix is larger than
    # nonzero minimum, with a factor equal to the squash_factor used
    inf = torch.finfo(loss_fn.dist_lookup.dtype).max
    lookup_nz = loss_fn.dist_lookup.masked_fill(loss_fn.dist_lookup == 0, inf)
    min_lookup_nz = lookup_nz.min()
    max_lookup = loss_fn.dist_lookup.max()

    computed = torch.div(max_lookup, min_lookup_nz)

    if custom_vocab is not None:
        max_nt = max([float(t) for t in custom_vocab.keys() if is_number(t)])
        min_nt = min(
            [float(t) for t in custom_vocab.keys() if is_number(t) and float(t) > 0]
        )
        factor = squash_factor or max_nt / min_nt
        expected = torch.tensor([factor], dtype=loss_fn.dist_lookup.dtype)
        assert torch.allclose(computed, expected, atol=1e-8), (
            "Distance to farthest number token should be the defined squashing factor larger ",
            f"than the distance to the closest number token ({computed} instead of {expected}).",
        )

    # Also make sure that the number token loss is thus always smaller or equal to the squashing factor
    losses = torch.zeros(len(ref_ids), len(ref_ids), dtype=torch.float32)
    for i, (gt_token, gt_token_id) in enumerate(zip(ref_tokens, ref_ids)):
        labels = torch.tensor([[gt_token_id]], dtype=torch.long)
        for peak_idx, peak_id in enumerate(ref_ids):
            logits = logit_builder(ref_ids, peak_id, peak_idx, vocab_size)
            loss = loss_fn(logits, labels.to(device=logits.device))
            losses[i, peak_idx] = loss.item()

    assert not torch.isnan(losses).any(), "Encountered NaN in loss matrix"
    if squash_factor is not None:
        assert torch.all(losses <= squash_factor), (
            "Loss should be smaller or equal to the squashing factor, if this is set."
        )


@pytest.mark.parametrize("loss_class", [NTLoss, NTLossDotProduct])
@pytest.mark.parametrize("logit_builder", [dirac_logits, gaussian_logits])
def test_logit_scaling(loss_class, logit_builder):
    loss_fn = loss_class(TOKENIZER, reweigh=True)
    ref_tokens = [str(i) for i in range(10)] + ["A"]
    ref_ids = [TOKENIZER.convert_tokens_to_ids(t) for t in ref_tokens]

    # Make sure max_dist is set up correctly for regularization
    assert loss_fn.max_dist > 0, "loss_fn.max_dist is not set up correctly"

    # Guard: make sure all required tokens exist in the vocab
    assert all(i is not None and i >= 0 for i in ref_ids), "Missing token id"

    losses = torch.zeros(len(ref_ids), len(ref_ids), dtype=torch.float32)
    for i, (gt_token, gt_token_id) in enumerate(zip(ref_tokens, ref_ids)):
        labels = torch.tensor([[gt_token_id]], dtype=torch.long)
        for peak_idx, peak_id in enumerate(ref_ids):
            logits = logit_builder(ref_ids, peak_id, peak_idx)
            loss = loss_fn(logits, labels.to(device=logits.device))
            losses[i, peak_idx] = loss.item()

        # Ensure that if GT is number and mass is on text, loss is at least as
        # high as for worst number prediction: should be the case for weighted NT loss.
        mins = torch.argsort(losses[i, :], dim=0)
        expected = torch.Tensor(
            sorted(range(10), key=lambda j: (abs(j - i), j)) + [10],
        ).long()

        if i == 10:
            assert torch.allclose(
                losses[i, :], torch.zeros_like(losses[i, :]), atol=1e-8
            ), "Loss should be zero when the ground-truth token is non-numeric."
        else:
            assert torch.equal(mins, expected), (
                "For a digit ground truth, loss must be minimal when the distribution "
                "peaks over the same digit."
            )
            assert torch.all(losses[i, expected[-2]] <= losses[i, -1]), (
                "For a digit ground truth and mass concentration on text, weighted loss "
                "should be at least as high as for worst number prediction."
            )

    assert not torch.isnan(losses).any(), "Encountered NaN in loss matrix"


def test_digit_level():
    # Ensure that 10 Number tokens are extracted if digit_level is set to True
    NEW_TOKENIZER = deepcopy(TOKENIZER)
    loss_class = NTLoss(tokenizer=NEW_TOKENIZER, digit_level=True)
    assert len(loss_class.number_values_dense) == 10

    # Add some tokens that are in right range but should still be ignored
    NEW_TOKENIZER.add_tokens([" 2"])
    loss_class = NTLoss(tokenizer=NEW_TOKENIZER, digit_level=True)
    assert len(loss_class.number_values_dense) == 10


def test_number_level_ntl():
    seq_tokens = ["A", "1", "2", "3", "B", "4", "5"]
    label_ids = TOKENIZER.convert_tokens_to_ids(seq_tokens)
    assert all(x is not None and x >= 0 for x in label_ids), "Missing token id"
    labels = torch.tensor([label_ids], dtype=torch.long)

    def one_hot_pos(tok_id, logit=50.0):
        return {tok_id: logit}

    # Perfect prediction: put all mass on the correct digit at each digit position.
    logits_dicts_perfect = []
    for tok in seq_tokens:
        tid = TOKENIZER.convert_tokens_to_ids(tok)
        # for non-digits, it doesn't matter; keep mass on that token to be safe
        logits_dicts_perfect.append(one_hot_pos(tid, 50.0))
    logits_perfect = make_logits(logits_dicts_perfect)
    labels = labels.to(device=logits_perfect.device)

    loss_fn = NumberLevelLoss(TOKENIZER, reweigh=False)
    loss = loss_fn(logits_perfect, labels, reduction="none")
    assert loss.shape == labels.shape
    assert loss.sum().item() == 0

    # Sanity: perfect case should be exactly zero for mean/sum as well
    loss = loss_fn(logits_perfect, labels, reduction="mean")
    assert loss.sum().item() == 0
    loss = loss_fn(logits_perfect, labels, reduction="sum")
    assert loss.sum().item() == 0

    # Now make a single digit wrong: change the middle digit "2" -> predict "9" instead.
    wrong_logits_dicts = [d.copy() for d in logits_dicts_perfect]
    wrong_logits_dicts[2] = {TOKENIZER.convert_tokens_to_ids("9"): 50.0}
    logits_middle_wrong = make_logits(wrong_logits_dicts)

    loss_middle = loss_fn(logits_middle_wrong, labels, reduction="none").squeeze()
    # Check that loss for that item is nonzero
    assert loss_middle[1].item() > 0
    # All others should have zero loss
    assert loss_middle[0].item() == 0 and loss_middle[2:].sum() == 0

    # Now make the first digit wrong and check whether error is higher
    wrong_logits_dicts = [d.copy() for d in logits_dicts_perfect]
    wrong_logits_dicts[1] = {TOKENIZER.convert_tokens_to_ids("9"): 50.0}
    logits_first_wrong = make_logits(wrong_logits_dicts)

    loss_first = loss_fn(logits_first_wrong, labels, reduction="none").squeeze()
    assert loss_first[1].item() > 0
    assert loss_first[0].item() == 0 and loss_first[2:].sum() == 0
    assert loss_first[1].item() > loss_middle[1].item()

    # Now make the third digit wrong and check whether error is lower
    wrong_logits_dicts = [d.copy() for d in logits_dicts_perfect]
    wrong_logits_dicts[3] = {TOKENIZER.convert_tokens_to_ids("5"): 50.0}
    logits_last_wrong = make_logits(wrong_logits_dicts)

    loss_last = loss_fn(logits_last_wrong, labels, reduction="none").squeeze()
    assert loss_last[1].item() > 0
    assert loss_last[0].item() == 0 and loss_last[2:].sum() == 0
    assert loss_last[1].item() < loss_middle[1].item()

    # If we aggregate, this must still hold
    for reduction in ["mean", "sum"]:
        loss_middle = loss_fn(
            logits_middle_wrong, labels, reduction=reduction
        ).squeeze()
        loss_last = loss_fn(logits_last_wrong, labels, reduction=reduction).squeeze()
        loss_first = loss_fn(logits_first_wrong, labels, reduction=reduction).squeeze()

        assert loss_middle.item() > 0.0
        assert loss_last.item() > 0.0
        assert loss_first.item() > 0.0
        assert loss_first.item() > loss_middle.item() > loss_last.item()


@pytest.mark.parametrize("reweigh", [True, False])
def test_number_level_ntl_scientific_notation(reweigh: bool):
    seq_tokens = ["A", "6", ".", "5", "1", "E", "+", "0", "2"]
    label_ids = TOKENIZER.convert_tokens_to_ids(seq_tokens)
    assert all(x is not None and x >= 0 for x in label_ids), "Missing token id"
    labels = torch.tensor([label_ids], dtype=torch.long)

    def one_hot_pos(tok_id, logit=50.0):
        return {tok_id: logit}

    # Perfect prediction: put all mass on the correct digit at each digit position.
    logits_dicts_perfect = []
    for tok in seq_tokens:
        tid = TOKENIZER.convert_tokens_to_ids(tok)
        # for non-digits, it doesn't matter; keep mass on that token to be safe
        logits_dicts_perfect.append(one_hot_pos(tid, 50.0))
    logits_perfect = make_logits(logits_dicts_perfect)
    logits_perfect.requires_grad = True
    labels = labels.to(device=logits_perfect.device)

    loss_fn = NumberLevelLoss(TOKENIZER, reweigh=reweigh, float_level=True)
    loss = loss_fn(logits_perfect, labels, reduction="none")
    assert loss.shape == labels.shape
    assert loss.sum().item() == 0
    assert loss.grad_fn is not None, "Loss is not differentiable!"

    # Sanity: perfect case should be exactly zero for mean/sum as well
    loss = loss_fn(logits_perfect, labels, reduction="mean")
    assert loss.sum().item() == 0
    loss = loss_fn(logits_perfect, labels, reduction="sum")
    assert loss.sum().item() == 0

    # Now make a single digit in 6.51 wrong: change the middle digit "5" -> predict "4" instead.
    wrong_logits_dicts = [d.copy() for d in logits_dicts_perfect]
    wrong_logits_dicts[3] = {TOKENIZER.convert_tokens_to_ids("6"): 50.0}
    logits_middle_wrong = make_logits(wrong_logits_dicts)

    loss_middle = loss_fn(logits_middle_wrong, labels, reduction="none").squeeze()
    # Check that loss for that item is nonzero
    assert loss_middle[1].item() > 0
    # All others should have zero loss
    assert loss_middle[0].item() == 0 and loss_middle[2:].sum() == 0

    # Now make the first digit wrong and check whether error is higher
    wrong_logits_dicts = [d.copy() for d in logits_dicts_perfect]
    wrong_logits_dicts[1] = {TOKENIZER.convert_tokens_to_ids("7"): 50.0}
    logits_first_wrong = make_logits(wrong_logits_dicts)

    loss_first = loss_fn(logits_first_wrong, labels, reduction="none").squeeze()
    assert loss_first[1].item() > 0
    assert loss_first[0].item() == 0 and loss_first[2:].sum() == 0
    assert loss_first[1].item() > loss_middle[1].item()

    # Now make the third digit wrong and check whether error is lower
    wrong_logits_dicts = [d.copy() for d in logits_dicts_perfect]
    wrong_logits_dicts[4] = {TOKENIZER.convert_tokens_to_ids("2"): 50.0}
    logits_last_wrong = make_logits(wrong_logits_dicts)

    loss_last = loss_fn(logits_last_wrong, labels, reduction="none").squeeze()
    assert loss_last[1].item() > 0
    assert loss_last[0].item() == 0 and loss_last[2:].sum() == 0
    assert loss_last[1].item() < loss_middle[1].item()

    # Test loss weights
    loss_weights = torch.rand_like(labels, dtype=logits_last_wrong.dtype)
    loss_with_weights = loss_fn(
        logits_last_wrong, labels, loss_weights=loss_weights, reduction="none"
    ).squeeze()
    assert loss_with_weights[1].item() > 0
    assert loss_with_weights[0].item() == 0 and loss_with_weights[2:].sum() == 0
    assert loss_with_weights[1].item() < loss_last[1].item()

    # If we aggregate, this must still hold
    for reduction in ["mean", "sum"]:
        loss_middle = loss_fn(
            logits_middle_wrong, labels, reduction=reduction
        ).squeeze()
        loss_last = loss_fn(logits_last_wrong, labels, reduction=reduction).squeeze()
        loss_first = loss_fn(logits_first_wrong, labels, reduction=reduction).squeeze()

        assert loss_middle.item() > 0.0
        assert loss_last.item() > 0.0
        assert loss_first.item() > 0.0
        assert loss_first.item() > loss_middle.item() > loss_last.item()

@pytest.mark.parametrize("loss_class", [NTLoss, NTLossDotProduct, NumberLevelLoss])
def test_vocab_size_handling(loss_class):
    """Tests the vocab_size handling logic"""
    larger_vocab_size = VOCAB_SIZE + 100
    labels = torch.tensor([[TOKENIZER.convert_tokens_to_ids("3")]], device=DEVICE)

    # Case 1: Mismatch, vocab_size not provided
    logits_large = torch.randn(1, 1, larger_vocab_size, device=DEVICE)
    loss_fn_no_size = loss_class(tokenizer=TOKENIZER)

    with pytest.raises(ValueError, match="The current `vocab_size`"):
        loss_fn_no_size(logits_large, labels)

    # Case 2: Mismatch, incorrect vocab_size provided
    wrong_vocab_size = larger_vocab_size + 50
    loss_fn_wrong_size = loss_class(tokenizer=TOKENIZER, vocab_size=wrong_vocab_size)

    with pytest.raises(ValueError, match="The current `vocab_size`"):
        loss_fn_wrong_size(logits_large, labels)

    # Case 3: Success, correct vocab_size provided
    loss_fn_correct_size = loss_class(tokenizer=TOKENIZER, vocab_size=larger_vocab_size)
    try:
        loss = loss_fn_correct_size(logits_large, labels)
        assert torch.is_tensor(loss)
        assert not torch.isnan(loss)
    except Exception as e:
        pytest.fail(f"Loss calculation failed unexpectedly with correct vocab_size: {e}")

    # Case 4: Sanity check, matching sizes (original behavior)
    logits_normal = torch.randn(1, 1, VOCAB_SIZE, device=DEVICE)
    try:
        loss = loss_fn_no_size(logits_normal, labels)
        assert torch.is_tensor(loss)
    except Exception as e:
        pytest.fail(f"Loss calculation failed with matching vocab sizes: {e}")
