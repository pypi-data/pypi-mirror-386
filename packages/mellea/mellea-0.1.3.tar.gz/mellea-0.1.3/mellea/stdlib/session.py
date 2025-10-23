"""Mellea Sessions."""

from __future__ import annotations

import contextvars
from copy import copy
from typing import Any, Literal, overload

from PIL import Image as PILImage

import mellea.stdlib.funcs as mfuncs
from mellea.backends import Backend, BaseModelSubclass
from mellea.backends.model_ids import (
    IBM_GRANITE_3_3_8B,
    IBM_GRANITE_4_MICRO_3B,
    ModelIdentifier,
)
from mellea.backends.ollama import OllamaModelBackend
from mellea.backends.openai import OpenAIBackend
from mellea.helpers.fancy_logger import FancyLogger
from mellea.stdlib.base import (
    CBlock,
    Component,
    Context,
    GenerateLog,
    ImageBlock,
    ModelOutputThunk,
    SimpleContext,
)
from mellea.stdlib.chat import Message
from mellea.stdlib.requirement import Requirement, ValidationResult
from mellea.stdlib.sampling import SamplingResult, SamplingStrategy
from mellea.stdlib.sampling.base import RejectionSamplingStrategy

# Global context variable for the context session
_context_session: contextvars.ContextVar[MelleaSession | None] = contextvars.ContextVar(
    "context_session", default=None
)


def get_session() -> MelleaSession:
    """Get the current session from context.

    Raises:
        RuntimeError: If no session is currently active.
    """
    session = _context_session.get()
    if session is None:
        raise RuntimeError(
            "No active session found. Use 'with start_session(...):' to create one."
        )
    return session


def backend_name_to_class(name: str) -> Any:
    """Resolves backend names to Backend classes."""
    if name == "ollama":
        return OllamaModelBackend
    elif name == "hf" or name == "huggingface":
        from mellea.backends.huggingface import LocalHFBackend

        return LocalHFBackend
    elif name == "openai":
        return OpenAIBackend
    elif name == "watsonx":
        from mellea.backends.watsonx import WatsonxAIBackend

        return WatsonxAIBackend
    elif name == "litellm":
        from mellea.backends.litellm import LiteLLMBackend

        return LiteLLMBackend
    else:
        return None


def start_session(
    backend_name: Literal["ollama", "hf", "openai", "watsonx", "litellm"] = "ollama",
    model_id: str | ModelIdentifier = IBM_GRANITE_4_MICRO_3B,
    ctx: Context | None = None,
    *,
    model_options: dict | None = None,
    **backend_kwargs,
) -> MelleaSession:
    """Start a new Mellea session. Can be used as a context manager or called directly.

    This function creates and configures a new Mellea session with the specified backend
    and model. When used as a context manager (with `with` statement), it automatically
    sets the session as the current active session for use with convenience functions
    like `instruct()`, `chat()`, `query()`, and `transform()`. When called directly,
    it returns a session object that can be used directly.

    Args:
        backend_name: The backend to use. Options are:
            - "ollama": Use Ollama backend for local models
            - "hf" or "huggingface": Use HuggingFace transformers backend
            - "openai": Use OpenAI API backend
            - "watsonx": Use IBM WatsonX backend
            - "litellm": Use the LiteLLM backend
        model_id: Model identifier or name. Can be a `ModelIdentifier` from
            mellea.backends.model_ids or a string model name.
        ctx: Context manager for conversation history. Defaults to SimpleContext().
            Use ChatContext() for chat-style conversations.
        model_options: Additional model configuration options that will be passed
            to the backend (e.g., temperature, max_tokens, etc.).
        **backend_kwargs: Additional keyword arguments passed to the backend constructor.

    Returns:
        MelleaSession: A session object that can be used as a context manager
        or called directly with session methods.

    Usage:
        # As a context manager (sets global session):
        with start_session("ollama", "granite3.3:8b") as session:
            result = instruct("Generate a story")  # Uses current session
            # session is also available directly
            other_result = session.chat("Hello")

        # Direct usage (no global session set):
        session = start_session("ollama", "granite3.3:8b")
        result = session.instruct("Generate a story")
        # Remember to call session.cleanup() when done
        session.cleanup()

    Examples:
        # Basic usage with default settings
        with start_session() as session:
            response = instruct("Explain quantum computing")

        # Using OpenAI with custom model options
        with start_session("openai", "gpt-4", model_options={"temperature": 0.7}):
            response = chat("Write a poem")

        # Using HuggingFace with ChatContext for conversations
        from mellea.stdlib.base import ChatContext
        with start_session("hf", "microsoft/DialoGPT-medium", ctx=ChatContext()):
            chat("Hello!")
            chat("How are you?")  # Remembers previous message

        # Direct usage without context manager
        session = start_session()
        response = session.instruct("Explain quantum computing")
        session.cleanup()
    """
    backend_class = backend_name_to_class(backend_name)
    if backend_class is None:
        raise Exception(
            f"Backend name {backend_name} unknown. Please see the docstring for `mellea.stdlib.session.start_session` for a list of options."
        )
    assert backend_class is not None
    backend = backend_class(model_id, model_options=model_options, **backend_kwargs)

    if ctx is None:
        ctx = SimpleContext()
    return MelleaSession(backend, ctx)


class MelleaSession:
    """Mellea sessions are a THIN wrapper around `m` convenience functions with NO special semantics.

    Using a Mellea session is not required, but it does represent the "happy path" of Mellea programming. Some nice things about ussing a `MelleaSession`:
    1. In most cases you want to keep a Context together with the Backend from which it came.
    2. You can directly run an instruction or a send a chat, instead of first creating the `Instruction` or `Chat` object and then later calling backend.generate on the object.
    3. The context is "threaded-through" for you, which allows you to issue a sequence of commands instead of first calling backend.generate on something and then appending it to your context.

    These are all relatively simple code hygiene and state management benefits, but they add up over time.
    If you are doing complicating programming (e.g., non-trivial inference scaling) then you might be better off forgoing `MelleaSession`s and managing your Context and Backend directly.

    Note: we put the `instruct`, `validate`, and other convenience functions here instead of in `Context` or `Backend` to avoid import resolution issues.
    """

    ctx: Context

    def __init__(self, backend: Backend, ctx: Context | None = None):
        """Initializes a new Mellea session with the provided backend and context.

        Args:
            backend (Backend): This is always required.
            ctx (Context): The way in which the model's context will be managed. By default, each interaction with the model is a stand-alone interaction, so we use SimpleContext as the default.
        """
        self.backend = backend
        self.ctx: Context = ctx if ctx is not None else SimpleContext()
        self._session_logger = FancyLogger.get_logger()
        self._context_token = None

    def __enter__(self):
        """Enter context manager and set this session as the current global session."""
        self._context_token = _context_session.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and cleanup session."""
        self.cleanup()
        if self._context_token is not None:
            _context_session.reset(self._context_token)
            self._context_token = None

    def __copy__(self):
        """Use self.clone. Copies the current session but keeps references to the backend and context."""
        new = MelleaSession(backend=self.backend, ctx=self.ctx)
        new._session_logger = self._session_logger
        # Explicitly don't copy over the _context_token.

        return new

    def clone(self):
        """Useful for running multiple generation requests while keeping the context at a given point in time.

        Returns:
            a copy of the current session. Keeps the context, backend, and session logger.

        Examples:
            >>> from mellea import start_session
            >>> m = start_session()
            >>> m.instruct("What is 2x2?")
            >>>
            >>> m1 = m.clone()
            >>> out = m1.instruct("Multiply that by 2")
            >>> print(out)
            ... 8
            >>>
            >>> m2 = m.clone()
            >>> out = m2.instruct("Multiply that by 3")
            >>> print(out)
            ... 12
        """
        return copy(self)

    def reset(self):
        """Reset the context state."""
        self.ctx = self.ctx.reset_to_new()

    def cleanup(self) -> None:
        """Clean up session resources."""
        self.reset()
        if hasattr(self.backend, "close"):
            self.backend.close()  # type: ignore

    @overload
    def act(
        self,
        action: Component,
        *,
        requirements: list[Requirement] | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: Literal[False] = False,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> ModelOutputThunk: ...

    @overload
    def act(
        self,
        action: Component,
        *,
        requirements: list[Requirement] | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: Literal[True],
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> SamplingResult: ...

    def act(
        self,
        action: Component,
        *,
        requirements: list[Requirement] | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: bool = False,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> ModelOutputThunk | SamplingResult:
        """Runs a generic action, and adds both the action and the result to the context.

        Args:
            action: the Component from which to generate.
            requirements: used as additional requirements when a sampling strategy is provided
            strategy: a SamplingStrategy that describes the strategy for validating and repairing/retrying for the instruct-validate-repair pattern. None means that no particular sampling strategy is used.
            return_sampling_results: attach the (successful and failed) sampling attempts to the results.
            format: if set, the BaseModel to use for constrained decoding.
            model_options: additional model options, which will upsert into the model/backend's defaults.
            tool_calls: if true, tool calling is enabled.

        Returns:
            A ModelOutputThunk if `return_sampling_results` is `False`, else returns a `SamplingResult`.
        """
        r = mfuncs.act(
            action,
            context=self.ctx,
            backend=self.backend,
            requirements=requirements,
            strategy=strategy,
            return_sampling_results=return_sampling_results,
            format=format,
            model_options=model_options,
            tool_calls=tool_calls,
        )  # type: ignore

        if isinstance(r, SamplingResult):
            self.ctx = r.result_ctx
            return r
        else:
            result, context = r
            self.ctx = context
            return result

    @overload
    def instruct(
        self,
        description: str,
        *,
        images: list[ImageBlock] | list[PILImage.Image] | None = None,
        requirements: list[Requirement | str] | None = None,
        icl_examples: list[str | CBlock] | None = None,
        grounding_context: dict[str, str | CBlock | Component] | None = None,
        user_variables: dict[str, str] | None = None,
        prefix: str | CBlock | None = None,
        output_prefix: str | CBlock | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: Literal[False] = False,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> ModelOutputThunk: ...

    @overload
    def instruct(
        self,
        description: str,
        *,
        images: list[ImageBlock] | list[PILImage.Image] | None = None,
        requirements: list[Requirement | str] | None = None,
        icl_examples: list[str | CBlock] | None = None,
        grounding_context: dict[str, str | CBlock | Component] | None = None,
        user_variables: dict[str, str] | None = None,
        prefix: str | CBlock | None = None,
        output_prefix: str | CBlock | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: Literal[True],
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> SamplingResult: ...

    def instruct(
        self,
        description: str,
        *,
        images: list[ImageBlock] | list[PILImage.Image] | None = None,
        requirements: list[Requirement | str] | None = None,
        icl_examples: list[str | CBlock] | None = None,
        grounding_context: dict[str, str | CBlock | Component] | None = None,
        user_variables: dict[str, str] | None = None,
        prefix: str | CBlock | None = None,
        output_prefix: str | CBlock | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: bool = False,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> ModelOutputThunk | SamplingResult:
        """Generates from an instruction.

        Args:
            description: The description of the instruction.
            requirements: A list of requirements that the instruction can be validated against.
            icl_examples: A list of in-context-learning examples that the instruction can be validated against.
            grounding_context: A list of grounding contexts that the instruction can use. They can bind as variables using a (key: str, value: str | ContentBlock) tuple.
            user_variables: A dict of user-defined variables used to fill in Jinja placeholders in other parameters. This requires that all other provided parameters are provided as strings.
            prefix: A prefix string or ContentBlock to use when generating the instruction.
            output_prefix: A string or ContentBlock that defines a prefix for the output generation. Usually you do not need this.
            strategy: A SamplingStrategy that describes the strategy for validating and repairing/retrying for the instruct-validate-repair pattern. None means that no particular sampling strategy is used.
            return_sampling_results: attach the (successful and failed) sampling attempts to the results.
            format: If set, the BaseModel to use for constrained decoding.
            model_options: Additional model options, which will upsert into the model/backend's defaults.
            tool_calls: If true, tool calling is enabled.
            images: A list of images to be used in the instruction or None if none.
        """
        r = mfuncs.instruct(
            description,
            context=self.ctx,
            backend=self.backend,
            images=images,
            requirements=requirements,
            icl_examples=icl_examples,
            grounding_context=grounding_context,
            user_variables=user_variables,
            prefix=prefix,
            output_prefix=output_prefix,
            strategy=strategy,
            return_sampling_results=return_sampling_results,  # type: ignore
            format=format,
            model_options=model_options,
            tool_calls=tool_calls,
        )

        if isinstance(r, SamplingResult):
            self.ctx = r.result_ctx
            return r
        else:
            # It's a tuple[ModelOutputThunk, Context].
            result, context = r
            self.ctx = context
            return result

    def chat(
        self,
        content: str,
        role: Message.Role = "user",
        *,
        images: list[ImageBlock] | list[PILImage.Image] | None = None,
        user_variables: dict[str, str] | None = None,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> Message:
        """Sends a simple chat message and returns the response. Adds both messages to the Context."""
        result, context = mfuncs.chat(
            content=content,
            context=self.ctx,
            backend=self.backend,
            role=role,
            images=images,
            user_variables=user_variables,
            format=format,
            model_options=model_options,
            tool_calls=tool_calls,
        )

        self.ctx = context
        return result

    def validate(
        self,
        reqs: Requirement | list[Requirement],
        *,
        output: CBlock | None = None,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        generate_logs: list[GenerateLog] | None = None,
        input: CBlock | None = None,
    ) -> list[ValidationResult]:
        """Validates a set of requirements over the output (if provided) or the current context (if the output is not provided)."""
        return mfuncs.validate(
            reqs=reqs,
            context=self.ctx,
            backend=self.backend,
            output=output,
            format=format,
            model_options=model_options,
            generate_logs=generate_logs,
            input=input,
        )

    def query(
        self,
        obj: Any,
        query: str,
        *,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> ModelOutputThunk:
        """Query method for retrieving information from an object.

        Args:
            obj : The object to be queried. It should be an instance of MObject or can be converted to one if necessary.
            query:  The string representing the query to be executed against the object.
            format:  format for output parsing.
            model_options: Model options to pass to the backend.
            tool_calls: If true, the model may make tool calls. Defaults to False.

        Returns:
            ModelOutputThunk: The result of the query as processed by the backend.
        """
        result, context = mfuncs.query(
            obj=obj,
            query=query,
            context=self.ctx,
            backend=self.backend,
            format=format,
            model_options=model_options,
            tool_calls=tool_calls,
        )
        self.ctx = context
        return result

    def transform(
        self,
        obj: Any,
        transformation: str,
        *,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
    ) -> ModelOutputThunk | Any:
        """Transform method for creating a new object with the transformation applied.

        Args:
            obj : The object to be queried. It should be an instance of MObject or can be converted to one if necessary.
            transformation:  The string representing the query to be executed against the object.
            format: format for output parsing; usually not needed with transform.
            model_options: Model options to pass to the backend.

        Returns:
            ModelOutputThunk|Any: The result of the transformation as processed by the backend. If no tools were called,
            the return type will be always be ModelOutputThunk. If a tool was called, the return type will be the return type
            of the function called, usually the type of the object passed in.
        """
        result, context = mfuncs.transform(
            obj=obj,
            transformation=transformation,
            context=self.ctx,
            backend=self.backend,
            format=format,
            model_options=model_options,
        )
        self.ctx = context
        return result

    @overload
    async def aact(
        self,
        action: Component,
        *,
        requirements: list[Requirement] | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: Literal[False] = False,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> ModelOutputThunk: ...

    @overload
    async def aact(
        self,
        action: Component,
        *,
        requirements: list[Requirement] | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: Literal[True],
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> SamplingResult: ...

    async def aact(
        self,
        action: Component,
        *,
        requirements: list[Requirement] | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: bool = False,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> ModelOutputThunk | SamplingResult:
        """Runs a generic action, and adds both the action and the result to the context.

        Args:
            action: the Component from which to generate.
            requirements: used as additional requirements when a sampling strategy is provided
            strategy: a SamplingStrategy that describes the strategy for validating and repairing/retrying for the instruct-validate-repair pattern. None means that no particular sampling strategy is used.
            return_sampling_results: attach the (successful and failed) sampling attempts to the results.
            format: if set, the BaseModel to use for constrained decoding.
            model_options: additional model options, which will upsert into the model/backend's defaults.
            tool_calls: if true, tool calling is enabled.

        Returns:
            A ModelOutputThunk if `return_sampling_results` is `False`, else returns a `SamplingResult`.
        """
        r = await mfuncs.aact(
            action,
            context=self.ctx,
            backend=self.backend,
            requirements=requirements,
            strategy=strategy,
            return_sampling_results=return_sampling_results,
            format=format,
            model_options=model_options,
            tool_calls=tool_calls,
        )  # type: ignore

        if isinstance(r, SamplingResult):
            self.ctx = r.result_ctx
            return r
        else:
            result, context = r
            self.ctx = context
            return result

    @overload
    async def ainstruct(
        self,
        description: str,
        *,
        images: list[ImageBlock] | list[PILImage.Image] | None = None,
        requirements: list[Requirement | str] | None = None,
        icl_examples: list[str | CBlock] | None = None,
        grounding_context: dict[str, str | CBlock | Component] | None = None,
        user_variables: dict[str, str] | None = None,
        prefix: str | CBlock | None = None,
        output_prefix: str | CBlock | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: Literal[False] = False,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> ModelOutputThunk: ...

    @overload
    async def ainstruct(
        self,
        description: str,
        *,
        images: list[ImageBlock] | list[PILImage.Image] | None = None,
        requirements: list[Requirement | str] | None = None,
        icl_examples: list[str | CBlock] | None = None,
        grounding_context: dict[str, str | CBlock | Component] | None = None,
        user_variables: dict[str, str] | None = None,
        prefix: str | CBlock | None = None,
        output_prefix: str | CBlock | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: Literal[True],
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> SamplingResult: ...

    async def ainstruct(
        self,
        description: str,
        *,
        images: list[ImageBlock] | list[PILImage.Image] | None = None,
        requirements: list[Requirement | str] | None = None,
        icl_examples: list[str | CBlock] | None = None,
        grounding_context: dict[str, str | CBlock | Component] | None = None,
        user_variables: dict[str, str] | None = None,
        prefix: str | CBlock | None = None,
        output_prefix: str | CBlock | None = None,
        strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
        return_sampling_results: bool = False,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> ModelOutputThunk | SamplingResult:
        """Generates from an instruction.

        Args:
            description: The description of the instruction.
            requirements: A list of requirements that the instruction can be validated against.
            icl_examples: A list of in-context-learning examples that the instruction can be validated against.
            grounding_context: A list of grounding contexts that the instruction can use. They can bind as variables using a (key: str, value: str | ContentBlock) tuple.
            user_variables: A dict of user-defined variables used to fill in Jinja placeholders in other parameters. This requires that all other provided parameters are provided as strings.
            prefix: A prefix string or ContentBlock to use when generating the instruction.
            output_prefix: A string or ContentBlock that defines a prefix for the output generation. Usually you do not need this.
            strategy: A SamplingStrategy that describes the strategy for validating and repairing/retrying for the instruct-validate-repair pattern. None means that no particular sampling strategy is used.
            return_sampling_results: attach the (successful and failed) sampling attempts to the results.
            format: If set, the BaseModel to use for constrained decoding.
            model_options: Additional model options, which will upsert into the model/backend's defaults.
            tool_calls: If true, tool calling is enabled.
            images: A list of images to be used in the instruction or None if none.
        """
        r = await mfuncs.ainstruct(
            description,
            context=self.ctx,
            backend=self.backend,
            images=images,
            requirements=requirements,
            icl_examples=icl_examples,
            grounding_context=grounding_context,
            user_variables=user_variables,
            prefix=prefix,
            output_prefix=output_prefix,
            strategy=strategy,
            return_sampling_results=return_sampling_results,  # type: ignore
            format=format,
            model_options=model_options,
            tool_calls=tool_calls,
        )

        if isinstance(r, SamplingResult):
            self.ctx = r.result_ctx
            return r
        else:
            # It's a tuple[ModelOutputThunk, Context].
            result, context = r
            self.ctx = context
            return result

    async def achat(
        self,
        content: str,
        role: Message.Role = "user",
        *,
        images: list[ImageBlock] | list[PILImage.Image] | None = None,
        user_variables: dict[str, str] | None = None,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> Message:
        """Sends a simple chat message and returns the response. Adds both messages to the Context."""
        result, context = await mfuncs.achat(
            content=content,
            context=self.ctx,
            backend=self.backend,
            role=role,
            images=images,
            user_variables=user_variables,
            format=format,
            model_options=model_options,
            tool_calls=tool_calls,
        )

        self.ctx = context
        return result

    async def avalidate(
        self,
        reqs: Requirement | list[Requirement],
        *,
        output: CBlock | None = None,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        generate_logs: list[GenerateLog] | None = None,
        input: CBlock | None = None,
    ) -> list[ValidationResult]:
        """Validates a set of requirements over the output (if provided) or the current context (if the output is not provided)."""
        return await mfuncs.avalidate(
            reqs=reqs,
            context=self.ctx,
            backend=self.backend,
            output=output,
            format=format,
            model_options=model_options,
            generate_logs=generate_logs,
            input=input,
        )

    async def aquery(
        self,
        obj: Any,
        query: str,
        *,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
        tool_calls: bool = False,
    ) -> ModelOutputThunk:
        """Query method for retrieving information from an object.

        Args:
            obj : The object to be queried. It should be an instance of MObject or can be converted to one if necessary.
            query:  The string representing the query to be executed against the object.
            format:  format for output parsing.
            model_options: Model options to pass to the backend.
            tool_calls: If true, the model may make tool calls. Defaults to False.

        Returns:
            ModelOutputThunk: The result of the query as processed by the backend.
        """
        result, context = await mfuncs.aquery(
            obj=obj,
            query=query,
            context=self.ctx,
            backend=self.backend,
            format=format,
            model_options=model_options,
            tool_calls=tool_calls,
        )
        self.ctx = context
        return result

    async def atransform(
        self,
        obj: Any,
        transformation: str,
        *,
        format: type[BaseModelSubclass] | None = None,
        model_options: dict | None = None,
    ) -> ModelOutputThunk | Any:
        """Transform method for creating a new object with the transformation applied.

        Args:
            obj: The object to be queried. It should be an instance of MObject or can be converted to one if necessary.
            transformation:  The string representing the query to be executed against the object.
            format: format for output parsing; usually not needed with transform.
            model_options: Model options to pass to the backend.

        Returns:
            ModelOutputThunk|Any: The result of the transformation as processed by the backend. If no tools were called,
            the return type will be always be ModelOutputThunk. If a tool was called, the return type will be the return type
            of the function called, usually the type of the object passed in.
        """
        result, context = await mfuncs.atransform(
            obj=obj,
            transformation=transformation,
            context=self.ctx,
            backend=self.backend,
            format=format,
            model_options=model_options,
        )
        self.ctx = context
        return result

    # ###############################
    #  Convenience functions
    # ###############################
    def last_prompt(self) -> str | list[dict] | None:
        """Returns the last prompt that has been called from the session context.

        Returns:
            A string if the last prompt was a raw call to the model OR a list of messages (as role-msg-dicts). Is None if none could be found.
        """
        op = self.ctx.last_output()
        if op is None:
            return None
        log = op._generate_log
        if isinstance(log, GenerateLog):
            return log.prompt
        elif isinstance(log, list):
            last_el = log[-1]
            if isinstance(last_el, GenerateLog):
                return last_el.prompt
        return None
