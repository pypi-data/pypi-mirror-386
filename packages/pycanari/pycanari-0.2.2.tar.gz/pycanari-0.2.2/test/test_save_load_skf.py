from canari import Model, SKF
from canari.component import LocalTrend, LocalAcceleration, LstmNetwork, WhiteNoise
from test.test_save_load_model import compare_model_dict
import pytest


# SKF model
skf_lstm = SKF(
    norm_model=Model(
        LocalTrend(),
        LstmNetwork(look_back_len=10, num_layer=2, num_hidden_unit=10, smoother=False),
        WhiteNoise(),
    ),
    abnorm_model=Model(
        LocalAcceleration(),
        LstmNetwork(look_back_len=10, num_layer=2, num_hidden_unit=10, smoother=False),
        WhiteNoise(),
    ),
    std_transition_error=1e-4,
    norm_to_abnorm_prob=1e-4,
    abnorm_to_norm_prob=1e-1,
    norm_model_prior_prob=0.99,
)
skf_slstm = SKF(
    norm_model=Model(
        LocalTrend(),
        LstmNetwork(look_back_len=10, num_layer=2, num_hidden_unit=10, smoother=True),
        WhiteNoise(),
    ),
    abnorm_model=Model(
        LocalAcceleration(),
        LstmNetwork(look_back_len=10, num_layer=2, num_hidden_unit=10, smoother=True),
        WhiteNoise(),
    ),
    std_transition_error=1e-4,
    norm_to_abnorm_prob=1e-4,
    abnorm_to_norm_prob=1e-1,
    norm_model_prior_prob=0.99,
)


@pytest.mark.parametrize("skf_version", [skf_lstm, skf_slstm], ids=["LSTM", "SLSTM"])
def test_skf_save_load(skf_version):
    """Test save/load for SKF.py"""
    skf_dict = skf_version.get_dict()
    skf_loaded = SKF.load_dict(skf_dict)
    skf_loaded_dict = skf_loaded.get_dict()

    compare_model_dict(skf_dict["norm_model"], skf_loaded_dict["norm_model"])
    compare_model_dict(skf_dict["abnorm_model"], skf_loaded_dict["abnorm_model"])

    assert skf_dict["std_transition_error"] == skf_loaded_dict["std_transition_error"]
    assert skf_dict["norm_to_abnorm_prob"] == skf_loaded_dict["norm_to_abnorm_prob"]
    assert skf_dict["abnorm_to_norm_prob"] == skf_loaded_dict["abnorm_to_norm_prob"]
    assert skf_dict["norm_model_prior_prob"] == skf_loaded_dict["norm_model_prior_prob"]
