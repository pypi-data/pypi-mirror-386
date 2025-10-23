"""
Test CodeGenerationAgent - Production-Ready Code Generation Agent

Tests zero-config initialization, progressive configuration,
code generation features, language support, and quality metrics.

Written BEFORE implementation (TDD).
"""

import os

import pytest

# ============================================================================
# TEST CLASS 1: Initialization (REQUIRED - 8 tests)
# ============================================================================


class TestCodeGenerationAgentInitialization:
    """Test agent initialization patterns."""

    def test_zero_config_initialization(self):
        """Test agent works with zero configuration (most important test)."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        # Should work with no parameters
        agent = CodeGenerationAgent()

        assert agent is not None
        assert hasattr(agent, "codegen_config")
        assert hasattr(agent, "generate_code")

    def test_zero_config_uses_environment_variables(self):
        """Test that zero-config reads from environment variables."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        # Set environment variables
        os.environ["KAIZEN_LLM_PROVIDER"] = "anthropic"
        os.environ["KAIZEN_MODEL"] = "claude-3-sonnet"
        os.environ["KAIZEN_TEMPERATURE"] = "0.5"
        os.environ["KAIZEN_MAX_TOKENS"] = "2000"
        os.environ["KAIZEN_PROGRAMMING_LANGUAGE"] = "javascript"
        os.environ["KAIZEN_INCLUDE_TESTS"] = "false"
        os.environ["KAIZEN_INCLUDE_DOCUMENTATION"] = "false"

        try:
            agent = CodeGenerationAgent()

            # Should use environment values
            assert agent.codegen_config.llm_provider == "anthropic"
            assert agent.codegen_config.model == "claude-3-sonnet"
            assert agent.codegen_config.temperature == 0.5
            assert agent.codegen_config.max_tokens == 2000
            assert agent.codegen_config.programming_language == "javascript"
            assert agent.codegen_config.include_tests is False
            assert agent.codegen_config.include_documentation is False
        finally:
            # Clean up
            del os.environ["KAIZEN_LLM_PROVIDER"]
            del os.environ["KAIZEN_MODEL"]
            del os.environ["KAIZEN_TEMPERATURE"]
            del os.environ["KAIZEN_MAX_TOKENS"]
            del os.environ["KAIZEN_PROGRAMMING_LANGUAGE"]
            del os.environ["KAIZEN_INCLUDE_TESTS"]
            del os.environ["KAIZEN_INCLUDE_DOCUMENTATION"]

    def test_progressive_configuration_model_only(self):
        """Test progressive configuration - override model only."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(model="gpt-3.5-turbo")

        assert agent.codegen_config.model == "gpt-3.5-turbo"
        # Other values should be defaults
        assert agent.codegen_config.llm_provider == "openai"  # default

    def test_progressive_configuration_multiple_params(self):
        """Test progressive configuration - override multiple parameters."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(
            llm_provider="anthropic",
            model="claude-3-opus",
            temperature=0.1,
            max_tokens=3000,
            programming_language="typescript",
            include_tests=False,
            include_documentation=False,
        )

        assert agent.codegen_config.llm_provider == "anthropic"
        assert agent.codegen_config.model == "claude-3-opus"
        assert agent.codegen_config.temperature == 0.1
        assert agent.codegen_config.max_tokens == 3000
        assert agent.codegen_config.programming_language == "typescript"
        assert agent.codegen_config.include_tests is False
        assert agent.codegen_config.include_documentation is False

    def test_full_config_object_initialization(self):
        """Test initialization with full config object."""
        from kaizen.agents.specialized.code_generation import (
            CodeGenConfig,
            CodeGenerationAgent,
        )

        config = CodeGenConfig(
            llm_provider="openai",
            model="gpt-4-turbo",
            temperature=0.2,
            max_tokens=1800,
            timeout=60,
            programming_language="python",
            include_tests=True,
            include_documentation=True,
        )

        agent = CodeGenerationAgent(config=config)

        assert agent.codegen_config.llm_provider == "openai"
        assert agent.codegen_config.model == "gpt-4-turbo"
        assert agent.codegen_config.temperature == 0.2
        assert agent.codegen_config.max_tokens == 1800
        assert agent.codegen_config.timeout == 60
        assert agent.codegen_config.programming_language == "python"
        assert agent.codegen_config.include_tests is True
        assert agent.codegen_config.include_documentation is True

    def test_config_parameter_overrides_defaults(self):
        """Test that constructor parameters override config defaults."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        # Parameter should override default
        agent = CodeGenerationAgent(
            programming_language="javascript",
            include_tests=False,
            include_documentation=False,
        )

        assert agent.codegen_config.programming_language == "javascript"
        assert agent.codegen_config.include_tests is False
        assert agent.codegen_config.include_documentation is False

    def test_default_configuration_values(self):
        """Test that defaults are set correctly."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        # LLM defaults
        assert agent.codegen_config.llm_provider == "openai"
        assert agent.codegen_config.model == "gpt-4o-mini"  # Code-specific default
        assert agent.codegen_config.temperature == 0.2  # Lower for deterministic code
        assert agent.codegen_config.max_tokens == 2000

        # Code-specific defaults
        assert agent.codegen_config.programming_language == "python"
        assert agent.codegen_config.include_tests is True
        assert agent.codegen_config.include_documentation is True

        # Technical defaults
        assert agent.codegen_config.timeout == 30
        assert agent.codegen_config.retry_attempts == 3
        assert isinstance(agent.codegen_config.provider_config, dict)

    def test_timeout_merged_into_provider_config(self):
        """Test that timeout is merged into provider_config."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(timeout=60)

        # Timeout should be in provider_config
        assert "timeout" in agent.codegen_config.provider_config
        assert agent.codegen_config.provider_config["timeout"] == 60


# ============================================================================
# TEST CLASS 2: Execution (REQUIRED - 12 tests)
# ============================================================================


class TestCodeGenerationAgentExecution:
    """Test agent execution and code generation method."""

    def test_generate_code_method_exists(self):
        """Test that generate_code convenience method exists."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        assert hasattr(agent, "generate_code")
        assert callable(getattr(agent, "generate_code"))

    def test_generate_code_returns_dict(self):
        """Test that generate_code method returns a dictionary."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()
        result = agent.generate_code("Create a function to add two numbers")

        assert isinstance(result, dict)

    def test_generate_code_has_expected_output_fields(self):
        """Test that output contains expected signature fields."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        # Use mock provider for unit tests
        agent = CodeGenerationAgent(llm_provider="mock")
        result = agent.generate_code("Create a function to multiply two numbers")

        # Check for signature output fields
        assert "code" in result
        assert "explanation" in result
        assert "test_cases" in result
        assert "documentation" in result
        assert "confidence" in result

    def test_generate_code_accepts_task_description(self):
        """Test that generate_code method accepts task_description parameter."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        # Should accept task_description parameter
        result = agent.generate_code(task_description="Create a fibonacci function")

        assert result is not None
        assert isinstance(result, dict)

    def test_run_method_integration(self):
        """Test that agent.run() method works (inherited from BaseAgent)."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        # Direct call to BaseAgent.run()
        result = agent.run(
            task_description="Create a function to calculate factorial",
            language="python",
        )

        assert isinstance(result, dict)

    def test_execution_with_different_task_descriptions(self):
        """Test execution with various task descriptions."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(llm_provider="mock")

        # Test with different tasks
        test_cases = [
            "Create a function to reverse a string",
            "Implement binary search algorithm",
            "Generate a function to calculate prime numbers",
            "Create a class to manage a todo list",
        ]

        for task in test_cases:
            result = agent.generate_code(task)
            assert isinstance(result, dict)
            assert "code" in result
            assert "explanation" in result

    def test_language_parameter_override_works(self):
        """Test that language parameter can override default."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(llm_provider="mock", programming_language="python")

        # Override with JavaScript
        result = agent.generate_code(
            "Create a function to sort an array", language="javascript"
        )

        assert isinstance(result, dict)
        assert result.get("language") == "javascript"

    def test_quality_metrics_added(self):
        """Test that quality metrics are added to result."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(llm_provider="mock")
        result = agent.generate_code("Create a function to calculate sum")

        # Check for quality metrics
        assert "lines_of_code" in result
        assert "has_tests" in result
        assert "has_documentation" in result

    def test_language_metadata_added_to_result(self):
        """Test that language metadata is added to result."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(
            llm_provider="mock", programming_language="typescript"
        )
        result = agent.generate_code("Create a function to validate email")

        # Should have language metadata
        assert "language" in result
        assert result["language"] == "typescript"

    def test_test_cases_is_always_list(self):
        """Test that test_cases field is always a list."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(llm_provider="mock")
        result = agent.generate_code("Create a function to check palindrome")

        # test_cases should be a list
        assert "test_cases" in result
        assert isinstance(result["test_cases"], list)

    def test_execution_performance(self):
        """Test that execution completes in reasonable time."""
        import time

        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        start = time.time()
        result = agent.generate_code("Create a simple hello world function")
        duration = time.time() - start

        # Should complete in less than 30 seconds
        assert duration < 30
        assert result is not None

    def test_empty_input_handling(self):
        """Test handling of empty task description."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        # Should handle empty input gracefully
        result = agent.generate_code("")

        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "INVALID_INPUT"


# ============================================================================
# TEST CLASS 3: Configuration (REQUIRED - 8 tests)
# ============================================================================


class TestCodeGenerationAgentConfiguration:
    """Test configuration class and behavior."""

    def test_config_class_exists(self):
        """Test that configuration class exists."""
        from kaizen.agents.specialized.code_generation import CodeGenConfig

        assert CodeGenConfig is not None

    def test_config_is_dataclass(self):
        """Test that config uses dataclass decorator."""
        import dataclasses

        from kaizen.agents.specialized.code_generation import CodeGenConfig

        assert dataclasses.is_dataclass(CodeGenConfig)

    def test_config_has_required_llm_fields(self):
        """Test that config has required LLM fields."""
        from kaizen.agents.specialized.code_generation import CodeGenConfig

        config = CodeGenConfig()

        assert hasattr(config, "llm_provider")
        assert hasattr(config, "model")
        assert hasattr(config, "temperature")
        assert hasattr(config, "max_tokens")

    def test_config_has_required_technical_fields(self):
        """Test that config has required technical fields."""
        from kaizen.agents.specialized.code_generation import CodeGenConfig

        config = CodeGenConfig()

        assert hasattr(config, "timeout")
        assert hasattr(config, "retry_attempts")
        assert hasattr(config, "provider_config")

    def test_config_has_code_specific_fields(self):
        """Test that config has code-specific fields."""
        from kaizen.agents.specialized.code_generation import CodeGenConfig

        config = CodeGenConfig()

        assert hasattr(config, "programming_language")
        assert hasattr(config, "include_tests")
        assert hasattr(config, "include_documentation")

    def test_config_environment_variable_defaults(self):
        """Test that config reads from environment variables."""
        from kaizen.agents.specialized.code_generation import CodeGenConfig

        os.environ["KAIZEN_MODEL"] = "test-model"
        os.environ["KAIZEN_PROGRAMMING_LANGUAGE"] = "rust"
        os.environ["KAIZEN_INCLUDE_TESTS"] = "false"

        try:
            config = CodeGenConfig()
            assert config.model == "test-model"
            assert config.programming_language == "rust"
            assert config.include_tests is False
        finally:
            del os.environ["KAIZEN_MODEL"]
            del os.environ["KAIZEN_PROGRAMMING_LANGUAGE"]
            del os.environ["KAIZEN_INCLUDE_TESTS"]

    def test_config_can_be_instantiated_with_custom_values(self):
        """Test that config accepts custom values."""
        from kaizen.agents.specialized.code_generation import CodeGenConfig

        config = CodeGenConfig(
            llm_provider="custom_provider",
            model="custom_model",
            temperature=0.123,
            max_tokens=999,
            programming_language="go",
            include_tests=False,
            include_documentation=False,
        )

        assert config.llm_provider == "custom_provider"
        assert config.model == "custom_model"
        assert config.temperature == 0.123
        assert config.max_tokens == 999
        assert config.programming_language == "go"
        assert config.include_tests is False
        assert config.include_documentation is False

    def test_config_provider_config_is_dict(self):
        """Test that provider_config is initialized as dict."""
        from kaizen.agents.specialized.code_generation import CodeGenConfig

        config = CodeGenConfig()

        assert isinstance(config.provider_config, dict)

    def test_default_model_is_gpt_4o_mini(self):
        """Test that default model is gpt-4o-mini for better code quality."""
        from kaizen.agents.specialized.code_generation import CodeGenConfig

        config = CodeGenConfig()

        assert config.model == "gpt-4o-mini"


# ============================================================================
# TEST CLASS 4: Signature (REQUIRED - 5 tests)
# ============================================================================


class TestCodeGenerationAgentSignature:
    """Test signature definition and structure."""

    def test_signature_class_exists(self):
        """Test that signature class exists."""
        from kaizen.agents.specialized.code_generation import CodeGenSignature

        assert CodeGenSignature is not None

    def test_signature_inherits_from_base(self):
        """Test that signature inherits from Signature base class."""
        from kaizen.agents.specialized.code_generation import CodeGenSignature
        from kaizen.signatures import Signature

        assert issubclass(CodeGenSignature, Signature)

    def test_signature_has_input_fields(self):
        """Test that signature has defined input fields."""
        from kaizen.agents.specialized.code_generation import CodeGenSignature

        sig = CodeGenSignature()

        # Check for input fields
        assert hasattr(sig, "task_description")
        assert hasattr(sig, "language")

    def test_signature_has_output_fields(self):
        """Test that signature has defined output fields."""
        from kaizen.agents.specialized.code_generation import CodeGenSignature

        sig = CodeGenSignature()

        # Check for output fields
        assert hasattr(sig, "code")
        assert hasattr(sig, "explanation")
        assert hasattr(sig, "test_cases")
        assert hasattr(sig, "documentation")
        assert hasattr(sig, "confidence")

    def test_signature_has_docstring(self):
        """Test that signature has comprehensive docstring."""
        from kaizen.agents.specialized.code_generation import CodeGenSignature

        assert CodeGenSignature.__doc__ is not None
        assert len(CodeGenSignature.__doc__) > 20


# ============================================================================
# TEST CLASS 5: Error Handling (REQUIRED - 5 tests)
# ============================================================================


class TestCodeGenerationAgentErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_input_handling(self):
        """Test handling of empty task description."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        # Should handle empty input gracefully
        result = agent.generate_code("")

        assert isinstance(result, dict)
        # Should have error indicator
        assert "error" in result
        assert result["error"] == "INVALID_INPUT"

    def test_whitespace_only_input_handling(self):
        """Test handling of whitespace-only task description."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        # Should handle whitespace input gracefully
        result = agent.generate_code("   \t\n   ")

        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "INVALID_INPUT"

    def test_none_input_handling(self):
        """Test handling of None input."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        # Should handle None input gracefully
        try:
            result = agent.generate_code(None)
            # If it doesn't raise, check for error
            assert isinstance(result, dict)
            assert "error" in result
        except (TypeError, AttributeError):
            # Acceptable to raise error for None
            pass

    def test_invalid_language_handling(self):
        """Test handling of unsupported programming language."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        # Should still work with unsupported language (LLM decides)
        result = agent.generate_code(
            "Create a function", language="unknown_language_xyz"
        )

        assert isinstance(result, dict)
        # Should still generate something or handle gracefully

    def test_invalid_config_handling(self):
        """Test handling of invalid configuration values."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        # Test with invalid temperature (negative)
        try:
            agent = CodeGenerationAgent(temperature=-1.0)
            # If it doesn't raise, it should handle gracefully
            assert (
                agent.codegen_config.temperature >= -1.0
            )  # Stored but may not be used
        except ValueError:
            # Acceptable to raise ValueError for invalid config
            pass


# ============================================================================
# TEST CLASS 6: Documentation (REQUIRED - 4 tests)
# ============================================================================


class TestCodeGenerationAgentDocumentation:
    """Test docstrings and documentation completeness."""

    def test_agent_class_has_docstring(self):
        """Test that agent class has comprehensive docstring."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        assert CodeGenerationAgent.__doc__ is not None
        assert len(CodeGenerationAgent.__doc__) > 100

    def test_generate_code_method_has_docstring(self):
        """Test that generate_code method has docstring."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        assert CodeGenerationAgent.generate_code.__doc__ is not None
        assert len(CodeGenerationAgent.generate_code.__doc__) > 50

    def test_config_class_has_docstring(self):
        """Test that config class has docstring."""
        from kaizen.agents.specialized.code_generation import CodeGenConfig

        assert CodeGenConfig.__doc__ is not None

    def test_helper_methods_have_docstrings(self):
        """Test that helper methods have docstrings."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        # Check generate_tests method
        assert CodeGenerationAgent.generate_tests.__doc__ is not None

        # Check _build_code_gen_prompt method
        assert CodeGenerationAgent._build_code_gen_prompt.__doc__ is not None


# ============================================================================
# TEST CLASS 7: Type Hints (REQUIRED - 2 tests)
# ============================================================================


class TestCodeGenerationAgentTypeHints:
    """Test type hint completeness."""

    def test_generate_code_method_has_type_hints(self):
        """Test that generate_code method has type hints."""
        import inspect

        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        sig = inspect.signature(CodeGenerationAgent.generate_code)

        # Check return type hint
        assert sig.return_annotation != inspect.Parameter.empty

        # Check parameter type hints
        params_with_hints = 0
        total_params = 0

        for param_name, param in sig.parameters.items():
            if param_name != "self":
                total_params += 1
                if param.annotation != inspect.Parameter.empty:
                    params_with_hints += 1

        # At least 80% of parameters should have type hints
        if total_params > 0:
            hint_percentage = params_with_hints / total_params
            assert hint_percentage >= 0.8

    def test_init_method_has_type_hints(self):
        """Test that __init__ has type hints."""
        import inspect

        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        sig = inspect.signature(CodeGenerationAgent.__init__)

        # Check parameter type hints (most should have hints)
        params_with_hints = 0
        total_params = 0

        for param_name, param in sig.parameters.items():
            if param_name not in ["self", "kwargs"]:
                total_params += 1
                if param.annotation != inspect.Parameter.empty:
                    params_with_hints += 1

        # At least 80% of parameters should have type hints
        if total_params > 0:
            hint_percentage = params_with_hints / total_params
            assert hint_percentage >= 0.8


# ============================================================================
# TEST CLASS 8: Helper Methods (CODE-SPECIFIC - 6 tests)
# ============================================================================


class TestCodeGenerationAgentHelperMethods:
    """Test helper methods for code generation."""

    def test_generate_tests_method_exists(self):
        """Test that generate_tests helper method exists."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        assert hasattr(agent, "generate_tests")
        assert callable(agent.generate_tests)

    def test_generate_tests_returns_list(self):
        """Test that generate_tests returns a list."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()
        tests = agent.generate_tests("def add(a, b): return a + b", "python")

        assert isinstance(tests, list)

    def test_build_code_gen_prompt_method_exists(self):
        """Test that _build_code_gen_prompt helper method exists."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        assert hasattr(agent, "_build_code_gen_prompt")
        assert callable(agent._build_code_gen_prompt)

    def test_build_code_gen_prompt_returns_string(self):
        """Test that _build_code_gen_prompt returns a string."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()
        prompt = agent._build_code_gen_prompt("Create a function", "python")

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_build_code_gen_prompt_includes_language(self):
        """Test that _build_code_gen_prompt includes language."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()
        prompt = agent._build_code_gen_prompt("Create a function", "javascript")

        assert "javascript" in prompt.lower() or "JavaScript" in prompt

    def test_build_code_gen_prompt_includes_requirements(self):
        """Test that _build_code_gen_prompt includes requirements."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(include_tests=True, include_documentation=True)
        prompt = agent._build_code_gen_prompt("Create a function", "python")

        # Should mention tests and documentation
        assert "test" in prompt.lower() or "testing" in prompt.lower()
        assert "doc" in prompt.lower() or "comment" in prompt.lower()


# ============================================================================
# TEST CLASS 9: Quality Metrics (CODE-SPECIFIC - 4 tests)
# ============================================================================


class TestCodeGenerationAgentQualityMetrics:
    """Test quality metrics for generated code."""

    def test_lines_of_code_metric_added(self):
        """Test that lines_of_code metric is added."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(llm_provider="mock")
        result = agent.generate_code("Create a simple function")

        assert "lines_of_code" in result
        assert isinstance(result["lines_of_code"], int)

    def test_has_tests_metric_added(self):
        """Test that has_tests metric is added."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(llm_provider="mock", include_tests=True)
        result = agent.generate_code("Create a function to calculate average")

        assert "has_tests" in result
        assert isinstance(result["has_tests"], bool)

    def test_has_documentation_metric_added(self):
        """Test that has_documentation metric is added."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(llm_provider="mock", include_documentation=True)
        result = agent.generate_code("Create a function to find maximum")

        assert "has_documentation" in result
        assert isinstance(result["has_documentation"], bool)

    def test_language_metadata_added(self):
        """Test that language metadata is added."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(llm_provider="mock", programming_language="python")
        result = agent.generate_code("Create a function to sort a list")

        assert "language" in result
        assert result["language"] == "python"


# ============================================================================
# TEST CLASS 10: Language Support (CODE-SPECIFIC - 5 tests)
# ============================================================================


class TestCodeGenerationAgentLanguageSupport:
    """Test language support for code generation."""

    def test_python_code_generation(self):
        """Test code generation for Python."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(llm_provider="mock", programming_language="python")
        result = agent.generate_code("Create a function to reverse a string")

        assert isinstance(result, dict)
        assert result.get("language") == "python"

    def test_javascript_code_generation(self):
        """Test code generation for JavaScript."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(
            llm_provider="mock", programming_language="javascript"
        )
        result = agent.generate_code("Create a function to check even numbers")

        assert isinstance(result, dict)
        assert result.get("language") == "javascript"

    def test_typescript_code_generation(self):
        """Test code generation for TypeScript."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(
            llm_provider="mock", programming_language="typescript"
        )
        result = agent.generate_code("Create a typed function to sum an array")

        assert isinstance(result, dict)
        assert result.get("language") == "typescript"

    def test_language_override_works(self):
        """Test that language parameter can override config default."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent(llm_provider="mock", programming_language="python")

        # Override with TypeScript
        result = agent.generate_code(
            "Create a function to filter an array", language="typescript"
        )

        assert result.get("language") == "typescript"

    def test_default_language_is_python(self):
        """Test that default language is Python."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        assert agent.codegen_config.programming_language == "python"


# ============================================================================
# TEST CLASS 11: BaseAgent Integration (REQUIRED - 2 tests)
# ============================================================================


class TestCodeGenerationAgentBaseAgentIntegration:
    """Test integration with BaseAgent."""

    def test_agent_inherits_from_base_agent(self):
        """Test CodeGenerationAgent inherits from BaseAgent."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent
        from kaizen.core.base_agent import BaseAgent

        agent = CodeGenerationAgent()

        assert isinstance(agent, BaseAgent)

    def test_agent_uses_async_single_shot_strategy(self):
        """Test that agent uses MultiCycleStrategy by default."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent
        from kaizen.strategies.multi_cycle import MultiCycleStrategy

        agent = CodeGenerationAgent(llm_provider="mock")

        # Should use MultiCycleStrategy (default for BaseAgent)
        assert isinstance(agent.strategy, MultiCycleStrategy)


# ============================================================================
# TEST CLASS 12: Additional Helper Methods (CODE-SPECIFIC - 4 tests)
# ============================================================================


class TestCodeGenerationAgentAdditionalHelpers:
    """Test additional helper methods from the example."""

    def test_explain_code_method_exists(self):
        """Test that explain_code helper method exists."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        assert hasattr(agent, "explain_code")
        assert callable(agent.explain_code)

    def test_explain_code_returns_string(self):
        """Test that explain_code returns a string."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()
        explanation = agent.explain_code("def add(a, b): return a + b", "python")

        assert isinstance(explanation, str)

    def test_refactor_code_method_exists(self):
        """Test that refactor_code helper method exists."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()

        assert hasattr(agent, "refactor_code")
        assert callable(agent.refactor_code)

    def test_refactor_code_returns_dict(self):
        """Test that refactor_code returns a dict."""
        from kaizen.agents.specialized.code_generation import CodeGenerationAgent

        agent = CodeGenerationAgent()
        result = agent.refactor_code(
            "def add(a, b): return a + b", "add type hints", "python"
        )

        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
