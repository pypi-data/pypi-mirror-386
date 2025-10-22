"""Basic tests for chatan package."""

import pandas as pd
from unittest.mock import Mock, patch
from chatan import dataset, generator, sample


def test_basic_sampling():
    """Test basic sampling functionality."""
    schema = {
        "id": sample.uuid(),
        "category": sample.choice(["A", "B", "C"]),
        "score": sample.range(0, 100),
        "weighted": sample.weighted({"high": 0.7, "low": 0.3})
    }
    
    ds = dataset(schema, n=10)
    df = ds.generate()
    
    assert len(df) == 10
    assert all(col in df.columns for col in ["id", "category", "score", "weighted"])
    assert all(df["category"].isin(["A", "B", "C"]))
    assert all(0 <= score <= 100 for score in df["score"])


@patch('openai.OpenAI')
def test_generator_integration(mock_openai):
    """Test generator integration."""
    # Mock OpenAI response
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Generated response"
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client
    
    gen = generator("openai", "fake-key")
    
    schema = {
        "task": sample.choice(["task1", "task2"]),
        "prompt": gen("Write a prompt for {task}"),
    }
    
    ds = dataset(schema, n=2)
    df = ds.generate()
    
    assert len(df) == 2
    assert all(df["prompt"] == "Generated response")
    assert mock_client.chat.completions.create.call_count == 2


def test_dependency_resolution():
    """Test that column dependencies are resolved correctly."""
    schema = {
        "a": sample.choice([1, 2, 3]),
        "b": lambda ctx: ctx["a"] * 2,
        "c": lambda ctx: ctx["a"] + ctx["b"]
    }
    
    ds = dataset(schema, n=5)
    df = ds.generate()
    
    assert len(df) == 5
    for _, row in df.iterrows():
        assert row["b"] == row["a"] * 2
        assert row["c"] == row["a"] + row["b"]


def test_dataset_export():
    """Test dataset export functionality."""
    schema = {
        "id": sample.uuid(),
        "value": sample.range(1, 10)
    }
    
    ds = dataset(schema, n=3)
    df = ds.to_pandas()
    hf_ds = ds.to_huggingface()
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert len(hf_ds) == 3
