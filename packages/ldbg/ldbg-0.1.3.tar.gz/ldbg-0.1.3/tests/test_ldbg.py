import inspect
import builtins
import types
import os

import ldbg.ldbg as ldbg


def test_extract_code_blocks_single_block():
    md = "Here is some text\n```python\nprint('hello')\n```\nmore text"
    blocks = ldbg.extract_code_blocks(md)
    assert blocks == ["print('hello')\n"]


def test_extract_code_blocks_multiple_blocks():
    md = "```\na=1\n```\ntext\n```py\nb=2\n```"
    blocks = ldbg.extract_code_blocks(md)
    assert blocks == ["a=1\n", "b=2\n"]


def test_execute_code_block_prints_output(capsys):
    # execute_code_block uses exec(..., {}) so it runs in an empty namespace.
    ldbg.execute_code_block("print('hi from code block')", locals())
    captured = capsys.readouterr()
    assert "hi from code block" in captured.out


def test_execute_blocks_none_does_nothing(capsys):
    # Should not raise and should not print anything
    ldbg.execute_blocks(None, locals())
    captured = capsys.readouterr()
    assert captured.out == ""


def test_execute_blocks_user_confirms_exec(monkeypatch, capsys):
    # Provide markdown with a single code block.
    md = "Some text\n```\nprint('ran')\n```\n"
    # Simulate user input 'y'
    monkeypatch.setattr(builtins, "input", lambda prompt="": "y")
    # Simulate enough time passing (>0.5s) between prompt and input to bypass safety gate
    t = {"val": 0.0}
    def fake_time():
        t["val"] += 1.0
        return t["val"]
    monkeypatch.setattr(ldbg.time, "time", fake_time)

    executed = {"called": False, "code": None}

    def fake_exec_block(code, locals):
        executed["called"] = True
        executed["code"] = code

    monkeypatch.setattr(ldbg, "execute_code_block", fake_exec_block)

    ldbg.execute_blocks(md, locals())

    captured = capsys.readouterr()
    # We expect to have been prompted and the code executed
    assert "Would you like to execute the following code block:" in captured.out
    assert executed["called"] is True
    assert "print('ran')" in executed["code"]


def test_execute_blocks_user_declines(monkeypatch, capsys):
    md = "```\nprint('should_not_run')\n```"
    # Simulate user input 'n'
    monkeypatch.setattr(builtins, "input", lambda prompt="": "n")
    # Simulate enough time passing (>0.5s) between prompt and input to bypass safety gate
    t = {"val": 0.0}
    def fake_time():
        t["val"] += 1.0
        return t["val"]
    monkeypatch.setattr(ldbg.time, "time", fake_time)

    executed = {"called": False}

    monkeypatch.setattr(
        ldbg, "execute_code_block", lambda code: executed.update(called=True)
    )

    ldbg.execute_blocks(md, locals())
    captured = capsys.readouterr()
    assert "Would you like to execute the following code block:" in captured.out
    assert executed.get("called") is not True


def test_generate_commands_calls_api_and_forwards_response(monkeypatch, capsys):
    """
    Ensure generate_commands:
      - prints the system prompt when print_prompt=True
      - calls the client.chat.completions.create API (mocked)
      - prints the model response and passes it to execute_blocks
    """
    # Create a fake response text that contains a code block
    fake_response_text = (
        "Here is a suggestion:\n\n```python\nprint('from model')\n```\n"
        "And a closing line."
    )

    # Spy object to verify execute_blocks received the model response
    called = {"create_called": False, "passed_response": None}

    def fake_create(*args, **kwargs):
        called["create_called"] = True
        # Build an object with the expected shape: .choices[0].message.content
        msg = types.SimpleNamespace(content=fake_response_text)
        choice = types.SimpleNamespace(message=msg)
        return types.SimpleNamespace(choices=[choice])

    # Patch the chain client.chat.completions.create
    monkeypatch.setattr(ldbg.client.chat.completions, "create", fake_create)

    # Patch execute_blocks to capture what is passed
    def fake_execute_blocks(resp_text, locals):
        called["passed_response"] = resp_text

    monkeypatch.setattr(ldbg, "execute_blocks", fake_execute_blocks)

    # Ensure the function does not early-return due to VSCode warning
    monkeypatch.setattr(ldbg, "display_vscode_warning", False)

    # Call generate_commands from a real frame (the test's current frame) to let it build context
    frame = inspect.currentframe()
    # Run function
    ldbg.generate_commands("describe unknown_data", frame=frame, print_prompt=True)

    captured = capsys.readouterr()
    # Confirm we printed the System prompt and the asking line
    assert "System prompt:" in captured.out
    assert 'Asking gpt-5-mini-2025-08-07 "describe unknown_data"...' in captured.out

    # Confirm the API stub was called and execute_blocks got the model response
    assert called["create_called"] is True
    assert called["passed_response"] == fake_response_text


def test_generate_commands_handles_none_response(monkeypatch, capsys):
    """
    If the API returns a response object with None content, generate_commands should return gracefully.
    """

    def fake_create_none(*args, **kwargs):
        msg = types.SimpleNamespace(content=None)
        choice = types.SimpleNamespace(message=msg)
        return types.SimpleNamespace(choices=[choice])

    monkeypatch.setattr(ldbg.client.chat.completions, "create", fake_create_none)
    # Patch execute_blocks to ensure it would not be called when response is None
    monkeypatch.setattr(
        ldbg,
        "execute_blocks",
        lambda t: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    # Ensure the function does not early-return due to VSCode warning
    monkeypatch.setattr(ldbg, "display_vscode_warning", False)

    # Call - should not raise
    ldbg.generate_commands(
        "any prompt", frame=inspect.currentframe(), print_prompt=False
    )


def test_initialize_client_default_openai(monkeypatch):
    """Test that initialize_client returns OpenAI client by default."""
    monkeypatch.delenv("LDBG_API", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    
    client, model = ldbg.initialize_client()
    
    assert client is not None
    assert isinstance(client, ldbg.OpenAI)
    assert model == "gpt-4-mini"


def test_initialize_client_deepseek(monkeypatch):
    """Test that initialize_client works with DeepSeek provider."""
    monkeypatch.setenv("LDBG_API", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_deepseek_key")
    
    client, model = ldbg.initialize_client()
    
    assert client is not None
    assert isinstance(client, ldbg.OpenAI)
    assert model == "deepseek-chat"
    assert str(client.base_url) == "https://api.deepseek.com/v1/"


def test_initialize_client_groq(monkeypatch):
    """Test that initialize_client works with Groq provider."""
    monkeypatch.setenv("LDBG_API", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    
    client, model = ldbg.initialize_client()
    
    assert client is not None
    assert isinstance(client, ldbg.OpenAI)
    assert model == "mixtral-8x7b-32768"
    assert str(client.base_url) == "https://api.groq.com/openai/v1/"


def test_initialize_client_anthropic(monkeypatch):
    """Test that initialize_client works with Anthropic provider."""
    monkeypatch.setenv("LDBG_API", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")
    
    client, model = ldbg.initialize_client()
    
    assert client is not None
    assert isinstance(client, ldbg.OpenAI)
    assert model == "claude-3-5-sonnet-20241022"
    assert client.base_url == "https://api.anthropic.com/v1/"


def test_initialize_client_together(monkeypatch):
    """Test that initialize_client works with Together AI provider."""
    monkeypatch.setenv("LDBG_API", "together")
    monkeypatch.setenv("TOGETHER_API_KEY", "test_together_key")
    
    client, model = ldbg.initialize_client()
    
    assert client is not None
    assert isinstance(client, ldbg.OpenAI)
    assert model == "meta-llama/Llama-3-70b-chat-hf"
    assert str(client.base_url) == "https://api.together.xyz/v1/"


def test_initialize_client_openrouter(monkeypatch):
    """Test that initialize_client works with OpenRouter provider."""
    monkeypatch.setenv("LDBG_API", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_openrouter_key")
    
    client, model = ldbg.initialize_client()
    
    assert client is not None
    assert isinstance(client, ldbg.OpenAI)
    assert model == "openai/gpt-4-turbo"
    assert str(client.base_url) == "https://openrouter.ai/api/v1/"


def test_initialize_client_ollama(monkeypatch):
    """Test that initialize_client works with Ollama provider."""
    monkeypatch.setenv("LDBG_API", "ollama")
    # Ollama doesn't require an API key
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    
    client, model = ldbg.initialize_client()
    
    assert client is not None
    assert isinstance(client, ldbg.OpenAI)
    assert model == "llama2"
    assert str(client.base_url) == "http://localhost:11434/v1/"


def test_initialize_client_invalid_provider(monkeypatch):
    """Test that initialize_client raises error for invalid provider."""
    monkeypatch.setenv("LDBG_API", "invalid_provider")
    
    try:
        ldbg.initialize_client()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown provider" in str(e)


def test_initialize_client_missing_api_key(monkeypatch):
    """Test that initialize_client raises error when API key is missing."""
    monkeypatch.setenv("LDBG_API", "deepseek")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    
    try:
        ldbg.initialize_client()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "API key not found" in str(e)


def test_generate_commands_uses_default_model(monkeypatch, capsys):
    """Test that generate_commands uses the default model when none is specified."""
    fake_response_text = "Here is a suggestion:\n\n```python\nprint('test')\n```\n"

    def fake_create(*args, **kwargs):
        # Verify the model parameter matches the default
        assert kwargs.get("model") == ldbg.DEFAULT_MODEL
        msg = types.SimpleNamespace(content=fake_response_text)
        choice = types.SimpleNamespace(message=msg)
        return types.SimpleNamespace(choices=[choice])

    monkeypatch.setattr(ldbg.client.chat.completions, "create", fake_create)
    monkeypatch.setattr(ldbg, "execute_blocks", lambda resp_text, locals: None)
    monkeypatch.setattr(ldbg, "display_vscode_warning", False)

    # Call without specifying model
    ldbg.generate_commands(
        "test prompt", frame=inspect.currentframe(), print_prompt=False
    )

    captured = capsys.readouterr()
    assert f'Asking {ldbg.DEFAULT_MODEL} "test prompt"...' in captured.out
