"""Tests for hooks system."""

import pytest

from kagura.commands import (
    Command,
    CommandExecutor,
    Hook,
    HookAction,
    HookRegistry,
    HookResult,
    HookType,
    InlineCommandExecutor,
    hook,
)


class TestHookResult:
    """Tests for HookResult."""

    def test_ok_result(self):
        """Test creating OK result."""
        result = HookResult.ok()
        assert result.action == HookAction.OK
        assert result.message is None
        assert result.is_ok()
        assert not result.is_blocked()

    def test_ok_with_message(self):
        """Test OK result with message."""
        result = HookResult.ok("All good")
        assert result.message == "All good"
        assert result.is_ok()

    def test_block_result(self):
        """Test creating BLOCK result."""
        result = HookResult.block("Blocked!")
        assert result.action == HookAction.BLOCK
        assert result.message == "Blocked!"
        assert not result.is_ok()
        assert result.is_blocked()

    def test_suggest_result(self):
        """Test creating SUGGEST result."""
        result = HookResult.suggest("Try this instead")
        assert result.action == HookAction.SUGGEST
        assert result.message == "Try this instead"

    def test_modify_result(self):
        """Test creating MODIFY result."""
        modified = {"command": "ls -la"}
        result = HookResult.modify(modified, "Modified command")
        assert result.action == HookAction.MODIFY
        assert result.modified_input == modified
        assert result.message == "Modified command"


class TestHook:
    """Tests for Hook class."""

    def test_hook_creation(self):
        """Test creating a hook."""
        def callback(tool_input):
            return HookResult.ok()

        hook = Hook(
            name="test-hook",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="bash",
            callback=callback,
        )

        assert hook.name == "test-hook"
        assert hook.hook_type == HookType.PRE_TOOL_USE
        assert hook.matcher == "bash"
        assert hook.enabled

    def test_hook_matches_specific(self):
        """Test hook matching specific tool."""
        def callback(tool_input):
            return HookResult.ok()

        hook = Hook(
            name="test",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="bash",
            callback=callback,
        )

        assert hook.matches("bash")
        assert hook.matches("Bash")  # Case insensitive
        assert not hook.matches("git")

    def test_hook_matches_all(self):
        """Test hook matching all tools."""
        def callback(tool_input):
            return HookResult.ok()

        hook = Hook(
            name="test",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="*",
            callback=callback,
        )

        assert hook.matches("bash")
        assert hook.matches("git")
        assert hook.matches("anything")

    def test_hook_execute(self):
        """Test executing a hook."""
        def callback(tool_input):
            assert tool_input["command"] == "test"
            return HookResult.ok("Success")

        hook = Hook(
            name="test",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="*",
            callback=callback,
        )

        result = hook.execute({"command": "test"})
        assert result.is_ok()
        assert result.message == "Success"

    def test_hook_disabled(self):
        """Test disabled hook returns OK."""
        def callback(tool_input):
            return HookResult.block("Should not run")

        hook = Hook(
            name="test",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="*",
            callback=callback,
            enabled=False,
        )

        result = hook.execute({"command": "test"})
        assert result.is_ok()

    def test_hook_exception_handling(self):
        """Test hook exception is caught."""
        def callback(tool_input):
            raise ValueError("Oops!")

        hook = Hook(
            name="test",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="*",
            callback=callback,
        )

        result = hook.execute({"command": "test"})
        assert result.is_ok()  # Exception caught, continues
        assert "failed" in result.message


class TestHookRegistry:
    """Tests for HookRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = HookRegistry()
        assert registry.count() == 0
        assert registry.count(HookType.PRE_TOOL_USE) == 0

    def test_register_hook(self):
        """Test registering hooks."""
        registry = HookRegistry()

        def callback(tool_input):
            return HookResult.ok()

        hook = Hook(
            name="test",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="bash",
            callback=callback,
        )

        registry.register(hook)
        assert registry.count() == 1
        assert registry.count(HookType.PRE_TOOL_USE) == 1

    def test_unregister_hook(self):
        """Test unregistering hooks."""
        registry = HookRegistry()

        def callback(tool_input):
            return HookResult.ok()

        hook = Hook(
            name="test",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="bash",
            callback=callback,
        )

        registry.register(hook)
        assert registry.count() == 1

        removed = registry.unregister("test")
        assert removed
        assert registry.count() == 0

        # Unregistering again returns False
        removed = registry.unregister("test")
        assert not removed

    def test_get_hooks(self):
        """Test getting matching hooks."""
        registry = HookRegistry()

        def callback(tool_input):
            return HookResult.ok()

        # Register hooks for different tools
        bash_hook = Hook(
            name="bash-hook",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="bash",
            callback=callback,
        )
        git_hook = Hook(
            name="git-hook",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="git",
            callback=callback,
        )
        all_hook = Hook(
            name="all-hook",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="*",
            callback=callback,
        )

        registry.register(bash_hook)
        registry.register(git_hook)
        registry.register(all_hook)

        # Get bash hooks
        bash_hooks = registry.get_hooks(HookType.PRE_TOOL_USE, "bash")
        assert len(bash_hooks) == 2  # bash-hook and all-hook
        assert any(h.name == "bash-hook" for h in bash_hooks)
        assert any(h.name == "all-hook" for h in bash_hooks)

        # Get git hooks
        git_hooks = registry.get_hooks(HookType.PRE_TOOL_USE, "git")
        assert len(git_hooks) == 2  # git-hook and all-hook
        assert any(h.name == "git-hook" for h in git_hooks)

    def test_execute_hooks(self):
        """Test executing multiple hooks."""
        registry = HookRegistry()

        results_log = []

        def callback1(tool_input):
            results_log.append("hook1")
            return HookResult.ok()

        def callback2(tool_input):
            results_log.append("hook2")
            return HookResult.ok()

        hook1 = Hook(
            name="hook1",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="*",
            callback=callback1,
        )
        hook2 = Hook(
            name="hook2",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="*",
            callback=callback2,
        )

        registry.register(hook1)
        registry.register(hook2)

        results = registry.execute_hooks(HookType.PRE_TOOL_USE, "bash", {})
        assert len(results) == 2
        assert all(r.is_ok() for r in results)
        assert results_log == ["hook1", "hook2"]

    def test_execute_hooks_stops_on_block(self):
        """Test hook execution stops on first block."""
        registry = HookRegistry()

        results_log = []

        def callback1(tool_input):
            results_log.append("hook1")
            return HookResult.block("Blocked!")

        def callback2(tool_input):
            results_log.append("hook2")
            return HookResult.ok()

        hook1 = Hook(
            name="hook1",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="*",
            callback=callback1,
        )
        hook2 = Hook(
            name="hook2",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="*",
            callback=callback2,
        )

        registry.register(hook1)
        registry.register(hook2)

        results = registry.execute_hooks(HookType.PRE_TOOL_USE, "bash", {})
        assert len(results) == 1  # Stopped after first block
        assert results[0].is_blocked()
        assert results_log == ["hook1"]  # hook2 never executed

    def test_clear_hooks(self):
        """Test clearing hooks."""
        registry = HookRegistry()

        def callback(tool_input):
            return HookResult.ok()

        hook1 = Hook(
            name="hook1",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="*",
            callback=callback,
        )
        hook2 = Hook(
            name="hook2",
            hook_type=HookType.POST_TOOL_USE,
            matcher="*",
            callback=callback,
        )

        registry.register(hook1)
        registry.register(hook2)
        assert registry.count() == 2

        # Clear only PRE_TOOL_USE
        registry.clear(HookType.PRE_TOOL_USE)
        assert registry.count(HookType.PRE_TOOL_USE) == 0
        assert registry.count(HookType.POST_TOOL_USE) == 1

        # Clear all
        registry.clear()
        assert registry.count() == 0


class TestHookDecorators:
    """Tests for hook decorator API."""

    def test_pre_tool_use_decorator(self):
        """Test @hook.pre_tool_use decorator."""
        registry = HookRegistry()
        from kagura.commands.hook_decorators import HookDecorators
        test_hook = HookDecorators(registry)

        @test_hook.pre_tool_use("bash")
        def validate_bash(tool_input):
            return HookResult.ok()

        assert registry.count() == 1
        hooks = registry.get_hooks(HookType.PRE_TOOL_USE, "bash")
        assert len(hooks) == 1
        assert hooks[0].name == "validate_bash"

    def test_post_tool_use_decorator(self):
        """Test @hook.post_tool_use decorator."""
        registry = HookRegistry()
        from kagura.commands.hook_decorators import HookDecorators
        test_hook = HookDecorators(registry)

        @test_hook.post_tool_use("git")
        def log_git(tool_input):
            return HookResult.ok()

        assert registry.count() == 1
        hooks = registry.get_hooks(HookType.POST_TOOL_USE, "git")
        assert len(hooks) == 1
        assert hooks[0].name == "log_git"

    def test_validation_decorator(self):
        """Test @hook.validation decorator."""
        registry = HookRegistry()
        from kagura.commands.hook_decorators import HookDecorators
        test_hook = HookDecorators(registry)

        @test_hook.validation("*")
        def validate_params(tool_input):
            return HookResult.ok()

        assert registry.count() == 1
        hooks = registry.get_hooks(HookType.VALIDATION, "anything")
        assert len(hooks) == 1


class TestInlineCommandExecutorWithHooks:
    """Tests for InlineCommandExecutor with hooks."""

    def test_pre_tool_use_hook_blocks_command(self):
        """Test that pre-tool-use hook can block command."""
        registry = HookRegistry()

        def block_rm(tool_input):
            if "rm" in tool_input.get("command", ""):
                return HookResult.block("rm command blocked!")
            return HookResult.ok()

        hook = Hook(
            name="block-rm",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="bash",
            callback=block_rm,
        )
        registry.register(hook)

        executor = InlineCommandExecutor(hook_registry=registry)
        result = executor.execute("Files: !`rm -rf /`")

        assert "[Blocked: rm command blocked!]" in result

    def test_pre_tool_use_hook_modifies_command(self):
        """Test that pre-tool-use hook can modify command."""
        registry = HookRegistry()

        def modify_echo(tool_input):
            modified = {"command": "echo 'modified'", "tool": "bash"}
            return HookResult.modify(modified)

        hook = Hook(
            name="modify-echo",
            hook_type=HookType.PRE_TOOL_USE,
            matcher="bash",
            callback=modify_echo,
        )
        registry.register(hook)

        executor = InlineCommandExecutor(hook_registry=registry)
        result = executor.execute("Output: !`echo 'original'`")

        assert "modified" in result
        assert "original" not in result

    def test_post_tool_use_hook_called(self):
        """Test that post-tool-use hook is called after execution."""
        registry = HookRegistry()
        called = []

        def log_execution(tool_input):
            called.append(tool_input)
            return HookResult.ok()

        hook = Hook(
            name="log",
            hook_type=HookType.POST_TOOL_USE,
            matcher="bash",
            callback=log_execution,
        )
        registry.register(hook)

        executor = InlineCommandExecutor(hook_registry=registry)
        executor.execute("Result: !`echo 'test'`")

        assert len(called) == 1
        assert "command" in called[0]
        assert "output" in called[0]


class TestCommandExecutorWithHooks:
    """Tests for CommandExecutor with hooks."""

    def test_validation_hook_blocks_execution(self):
        """Test that validation hook can block execution."""
        registry = HookRegistry()

        def validate_params(tool_input):
            params = tool_input.get("parameters", {})
            if not params.get("required_param"):
                return HookResult.block("required_param is missing!")
            return HookResult.ok()

        hook = Hook(
            name="validate",
            hook_type=HookType.VALIDATION,
            matcher="*",
            callback=validate_params,
        )
        registry.register(hook)

        command = Command(
            name="test",
            description="Test",
            template="Hello {{ name }}!",
            parameters={"name": "string"},
        )

        executor = CommandExecutor(hook_registry=registry)

        with pytest.raises(ValueError, match="required_param is missing"):
            executor.render(command, {"name": "Alice"})

    def test_validation_hook_modifies_parameters(self):
        """Test that validation hook can modify parameters."""
        registry = HookRegistry()

        def add_default(tool_input):
            params = tool_input.get("parameters", {})
            if "name" not in params:
                params["name"] = "Default"
            return HookResult.modify({"parameters": params})

        hook = Hook(
            name="add-default",
            hook_type=HookType.VALIDATION,
            matcher="*",
            callback=add_default,
        )
        registry.register(hook)

        command = Command(
            name="test",
            description="Test",
            template="Hello {{ name }}!",
        )

        executor = CommandExecutor(hook_registry=registry)
        result = executor.render(command, {})

        assert "Hello Default!" in result
