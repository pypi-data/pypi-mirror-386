import pytest

from mlflow_oidc_auth_groups_plugin_adfs import groups


def _function_clean_token_userinfo(token_userinfo):
    del(token_userinfo["azp"])
    del(token_userinfo["uid"])
    
    return token_userinfo


class TestGroups:
    def test_decode_token(self, fixture_data):
        decoded_token = groups.decode_and_validate_token(fixture_data.access_token)

        expect = fixture_data.decoded_token
        result = _function_clean_token_userinfo(decoded_token)

        assert result == expect
    

    def test_get_claim_groups(self, fixture_data):
        expect = fixture_data.token_groups
        result = groups.get_claim_groups(fixture_data.decoded_token)

        assert result == expect
    
    
    def test_get_user_groups(self, fixture_data):
        expect = fixture_data.groups_expect
        result = groups.get_user_groups(access_token=fixture_data.access_token)

        assert result == expect

  
class TestUtils:
    def test_normalise_list(self):
        raw_groups = "g_yc_da_research_mlflow_read"
        expect = [raw_groups]
        result = groups._normalize_list(raw_groups)
        assert result == expect

        expect = [""]
        result = groups._normalize_list("")
        assert result == expect

        raw_groups = ["g_yc_da_research_mlflow_read", "g_yc_da_research_mlflow_edit"]
        expect = raw_groups
        result = groups._normalize_list(raw_groups)
        assert result == expect

        raw_groups = ["g_yc_da_research_mlflow_read", ""]
        expect = raw_groups
        result = groups._normalize_list(raw_groups)
        assert result == expect
    
    def test_normalise_list__fail(self):
        raw_groups = None
        with pytest.raises(TypeError):
            groups._normalize_list(raw_groups)
        
        raw_groups = 1
        with pytest.raises(TypeError):
            groups._normalize_list(raw_groups)
    
    def test_normalise_list__return_only_str(self):
        expect = ["1", "2"]
        result = groups._normalize_list([1, 2])
        assert result == expect

        expect = ["1"]
        result = groups._normalize_list([1])
        assert result == expect