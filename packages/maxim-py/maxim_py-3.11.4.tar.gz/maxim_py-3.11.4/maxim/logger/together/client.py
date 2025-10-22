"""Together AI API instrumentation for Maxim logging.

This module provides instrumentation for the Together AI SDK to integrate with Maxim's
logging and monitoring capabilities. It patches the Together AI client methods to
automatically track API calls, model parameters, and responses.

The instrumentation supports both synchronous and asynchronous chat completions,
streaming responses, and various model parameters specific to Together AI.
"""

import functools
from typing import Any, Optional
from uuid import uuid4
from together.resources.chat import AsyncChatCompletions, ChatCompletions
from ..logger import Generation, Logger, Trace, GenerationConfigDict
from .utils import TogetherUtils
from .helpers import TogetherHelpers
from ...scribe import scribe


_INSTRUMENTED = False

def instrument_together(logger: Logger) -> None:
    """Patch Together AI's chat completion methods for Maxim logging.
    
    This function instruments the Together AI SDK by patching the chat completion
    methods to automatically log API calls, model parameters, and responses to
    Maxim. It supports both synchronous and asynchronous operations, streaming
    responses, and various Together AI specific features.
    
    The instrumentation is designed to be non-intrusive and maintains the original
    API behavior while adding comprehensive logging capabilities.
    
    Args:
        logger (Logger): The Maxim logger instance to use for tracking and
            logging API interactions. This logger will be used to create
            traces and generations for each API call.
    """

    global _INSTRUMENTED
    if _INSTRUMENTED:
        scribe().debug("[MaximSDK] Together already instrumented")
        return

    def wrap_sync_create(create_func):
        """Wrapper for synchronous chat completion create method.
        
        This wrapper function intercepts synchronous chat completion requests
        to Together AI and adds comprehensive logging capabilities while
        preserving the original API behavior.
        
        Args:
            create_func: The original Together AI chat completion create method
                to be wrapped with logging capabilities.
        
        Returns:
            Wrapped function that provides the same interface as the original
            but with added Maxim logging and monitoring.
        """

        @functools.wraps(create_func)
        def wrapper(self: ChatCompletions, *args: Any, **kwargs: Any):
            # Extract Maxim-specific headers for trace and generation configuration
            extra_headers = kwargs.get("extra_headers", None)
            trace_id = None
            generation_name = None
            generation_tags = None
            trace_tags = None

            if extra_headers is not None:
                trace_id = extra_headers.get("x-maxim-trace-id", None)
                generation_name = extra_headers.get("x-maxim-generation-name", None)
                generation_tags = extra_headers.get("x-maxim-generation-tags", None)
                trace_tags = extra_headers.get("x-maxim-trace-tags", None)

            # Determine if we need to create a new trace or use existing one
            is_local_trace = trace_id is None
            model = kwargs.get("model", None)
            final_trace_id = trace_id or str(uuid4())
            generation: Optional[Generation] = None
            trace: Optional[Trace] = None
            messages = kwargs.get("messages", None)
            is_streaming = kwargs.get("stream", False)

            # Initialize trace and generation for logging
            try:
                trace = logger.trace({"id": final_trace_id})
                gen_config = GenerationConfigDict(
                    id=str(uuid4()),
                    model=model or "",
                    provider="together",
                    name=generation_name,
                    model_parameters=TogetherUtils.get_model_params(**kwargs),
                    messages=TogetherUtils.parse_message_param(messages or []),
                )
                generation = trace.generation(gen_config)

                # Check for image URLs in messages and add as attachments
                TogetherUtils.add_image_attachments_from_messages(generation, messages or [])

            except Exception as e:
                if generation is not None:
                    generation.error({"message": str(e)})
                scribe().warning(
                    f"[MaximSDK][TogetherInstrumentation] Error in generating content: {e}",
                )

            # Remove extra_headers from kwargs before sending to Together AI
            clean_kwargs = {k: v for k, v in kwargs.items() if k != "extra_headers"}
            try:
                response = create_func(self, *args, **clean_kwargs)
            except Exception as e:
                if generation is not None:
                    generation.error({"message": str(e)})
                scribe().warning(
                    f"[MaximSDK][TogetherInstrumentation] Error in generating content: {e}",
                )
                raise

            # Process response and log results
            try:
                if generation is not None:
                    if is_streaming:
                        response = TogetherHelpers.sync_stream_helper(response, generation, trace, is_local_trace)
                    else:
                        generation.result(TogetherUtils.parse_completion(response))
                        if is_local_trace and trace is not None:
                            if response.choices and len(response.choices) > 0:
                                trace.set_output(response.choices[0].message.content or "")
                            else:
                                trace.set_output("")
                            trace.end()
            except Exception as e:
                if generation is not None:
                    generation.error({"message": str(e)})
                scribe().warning(
                    f"[MaximSDK][TogetherInstrumentation] Error in logging generation: {e}",
                )

            # Apply tags if provided
            if generation_tags is not None and generation is not None:
                for key, value in generation_tags.items():
                    generation.add_tag(key, value)
            if trace_tags is not None and trace is not None:
                for key, value in trace_tags.items():
                    trace.add_tag(key, value)

            return response

        return wrapper

    def wrap_async_create(create_func):
        """Wrapper for asynchronous chat completion create method.
        
        This wrapper function intercepts asynchronous chat completion requests
        to Together AI and adds comprehensive logging capabilities while
        preserving the original API behavior and async semantics.
        
        Args:
            create_func: The original Together AI async chat completion create method
                to be wrapped with logging capabilities.
        
        Returns:
            Wrapped async function that provides the same interface as the original
            but with added Maxim logging and monitoring.
        """

        @functools.wraps(create_func)
        async def wrapper(self: AsyncChatCompletions, *args: Any, **kwargs: Any):
            # Extract Maxim-specific headers for trace and generation configuration
            extra_headers = kwargs.get("extra_headers", None)
            trace_id = None
            generation_name = None
            generation_tags = None
            trace_tags = None

            if extra_headers is not None:
                trace_id = extra_headers.get("x-maxim-trace-id", None)
                generation_name = extra_headers.get("x-maxim-generation-name", None)
                generation_tags = extra_headers.get("x-maxim-generation-tags", None)
                trace_tags = extra_headers.get("x-maxim-trace-tags", None)

            # Determine if we need to create a new trace or use existing one
            is_local_trace = trace_id is None
            model = kwargs.get("model", None)
            final_trace_id = trace_id or str(uuid4())
            generation: Optional[Generation] = None
            trace: Optional[Trace] = None
            messages = kwargs.get("messages", None)
            is_streaming = kwargs.get("stream", False)

            # Initialize trace and generation for logging
            try:
                trace = logger.trace({"id": final_trace_id})
                gen_config = GenerationConfigDict(
                    id=str(uuid4()),
                    model=model or "",
                    provider="together",
                    name=generation_name,
                    model_parameters=TogetherUtils.get_model_params(**kwargs),
                    messages=TogetherUtils.parse_message_param(messages or []),
                )
                generation = trace.generation(gen_config)

                # Check for image URLs in messages and add as attachments
                TogetherUtils.add_image_attachments_from_messages(generation, messages or [])

            except Exception as e:
                if generation is not None:
                    generation.error({"message": str(e)})
                scribe().warning(
                    f"[MaximSDK][TogetherInstrumentation] Error in generating content: {e}",
                )

            # Remove extra_headers from kwargs before sending to Together AI
            clean_kwargs = {k: v for k, v in kwargs.items() if k != "extra_headers"}
            try:
                response = await create_func(self, *args, **clean_kwargs)
            except Exception as e:
                if generation is not None:
                    generation.error({"message": str(e)})
                scribe().warning(
                    f"[MaximSDK][TogetherInstrumentation] Error in generating content: {e}",
                )
                raise

            # Process response and log results
            try:
                if generation is not None: 
                    if is_streaming:
                        response = TogetherHelpers.async_stream_helper(response, generation, trace, is_local_trace)
                    else:
                        generation.result(TogetherUtils.parse_completion(response))
                        if is_local_trace and trace is not None:
                            if response.choices and len(response.choices) > 0:
                                trace.set_output(response.choices[0].message.content or "")
                            else:
                                trace.set_output("")
                            trace.end()
            except Exception as e:
                if generation is not None:
                    generation.error({"message": str(e)})
                scribe().warning(
                    f"[MaximSDK][TogetherInstrumentation] Error in logging generation: {e}",
                )

            # Apply tags if provided
            if generation_tags is not None and generation is not None:
                for key, value in generation_tags.items():
                    generation.add_tag(key, value)
            if trace_tags is not None and trace is not None:
                for key, value in trace_tags.items():
                    trace.add_tag(key, value)

            return response

        return wrapper

    # Apply the patches to both sync and async chat completion methods
    ChatCompletions.create = wrap_sync_create(ChatCompletions.create)
    AsyncChatCompletions.create = wrap_async_create(AsyncChatCompletions.create)
    _INSTRUMENTED = True
