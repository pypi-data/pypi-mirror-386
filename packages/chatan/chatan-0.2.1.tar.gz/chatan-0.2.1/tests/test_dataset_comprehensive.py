"""Comprehensive tests for dataset module."""

import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import Mock
from datasets import Dataset as HFDataset

from chatan.dataset import Dataset, dataset
from chatan.generator import GeneratorFunction
from chatan.sampler import ChoiceSampler, UUIDSampler


class TestDatasetInitialization:
    """Test Dataset class initialization."""

    def test_init_with_dict_schema(self):
        """Test initialization with dictionary schema."""
        schema = {"col1": "static", "col2": ChoiceSampler(["A", "B"])}
        ds = Dataset(schema, n=50)
        
        assert ds.schema == schema
        assert ds.n == 50
        assert ds._data is None

    def test_init_with_string_schema(self):
        """Test initialization with string schema (not implemented)."""
        with pytest.raises(NotImplementedError):
            Dataset("create a QA dataset", n=100)

    def test_default_sample_count(self):
        """Test default sample count."""
        ds = Dataset({"col": "value"})
        assert ds.n == 100


class TestDependencyResolution:
    """Test dependency resolution and topological sorting."""

    def test_no_dependencies(self):
        """Test schema with no dependencies."""
        schema = {
            "col1": ChoiceSampler(["A", "B"]),
            "col2": UUIDSampler(),
            "col3": "static"
        }
        ds = Dataset(schema, n=5)
        
        dependencies = ds._build_dependency_graph()
        assert dependencies == {"col1": [], "col2": [], "col3": []}
        
        order = ds._topological_sort(dependencies)
        assert set(order) == {"col1", "col2", "col3"}

    def test_simple_dependency_chain(self):
        """Test simple dependency chain A -> B -> C."""
        mock_gen = Mock(spec=GeneratorFunction)
        mock_gen.prompt_template = "Generate based on {col1}"
        
        mock_gen2 = Mock(spec=GeneratorFunction)
        mock_gen2.prompt_template = "Generate based on {col2}"
        
        schema = {
            "col1": ChoiceSampler(["A", "B"]),
            "col2": mock_gen,
            "col3": mock_gen2
        }
        ds = Dataset(schema, n=5)
        
        dependencies = ds._build_dependency_graph()
        assert dependencies["col1"] == []
        assert dependencies["col2"] == ["col1"]
        assert dependencies["col3"] == ["col2"]
        
        order = ds._topological_sort(dependencies)
        assert order.index("col1") < order.index("col2")
        assert order.index("col2") < order.index("col3")

    def test_multiple_dependencies(self):
        """Test column with multiple dependencies."""
        mock_gen = Mock(spec=GeneratorFunction)
        mock_gen.prompt_template = "Combine {col1} and {col2}"
        
        schema = {
            "col1": ChoiceSampler(["A"]),
            "col2": ChoiceSampler(["B"]),
            "col3": mock_gen
        }
        ds = Dataset(schema, n=5)
        
        dependencies = ds._build_dependency_graph()
        assert dependencies["col3"] == ["col1", "col2"]
        
        order = ds._topological_sort(dependencies)
        col3_index = order.index("col3")
        assert order.index("col1") < col3_index
        assert order.index("col2") < col3_index

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        mock_gen1 = Mock(spec=GeneratorFunction)
        mock_gen1.prompt_template = "Based on {col2}"
        
        mock_gen2 = Mock(spec=GeneratorFunction)
        mock_gen2.prompt_template = "Based on {col1}"
        
        schema = {
            "col1": mock_gen1,
            "col2": mock_gen2
        }
        ds = Dataset(schema, n=5)
        
        dependencies = ds._build_dependency_graph()
        with pytest.raises(ValueError, match="Circular dependency"):
            ds._topological_sort(dependencies)

    def test_self_dependency_detection(self):
        """Test detection of self-referencing dependencies."""
        mock_gen = Mock(spec=GeneratorFunction)
        mock_gen.prompt_template = "Based on {col1} itself"
        
        schema = {"col1": mock_gen}
        ds = Dataset(schema, n=5)
        
        dependencies = ds._build_dependency_graph()
        with pytest.raises(ValueError, match="Circular dependency"):
            ds._topological_sort(dependencies)

    def test_dependency_outside_schema(self):
        """Test dependencies on columns not in schema are ignored."""
        mock_gen = Mock(spec=GeneratorFunction)
        mock_gen.prompt_template = "Based on {col1} and {external_col}"
        
        schema = {
            "col1": ChoiceSampler(["A"]),
            "col2": mock_gen
        }
        ds = Dataset(schema, n=5)
        
        dependencies = ds._build_dependency_graph()
        # external_col should be filtered out
        assert dependencies["col2"] == ["col1"]


class TestDataGeneration:
    """Test actual data generation."""

    def test_static_value_generation(self):
        """Test generation with static values."""
        schema = {
            "constant": "hello",
            "number": 42,
            "boolean": True
        }
        ds = Dataset(schema, n=3)
        df = ds.generate()
        
        assert len(df) == 3
        assert all(df["constant"] == "hello")
        assert all(df["number"] == 42)
        assert all(df["boolean"] == True)

    def test_sampler_generation(self):
        """Test generation with samplers."""
        schema = {
            "choice": ChoiceSampler(["A", "B", "C"]),
            "uuid": UUIDSampler()
        }
        ds = Dataset(schema, n=10)
        df = ds.generate()
        
        assert len(df) == 10
        assert all(df["choice"].isin(["A", "B", "C"]))
        
        # UUIDs should be unique
        assert len(df["uuid"].unique()) == 10

    def test_generator_function_with_context(self):
        """Test generation with GeneratorFunction."""
        mock_generator = Mock()
        mock_generator.generate.side_effect = lambda prompt: f"Generated: {prompt}"
        
        gen_func = GeneratorFunction(mock_generator, "Create content for {topic}")
        
        schema = {
            "topic": ChoiceSampler(["AI", "ML"]),
            "content": gen_func
        }
        ds = Dataset(schema, n=2)
        df = ds.generate()
        
        assert len(df) == 2
        assert all(df["content"].str.startswith("Generated: Create content for"))
        assert mock_generator.generate.call_count == 2

    def test_lambda_function_generation(self):
        """Test generation with lambda functions."""
        schema = {
            "base": ChoiceSampler([1, 2, 3]),
            "doubled": lambda ctx: ctx["base"] * 2,
            "sum": lambda ctx: ctx["base"] + ctx["doubled"]
        }
        ds = Dataset(schema, n=5)
        df = ds.generate()
        
        assert len(df) == 5
        for _, row in df.iterrows():
            assert row["doubled"] == row["base"] * 2
            assert row["sum"] == row["base"] + row["doubled"]

    def test_complex_dependency_chain(self):
        """Test complex dependency resolution."""
        schema = {
            "a": ChoiceSampler([1, 2]),
            "b": lambda ctx: ctx["a"] * 10,
            "c": ChoiceSampler([100, 200]),
            "d": lambda ctx: ctx["b"] + ctx["c"],
            "e": lambda ctx: ctx["a"] + ctx["d"]
        }
        ds = Dataset(schema, n=5)
        df = ds.generate()
        
        assert len(df) == 5
        for _, row in df.iterrows():
            assert row["b"] == row["a"] * 10
            assert row["d"] == row["b"] + row["c"]
            assert row["e"] == row["a"] + row["d"]

    def test_override_sample_count(self):
        """Test overriding sample count in generate()."""
        schema = {"col": ChoiceSampler(["A"])}
        ds = Dataset(schema, n=10)
        
        df = ds.generate(n=5)
        assert len(df) == 5
        
        # Original n should be unchanged
        assert ds.n == 10

    def test_multiple_generate_calls(self):
        """Test multiple calls to generate()."""
        schema = {"col": UUIDSampler()}
        ds = Dataset(schema, n=3)
        
        df1 = ds.generate()
        df2 = ds.generate()
        
        # Should generate different data each time
        assert len(df1) == 3
        assert len(df2) == 3
        assert not df1["col"].equals(df2["col"])


class TestDatasetExport:
    """Test dataset export functionality."""

    def test_to_pandas(self):
        """Test conversion to pandas DataFrame."""
        schema = {"col": ChoiceSampler(["A", "B"])}
        ds = Dataset(schema, n=5)
        
        df = ds.to_pandas()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5

    def test_to_pandas_without_prior_generation(self):
        """Test to_pandas generates data if needed."""
        schema = {"col": ChoiceSampler(["A", "B"])}
        ds = Dataset(schema, n=5)
        
        assert ds._data is None
        df = ds.to_pandas()
        assert ds._data is not None
        assert len(df) == 5

    def test_to_huggingface(self):
        """Test conversion to HuggingFace Dataset."""
        schema = {"col": ChoiceSampler(["A", "B"])}
        ds = Dataset(schema, n=5)
        
        hf_ds = ds.to_huggingface()
        assert isinstance(hf_ds, HFDataset)
        assert len(hf_ds) == 5

    def test_save_parquet(self):
        """Test saving to parquet format."""
        schema = {"col": ChoiceSampler(["A", "B"])}
        ds = Dataset(schema, n=5)
        
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            try:
                ds.save(f.name, format="parquet")
                assert os.path.exists(f.name)
                
                # Read back and verify
                df_loaded = pd.read_parquet(f.name)
                assert len(df_loaded) == 5
                assert "col" in df_loaded.columns
            finally:
                os.unlink(f.name)

    def test_save_csv(self):
        """Test saving to CSV format."""
        schema = {"col": ChoiceSampler(["A", "B"])}
        ds = Dataset(schema, n=5)
        
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode='w') as f:
            try:
                ds.save(f.name, format="csv")
                assert os.path.exists(f.name)
                
                # Read back and verify
                df_loaded = pd.read_csv(f.name)
                assert len(df_loaded) == 5
                assert "col" in df_loaded.columns
            finally:
                os.unlink(f.name)

    def test_save_json(self):
        """Test saving to JSON format."""
        schema = {"col": ChoiceSampler(["A", "B"])}
        ds = Dataset(schema, n=5)
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
            try:
                ds.save(f.name, format="json")
                assert os.path.exists(f.name)
                
                # Read back and verify
                df_loaded = pd.read_json(f.name)
                assert len(df_loaded) == 5
                assert "col" in df_loaded.columns
            finally:
                os.unlink(f.name)

    def test_save_unsupported_format(self):
        """Test error handling for unsupported formats."""
        schema = {"col": ChoiceSampler(["A"])}
        ds = Dataset(schema, n=5)
        
        with pytest.raises(ValueError, match="Unsupported format: xml"):
            ds.save("test.xml", format="xml")

    def test_save_without_prior_generation(self):
        """Test save generates data if needed."""
        schema = {"col": ChoiceSampler(["A"])}
        ds = Dataset(schema, n=5)
        
        assert ds._data is None
        
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            try:
                ds.save(f.name)
                assert ds._data is not None
                assert os.path.exists(f.name)
            finally:
                os.unlink(f.name)


class TestDatasetFactory:
    """Test dataset factory function."""

    def test_factory_creates_dataset(self):
        """Test factory function creates Dataset instance."""
        schema = {"col": "value"}
        ds = dataset(schema, n=50)
        
        assert isinstance(ds, Dataset)
        assert ds.schema == schema
        assert ds.n == 50

    def test_factory_default_count(self):
        """Test factory function with default count."""
        schema = {"col": "value"}
        ds = dataset(schema)
        
        assert ds.n == 100


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_callable_context_error(self):
        """Test error handling when callable fails."""
        def failing_func(ctx):
            raise ValueError("Function failed")
        
        schema = {
            "base": ChoiceSampler([1]),
            "fail": failing_func
        }
        ds = Dataset(schema, n=1)
        
        with pytest.raises(ValueError, match="Function failed"):
            ds.generate()

    def test_generator_function_context_error(self):
        """Test error handling when GeneratorFunction fails."""
        mock_generator = Mock()
        mock_generator.generate.side_effect = Exception("Generation failed")
        
        gen_func = GeneratorFunction(mock_generator, "Template")
        
        schema = {"content": gen_func}
        ds = Dataset(schema, n=1)
        
        with pytest.raises(Exception, match="Generation failed"):
            ds.generate()

    def test_missing_context_variable(self):
        """Test error when context variable is missing."""
        mock_generator = Mock()
        gen_func = GeneratorFunction(mock_generator, "Template {missing}")
        
        schema = {
            "base": ChoiceSampler([1]),
            "content": gen_func
        }
        ds = Dataset(schema, n=1)
        
        with pytest.raises(KeyError):
            ds.generate()


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_realistic_qa_dataset(self):
        """Test realistic QA dataset generation."""
        mock_generator = Mock()
        mock_generator.generate.side_effect = [
            "What is machine learning?",
            "Machine learning is a subset of AI...",
            "Explain neural networks",
            "Neural networks are computational models..."
        ]
        
        gen_func_q = GeneratorFunction(mock_generator, "Generate a question about {topic}")
        gen_func_a = GeneratorFunction(mock_generator, "Answer: {question}")
        
        schema = {
            "id": UUIDSampler(),
            "topic": ChoiceSampler(["ML", "AI", "DL"]),
            "question": gen_func_q,
            "answer": gen_func_a
        }
        
        ds = Dataset(schema, n=2)
        df = ds.generate()
        
        assert len(df) == 2
        assert all(df["topic"].isin(["ML", "AI", "DL"]))
        assert len(df["id"].unique()) == 2  # Unique IDs
        assert mock_generator.generate.call_count == 4  # 2 questions + 2 answers

    def test_augmentation_pattern(self):
        """Test data augmentation pattern."""
        # Simulate existing dataset
        existing_data = pd.DataFrame({
            "original": ["Text 1", "Text 2", "Text 3"]
        })
        
        mock_generator = Mock()
        mock_generator.generate.side_effect = [
            "Variation of Text 1",
            "Variation of Text 2", 
            "Variation of Text 3"
        ]
        
        from chatan.sampler import DatasetSampler
        gen_func = GeneratorFunction(mock_generator, "Create variation: {original}")
        
        schema = {
            "original": DatasetSampler(existing_data, "original"),
            "variation": gen_func
        }
        
        ds = Dataset(schema, n=3)
        df = ds.generate()
        
        assert len(df) == 3
        assert all(df["original"].isin(["Text 1", "Text 2", "Text 3"]))
        assert all(df["variation"].str.startswith("Variation of"))

    def test_data_mix_pattern(self):
        """Test data mix generation pattern."""
        mock_generator = Mock()
        mock_generator.generate.side_effect = [
            "Implementation prompt",
            "Implementation response",
            "Explanation prompt", 
            "Explanation response"
        ]
        
        gen_prompt = GeneratorFunction(mock_generator, "Generate {task_type} prompt")
        gen_response = GeneratorFunction(mock_generator, "Respond to: {prompt}")
        
        schema = {
            "task_type": ChoiceSampler(["implementation", "explanation"]),
            "prompt": gen_prompt,
            "response": gen_response
        }
        
        ds = Dataset(schema, n=2)
        df = ds.generate()
        
        assert len(df) == 2
        assert all(df["task_type"].isin(["implementation", "explanation"]))
        assert mock_generator.generate.call_count == 4
