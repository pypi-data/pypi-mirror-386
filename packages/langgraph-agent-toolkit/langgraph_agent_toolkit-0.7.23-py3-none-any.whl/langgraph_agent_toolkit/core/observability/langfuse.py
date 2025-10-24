import hashlib
import json
from typing import Any, Dict, Literal, Optional, Tuple, Union

from langfuse import Langfuse

from langgraph_agent_toolkit.core.observability.base import BaseObservabilityPlatform
from langgraph_agent_toolkit.core.observability.types import PromptReturnType, PromptTemplateType
from langgraph_agent_toolkit.helper.constants import DEFAULT_CACHE_TTL_SECOND
from langgraph_agent_toolkit.helper.logging import logger


try:
    from langfuse.callback import CallbackHandler
except (ModuleNotFoundError, ImportError):
    # New langfuse version uses langfuse.langchain.CallbackHandler
    from langfuse.langchain import CallbackHandler


class LangfuseObservability(BaseObservabilityPlatform):
    """Langfuse implementation of observability platform."""

    def __init__(self, prompts_dir: Optional[str] = None, remote_first: bool = False):
        super().__init__(prompts_dir, remote_first)
        self.required_vars = ["LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_HOST"]

    @BaseObservabilityPlatform.requires_env_vars
    def get_callback_handler(self, **kwargs) -> CallbackHandler:
        return CallbackHandler(**kwargs)

    def before_shutdown(self) -> None:
        Langfuse().flush()

    @BaseObservabilityPlatform.requires_env_vars
    def record_feedback(self, run_id: str, key: str, score: float, **kwargs) -> None:
        Langfuse().score(
            trace_id=run_id,
            name=key,
            value=score,
            **kwargs,
        )

    def _compute_prompt_hash(self, prompt_template: PromptTemplateType) -> str:
        """Compute a hash of the prompt content to detect changes."""
        if isinstance(prompt_template, str):
            content_to_hash = prompt_template
        elif isinstance(prompt_template, list):
            content_to_hash = json.dumps(prompt_template, sort_keys=True)
        else:
            content_to_hash = str(prompt_template)

        return hashlib.md5(content_to_hash.encode("utf-8")).hexdigest()

    @BaseObservabilityPlatform.requires_env_vars
    def push_prompt(
        self,
        name: str,
        prompt_template: PromptTemplateType,
        metadata: Optional[Dict[str, Any]] = None,
        force_create_new_version: bool = True,
    ) -> None:
        langfuse = Langfuse()
        labels = metadata.get("labels", ["production"]) if metadata else ["production"]

        # Check if remote_first is enabled
        if self.remote_first:
            # When remote_first=True, prioritize remote prompts
            try:
                existing_remote_prompt = langfuse.get_prompt(name=name)
                if existing_remote_prompt:
                    logger.debug(f"Remote-first mode: Using existing remote prompt '{name}'")
                    # Store the remote prompt locally as well
                    full_metadata = metadata.copy() if metadata else {}
                    full_metadata["langfuse_prompt"] = existing_remote_prompt
                    full_metadata["original_prompt"] = self._convert_to_chat_prompt(prompt_template)
                    super().push_prompt(name, prompt_template, full_metadata, force_create_new_version)
                    return
            except Exception:
                logger.debug(f"Remote-first mode: Remote prompt '{name}' not found, will create new one")

        # Generate hash for the current prompt
        prompt_hash = self._compute_prompt_hash(prompt_template)

        # Handle existing prompt versions - custom implementation for Langfuse
        existing_prompt = None
        content_changed = True

        try:
            existing_prompt = langfuse.get_prompt(name=name)

            # Check if content has changed by comparing hashes
            # First try commit_message, then fall back to tags
            existing_hash = None
            if hasattr(existing_prompt, "commit_message") and existing_prompt.commit_message:
                existing_hash = existing_prompt.commit_message
            elif hasattr(existing_prompt, "tags") and existing_prompt.tags and len(existing_prompt.tags) > 0:
                # Use the first tag as the hash (assuming it contains the prompt hash)
                existing_hash = existing_prompt.tags[0]

            if existing_hash and existing_hash == prompt_hash:
                content_changed = False
                logger.debug(f"Prompt '{name}' content unchanged (hash: {existing_hash})")
            else:
                logger.debug(
                    f"Prompt '{name}' content changed from previous version (old: {existing_hash}, new: {prompt_hash})"
                )
        except Exception:
            logger.debug(f"Existing prompt '{name}' not found, will create a new one")

        prompt_obj = self._convert_to_chat_prompt(prompt_template)
        type_prompt = "text" if isinstance(prompt_template, str) else "chat"

        create_new = (
            # When force_create_new_version=True, always create a new version
            force_create_new_version
            or
            # When no existing prompt, create a new one
            existing_prompt is None
            or
            # When content has changed and we're not forcing to keep the old version
            content_changed
        )

        if create_new:
            langfuse_prompt = langfuse.create_prompt(
                name=name,
                prompt=prompt_template,
                labels=labels,
                type=type_prompt,
                tags=[prompt_hash],  # for v2 version
                commit_message=prompt_hash,  # Store hash in commit_message
            )
            if existing_prompt is None:
                logger.debug(f"Created new prompt '{name}' as it didn't exist before")
            elif content_changed:
                logger.debug(f"Created new prompt version '{name}' because content changed (hash: {prompt_hash})")
            else:
                logger.debug(f"Created new prompt version '{name}' because force_create_new_version=True")
        else:
            # Content unchanged and not forcing new version
            langfuse_prompt = existing_prompt
            logger.debug(f"Reusing existing prompt '{name}' as content is unchanged and force_create_new_version=False")

        full_metadata = metadata.copy() if metadata else {}
        full_metadata["langfuse_prompt"] = langfuse_prompt
        full_metadata["original_prompt"] = prompt_obj

        super().push_prompt(name, prompt_template, full_metadata, force_create_new_version)

    @BaseObservabilityPlatform.requires_env_vars
    def pull_prompt(
        self,
        name: str,
        return_with_prompt_object: bool = False,
        cache_ttl_seconds: Optional[int] = DEFAULT_CACHE_TTL_SECOND,
        template_format: Literal["f-string", "mustache", "jinja2"] = "f-string",
        label: Optional[str] = None,
        version: Optional[int] = None,
        **kwargs,
    ) -> Union[PromptReturnType, Tuple[PromptReturnType, Any]]:
        try:
            langfuse = Langfuse()
            get_prompt_kwargs = {"name": name, "cache_ttl_seconds": cache_ttl_seconds}

            if label:
                get_prompt_kwargs["label"] = label
            elif kwargs.get("prompt_label"):
                get_prompt_kwargs["label"] = kwargs.get("prompt_label")

            if version is not None:
                get_prompt_kwargs["version"] = version
            elif kwargs.get("prompt_version"):
                get_prompt_kwargs["version"] = kwargs.get("prompt_version")

            try:
                langfuse_prompt = langfuse.get_prompt(**get_prompt_kwargs)
            except Exception as e:
                logger.debug(f"Prompt not found with parameters: {e}")
                langfuse_prompt = langfuse.get_prompt(name=name, cache_ttl_seconds=cache_ttl_seconds)

            # Process the prompt object using the base class helper
            prompt = self._process_prompt_object(langfuse_prompt.prompt, template_format=template_format)

            return (prompt, langfuse_prompt) if return_with_prompt_object else prompt

        except Exception as e:
            logger.warning(f"Failed to pull prompt from Langfuse: {e}")
            local_prompt = super().pull_prompt(name, template_format=template_format, **kwargs)
            return (local_prompt, None) if return_with_prompt_object else local_prompt

    @BaseObservabilityPlatform.requires_env_vars
    def delete_prompt(self, name: str) -> None:
        logger.warning(f"Skipping deletion of prompt '{name}' from Langfuse")
        super().delete_prompt(name)
