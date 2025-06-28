"""
uvmgr.ops.ai – orchestration wrapper around runtime.ai.
Returns JSON-safe data for the CLI layer.
"""

from __future__ import annotations

from pathlib import Path
import time

from uvmgr.core.fs import safe_write
from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span
from uvmgr.core.metrics import ai_metrics, OperationResult
from uvmgr.core.semconv import AIAttributes
from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.runtime import ai as _rt


@timed
def ask(model: str, prompt: str) -> str:
    start_time = time.time()
    
    with span("ops.ai.ask", model=model):
        add_span_attributes(**{
            AIAttributes.MODEL: model,
            AIAttributes.PROVIDER: model.split("/")[0] if "/" in model else "unknown",
            AIAttributes.OPERATION: "ask",
            "ai.prompt_length": len(prompt),
            "ai.prompt_words": len(prompt.split()),
        })
        add_span_event("ai.ask.started", {
            "model": model,
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt
        })
        
        try:
            response = _rt.ask(model, prompt)
            
            # Record successful AI operation metrics
            duration = time.time() - start_time
            result = OperationResult(success=True, duration=duration, metadata={
                "model": model,
                "provider": model.split("/")[0] if "/" in model else "unknown",
                "input_tokens": len(prompt.split()),  # Rough estimate
                "output_tokens": len(response.split()),  # Rough estimate
                "cost": 0.0  # Could be calculated based on model pricing
            })
            ai_metrics.record_completion(
                model=model,
                provider=model.split("/")[0] if "/" in model else "unknown",
                input_tokens=len(prompt.split()),
                output_tokens=len(response.split()),
                cost=0.0,
                result=result
            )
            
            add_span_attributes(**{
                "ai.response_length": len(response),
                "ai.response_words": len(response.split()),
            })
            add_span_event("ai.ask.completed", {
                "response_length": len(response),
                "success": True
            })
            
            return response
            
        except Exception as e:
            # Record failed AI operation metrics
            duration = time.time() - start_time
            result = OperationResult(success=False, duration=duration, error=e, metadata={
                "model": model,
                "provider": model.split("/")[0] if "/" in model else "unknown",
            })
            ai_metrics.record_completion(
                model=model,
                provider=model.split("/")[0] if "/" in model else "unknown",
                input_tokens=len(prompt.split()),
                output_tokens=0,
                cost=0.0,
                result=result
            )
            
            add_span_event("ai.ask.failed", {"error": str(e), "model": model})
            raise


@timed
def plan(model: str, topic: str, outfile: Path | None = None) -> str:
    start_time = time.time()
    
    with span("ops.ai.plan", model=model, topic=topic):
        add_span_attributes(**{
            AIAttributes.MODEL: model,
            AIAttributes.PROVIDER: model.split("/")[0] if "/" in model else "unknown",
            AIAttributes.OPERATION: "plan",
            "ai.topic": topic,
            "ai.has_output_file": outfile is not None,
        })
        add_span_event("ai.plan.started", {
            "model": model,
            "topic": topic,
            "output_file": str(outfile) if outfile else None
        })
        
        try:
            steps = _rt.outline(model, topic)
            md = "# " + topic + "\n\n" + "\n".join(f"- {s}" for s in steps) + "\n"
            
            if outfile:
                safe_write(outfile, md)
                add_span_event("ai.plan.file_saved", {"path": str(outfile), "size": len(md)})
            
            # Record successful AI operation metrics
            duration = time.time() - start_time
            result = OperationResult(success=True, duration=duration, metadata={
                "model": model,
                "provider": model.split("/")[0] if "/" in model else "unknown",
                "steps_count": len(steps),
                "output_length": len(md),
            })
            ai_metrics.record_completion(
                model=model,
                provider=model.split("/")[0] if "/" in model else "unknown",
                input_tokens=len(topic.split()),
                output_tokens=len(md.split()),
                cost=0.0,
                result=result
            )
            
            add_span_attributes(**{
                "ai.steps_generated": len(steps),
                "ai.plan_length": len(md),
            })
            add_span_event("ai.plan.completed", {
                "steps_count": len(steps),
                "plan_length": len(md),
                "success": True
            })
            
            return md
            
        except Exception as e:
            # Record failed AI operation metrics
            duration = time.time() - start_time
            result = OperationResult(success=False, duration=duration, error=e, metadata={
                "model": model,
                "provider": model.split("/")[0] if "/" in model else "unknown",
            })
            ai_metrics.record_completion(
                model=model,
                provider=model.split("/")[0] if "/" in model else "unknown",
                input_tokens=len(topic.split()),
                output_tokens=0,
                cost=0.0,
                result=result
            )
            
            add_span_event("ai.plan.failed", {"error": str(e), "model": model})
            raise


@timed
def fix_tests(model: str, out_patch: Path = Path("fix.patch")) -> str:
    diff = _rt.fix_tests(model)
    if diff:
        safe_write(out_patch, diff)
    return diff


@timed
def list_models() -> list[str]:
    """List all available Ollama models."""
    with span("ops.ai.list_models"):
        add_span_attributes(**{
            AIAttributes.PROVIDER: "ollama",
            AIAttributes.OPERATION: "list_models",
        })
        add_span_event("ai.list_models.started")
        
        try:
            models = _rt.list_ollama_models()
            
            add_span_attributes(**{"ai.models_count": len(models)})
            add_span_event("ai.list_models.completed", {
                "models_count": len(models),
                "models": models[:5] if models else []  # First 5 models
            })
            
            return models
            
        except Exception as e:
            add_span_event("ai.list_models.failed", {"error": str(e)})
            raise


@timed
def delete_model(model: str) -> bool:
    """Delete an Ollama model. Returns True if successful, False otherwise."""
    return _rt.delete_ollama_model(model)
