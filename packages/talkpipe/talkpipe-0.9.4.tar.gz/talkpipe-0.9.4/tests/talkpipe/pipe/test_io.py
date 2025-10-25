import json, pickle, os
from unittest.mock import Mock, patch
from talkpipe.pipe import io
from talkpipe.util import config
from talkpipe.chatterlang import compiler

def test_echo_operation():
    f = compiler.compile('INPUT FROM echo[data="howdy|do", delimiter="|"]').as_function(single_in=True, single_out=False)
    ans = f(None)
    assert ans == ["howdy", "do"]

    f = compiler.compile('INPUT FROM echo[data="howdy,do"]').as_function(single_in=True, single_out=False)
    ans = f(None)
    assert ans == ["howdy", "do"]

    f = io.echo(data="howdy|do", delimiter='|')
    ans = list(f())
    assert ans == ["howdy", "do"]

def test_echo_with_n_parameter():
    """Test echo source with n parameter to repeat output."""
    # Test repeating multiple items with default delimiter
    f = compiler.compile('INPUT FROM echo[data="a,b", n=2]').as_function(single_in=True, single_out=False)
    ans = f(None)
    assert ans == ["a", "b", "a", "b"]

    # Test repeating multiple items with custom delimiter
    f = compiler.compile('INPUT FROM echo[data="x|y|z", delimiter="|", n=2]').as_function(single_in=True, single_out=False)
    ans = f(None)
    assert ans == ["x", "y", "z", "x", "y", "z"]

    # Test default n=1 behavior (unchanged)
    f = io.echo(data="test")
    ans = list(f())
    assert ans == ["test"]

    # Test direct call with n parameter
    f = io.echo(data="a,b", n=3)
    ans = list(f())
    assert ans == ["a", "b", "a", "b", "a", "b"]

    # Test repeating single item (no delimiter) using direct call
    f = io.echo(data="hello", delimiter=None, n=3)
    ans = list(f())
    assert ans == ["hello", "hello", "hello"]

def test_readJSONL(tmpdir):
    data = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35}
    ]

    temp_file_path = tmpdir.join("test.jsonl")
    with open(temp_file_path, 'w') as temp_file:
        for entry in data:
            temp_file.write(json.dumps(entry) + '\n')

    f = io.readJsonl()
    ans = list(f([temp_file_path]))
    assert ans == data

def test_dumpsJsonl():
    data = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35}
    ]

    f = io.dumpsJsonl()
    ans = list(f(data))
    assert ans == [json.dumps(entry) for entry in data]
        
def test_print(capsys):
    f = io.Print()
    ans = list(f(["howdy", "do"]))
    assert ans == ["howdy", "do"]
    captured = capsys.readouterr()
    assert captured.out == "howdy\ndo\n"
    
    f = io.Print(field_list="age")
    ans = list(f([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]))
    assert ans == [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    captured = capsys.readouterr()
    assert captured.out == "{'age': 30}\n{'age': 25}\n"

def test_log(capsys, tmpdir):

    config.configure_logger("test.log:INFO")
    f = io.Log(level="DEBUG", log_name="test.log")
    ans = list(f(["howdy", "do"]))
    assert ans == ["howdy", "do"]
    captured = capsys.readouterr()
    assert "howdy" not in captured.out 
    assert "do" not in captured.out

    config.configure_logger("test.log:DEBUG")
    f = io.Log(level="DEBUG", log_name="test.log")
    ans = list(f(["howdy", "do"]))
    assert ans == ["howdy", "do"]
    captured = capsys.readouterr()
    assert "howdy" in captured.err 
    assert "do" in captured.err

    config.configure_logger("test.log:DEBUG", logger_files=f"test.log:{os.path.join(str(tmpdir), 'test.log')}")
    f = io.Log(level="DEBUG", log_name="test.log")
    ans = list(f(["howdy", "do"]))
    assert ans == ["howdy", "do"]
    captured = capsys.readouterr()
    assert "howdy" in captured.err 
    assert "do" in captured.err
    with open(os.path.join(str(tmpdir), 'test.log'), 'r') as f:
        assert "howdy" in f.readline()
        assert "do" in f.readline()

def test_writePickle_basic_functionality(tmpdir):
    """Test basic writePickle functionality - writes all items and yields them."""
    data = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35}
    ]
    
    temp_file_path = tmpdir.join("test_basic.pickle")
    f = io.writePickle(fname=str(temp_file_path))
    
    # Test that all items are yielded
    result = list(f(data))
    assert result == data
    
    # Test that all items were written to pickle file
    with open(str(temp_file_path), 'rb') as file:
        loaded_items = []
        try:
            while True:
                loaded_items.append(pickle.load(file))
        except EOFError:
            pass
    assert loaded_items == data

def test_writePickle_first_only_true(tmpdir):
    """Test writePickle with first_only=True - only writes first item but yields all."""
    data = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35}
    ]
    
    temp_file_path = tmpdir.join("test_first_only.pickle")
    f = io.writePickle(fname=str(temp_file_path), first_only=True)
    
    # Test that all items are still yielded
    result = list(f(data))
    assert result == data
    
    # Test that only first item was written to pickle file
    with open(str(temp_file_path), 'rb') as file:
        first_item = pickle.load(file)
        assert first_item == data[0]
        
        # Verify no more items in file
        try:
            pickle.load(file)
            assert False, "Expected only one item in pickle file"
        except EOFError:
            pass  # Expected behavior

def test_writePickle_empty_data(tmpdir):
    """Test writePickle with empty input data."""
    temp_file_path = tmpdir.join("test_empty.pickle")
    f = io.writePickle(fname=str(temp_file_path))
    
    result = list(f([]))
    assert result == []
    
    # File should exist but be empty
    assert os.path.exists(str(temp_file_path))
    with open(str(temp_file_path), 'rb') as file:
        try:
            pickle.load(file)
            assert False, "Expected empty pickle file"
        except EOFError:
            pass  # Expected behavior

def test_writePickle_compiler_integration(tmpdir):
    """Test writePickle integration with compiler system."""
    data = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ]
    
    temp_file_path = tmpdir.join("test_compiler.pickle")
    
    # Test compilation and execution
    pipeline = compiler.compile(f'| writePickle[fname="{str(temp_file_path)}"]')
    f = pipeline.as_function(single_in=False, single_out=False)
    result = f(data)
    assert result == data
    
    # Verify pickle file contents
    with open(str(temp_file_path), 'rb') as file:
        loaded_items = []
        try:
            while True:
                loaded_items.append(pickle.load(file))
        except EOFError:
            pass
    assert loaded_items == data

def test_writePickle_different_data_types(tmpdir):
    """Test writePickle with various data types."""
    data = [
        42,
        "string_data", 
        [1, 2, 3],
        {"nested": {"dict": True}},
        None
    ]
    
    temp_file_path = tmpdir.join("test_types.pickle")
    f = io.writePickle(fname=str(temp_file_path))
    
    result = list(f(data))
    assert result == data
    
    # Verify all types were pickled correctly
    with open(str(temp_file_path), 'rb') as file:
        loaded_items = []
        try:
            while True:
                loaded_items.append(pickle.load(file))
        except EOFError:
            pass
    assert loaded_items == data

def test_writeString_basic_functionality(tmpdir):
    """Test basic writeString functionality - writes all items and yields them."""
    data = ["Alice", "Bob", "Charlie"]
    
    temp_file_path = tmpdir.join("test_basic.txt")
    f = io.writeString(fname=str(temp_file_path))
    
    # Test that all items are yielded
    result = list(f(data))
    assert result == data
    
    # Test that all items were written to file with newlines
    with open(str(temp_file_path), 'r') as file:
        content = file.read()
    assert content == "Alice\nBob\nCharlie\n"

def test_writeString_first_only_true(tmpdir):
    """Test writeString with first_only=True - only writes first item but yields all."""
    data = ["Alice", "Bob", "Charlie"]
    
    temp_file_path = tmpdir.join("test_first_only.txt")
    f = io.writeString(fname=str(temp_file_path), first_only=True)
    
    # Test that all items are still yielded
    result = list(f(data))
    assert result == data
    
    # Test that only first item was written to file
    with open(str(temp_file_path), 'r') as file:
        content = file.read()
    assert content == "Alice\n"

def test_writeString_no_newline(tmpdir):
    """Test writeString with new_line=False."""
    data = ["Alice", "Bob", "Charlie"]
    
    temp_file_path = tmpdir.join("test_no_newline.txt")
    f = io.writeString(fname=str(temp_file_path), new_line=False)
    
    # Test that all items are yielded
    result = list(f(data))
    assert result == data
    
    # Test that items were written without newlines
    with open(str(temp_file_path), 'r') as file:
        content = file.read()
    assert content == "AliceBobCharlie"

def test_writeString_first_only_no_newline(tmpdir):
    """Test writeString with first_only=True and new_line=False."""
    data = ["Alice", "Bob", "Charlie"]
    
    temp_file_path = tmpdir.join("test_first_no_newline.txt")
    f = io.writeString(fname=str(temp_file_path), first_only=True, new_line=False)
    
    # Test that all items are still yielded
    result = list(f(data))
    assert result == data
    
    # Test that only first item was written without newline
    with open(str(temp_file_path), 'r') as file:
        content = file.read()
    assert content == "Alice"

def test_writeString_empty_data(tmpdir):
    """Test writeString with empty input data."""
    temp_file_path = tmpdir.join("test_empty.txt")
    f = io.writeString(fname=str(temp_file_path))
    
    result = list(f([]))
    assert result == []
    
    # File should exist but be empty
    assert os.path.exists(str(temp_file_path))
    with open(str(temp_file_path), 'r') as file:
        content = file.read()
    assert content == ""

def test_writeString_different_data_types(tmpdir):
    """Test writeString with various data types."""
    data = [
        42,
        3.14,
        True,
        None,
        [1, 2, 3],
        {"name": "Alice"}
    ]
    
    temp_file_path = tmpdir.join("test_types.txt")
    f = io.writeString(fname=str(temp_file_path))
    
    result = list(f(data))
    assert result == data
    
    # Verify all types were converted to strings correctly
    with open(str(temp_file_path), 'r') as file:
        content = file.read()
    expected = "42\n3.14\nTrue\nNone\n[1, 2, 3]\n{'name': 'Alice'}\n"
    assert content == expected

def test_writeString_compiler_integration(tmpdir):
    """Test writeString integration with compiler system."""
    data = ["Alice", "Bob"]
    
    temp_file_path = tmpdir.join("test_compiler.txt")
    
    # Test compilation and execution
    pipeline = compiler.compile(f'| writeString[fname="{str(temp_file_path)}"]')
    f = pipeline.as_function(single_in=False, single_out=False)
    result = f(data)
    assert result == data
    
    # Verify file contents
    with open(str(temp_file_path), 'r') as file:
        content = file.read()
    assert content == "Alice\nBob\n"

def test_writeString_single_item(tmpdir):
    """Test writeString with single item."""
    data = ["single_item"]

    temp_file_path = tmpdir.join("test_single.txt")
    f = io.writeString(fname=str(temp_file_path))

    result = list(f(data))
    assert result == data

    with open(str(temp_file_path), 'r') as file:
        content = file.read()
    assert content == "single_item\n"

def test_prompt_error_handling_continues_after_exception(capsys):
    """Test that Prompt with error-resilient pipeline catches downstream exceptions and continues prompting."""
    # Mock the PromptSession to return specific values
    mock_session = Mock()
    mock_session.prompt.side_effect = [
        "1",      # Valid input
        "abc",    # Invalid input that will cause error
        "2",      # Valid input after error
        EOFError()  # Simulate user exiting
    ]

    # Create a lambda segment that will fail on non-numeric input
    from talkpipe.pipe.basic import EvalExpression

    with patch('talkpipe.pipe.io.PromptSession', return_value=mock_session):
        prompt = io.Prompt()
        # Chain with a lambda that converts to int (will fail on "abc")
        pipeline = prompt | EvalExpression(expression="int(item)")

        # Convert to function and execute
        func = pipeline.as_function()
        results = func()

        # Should get results for valid inputs only
        assert 1 in results
        assert 2 in results
        # "abc" should have caused an error but not stopped the pipeline

        # Verify error was printed
        captured = capsys.readouterr()
        assert "Error:" in captured.out or "invalid literal" in captured.out.lower()

def test_prompt_keyboard_interrupt_continues(capsys):
    """Test that Prompt handles KeyboardInterrupt and continues prompting."""
    mock_session = Mock()
    mock_session.prompt.side_effect = [
        "first input",
        KeyboardInterrupt(),
        "second input",
        EOFError()
    ]

    with patch('talkpipe.pipe.io.PromptSession', return_value=mock_session):
        prompt = io.Prompt()
        generator = prompt.generate()

        # First input should work normally
        assert next(generator) == "first input"

        # After KeyboardInterrupt, generator should continue
        assert next(generator) == "second input"

        # Verify message was printed
        captured = capsys.readouterr()
        assert "Interrupted" in captured.out

def test_prompt_eof_terminates():
    """Test that Prompt terminates on EOFError."""
    mock_session = Mock()
    mock_session.prompt.side_effect = [
        "first input",
        EOFError()
    ]

    with patch('talkpipe.pipe.io.PromptSession', return_value=mock_session):
        prompt = io.Prompt()
        generator = prompt.generate()

        # First input should work
        assert next(generator) == "first input"

        # EOFError should cause generator to stop
        try:
            next(generator)
            assert False, "Generator should have stopped on EOFError"
        except StopIteration:
            pass  # Expected behavior
