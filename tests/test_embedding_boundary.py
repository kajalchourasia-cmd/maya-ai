from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from app.services.embeddings import OpenAICompatibleEmbeddingProvider, validated_embedding_vectors


def payload():
    return {'model':'example', 'data':[{'index':1, 'embedding':[0.2,0.4]},
                                     {'index':0, 'embedding':[0.1,0.3]}]}


def test_vectors_reordered_by_exact_index():
    assert validated_embedding_vectors(payload(),2,'example',2)==[[0.1,0.3],[0.2,0.4]]


@pytest.mark.parametrize('change', ['model','duplicate','missing','boolean_index','dimension','empty','zero','nan','infinite','boolean_value','string_value'])
def test_invalid_provider_vectors_rejected(change):
    obj=deepcopy(payload())
    if change=='model': obj['model']='different'
    elif change=='duplicate': obj['data'][0]['index']=0
    elif change=='missing': obj['data'].pop()
    elif change=='boolean_index': obj['data'][0]['index']=True
    elif change=='dimension': obj['data'][0]['embedding'].append(0.1)
    elif change=='empty': obj['data'][0]['embedding']=[]
    elif change=='zero': obj['data'][0]['embedding']=[0,0]
    else: obj['data'][0]['embedding'][0]={'nan':float('nan'),'infinite':float('inf'),'boolean_value':True,'string_value':'0.1'}[change]
    with pytest.raises(ValueError): validated_embedding_vectors(obj,2,'example',2)


def test_empty_inputs_make_no_call_and_blank_inputs_fail():
    provider=OpenAICompatibleEmbeddingProvider(name='test',base_url='https://example.invalid/embeddings',api_key='not-a-key',model='example')
    assert provider.embed([])==[]
    with pytest.raises(ValueError): provider.embed([' '])


def test_boundary_keeps_usage_and_request_id_not_credentials(monkeypatch):
    obj=payload()
    obj['usage']={'prompt_tokens':5,'total_tokens':5}
    class Response:
        status=200
        headers={'x-request-id':'test-request'}
        def __enter__(self): return self
        def __exit__(self,*args): return None
        def read(self,maximum): return json.dumps(obj).encode()
    captured=[]
    def fake_open(request,timeout):
        captured.append(json.loads(request.data))
        return Response()
    monkeypatch.setattr('app.services.embeddings.build_opener',lambda *args:SimpleNamespace(open=fake_open))
    provider=OpenAICompatibleEmbeddingProvider(name='test',base_url='https://example.invalid/embeddings',api_key='never-log',model='example',dimensions=2)
    assert len(provider.embed(['one','two']))==2
    assert captured[0]['dimensions']==2 and captured[0]['encoding_format']=='float'
    assert provider.last_response_metadata['usage']['prompt_tokens']==5
    assert provider.last_response_metadata['request_id']=='test-request'
    assert 'never-log' not in json.dumps(provider.last_response_metadata)
