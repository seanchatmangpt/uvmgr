
# uvmgr External Project Testing Report

## Summary
- **Overall Success**: ❌ FAIL
- **Success Rate**: 78.6%
- **8020 Threshold**: ❌ NOT MET

## Statistics
- **Total Projects**: 5
- **Successful Projects**: 2
- **Total Tests**: 14
- **Tests Passed**: 11

## Project Results

### minimal-python (minimal) - ❌ FAIL
- **Tests Run**: 4
- **Tests Passed**: 3
- **Success Rate**: 75.0%

### fastapi-app (fastapi) - ✅ PASS
- **Tests Run**: 5
- **Tests Passed**: 4
- **Success Rate**: 80.0%

### cli-tool (cli) - ✅ PASS
- **Tests Run**: 5
- **Tests Passed**: 4
- **Success Rate**: 80.0%

### data-science (data_science) - ❌ FAIL
- **Tests Run**: 0
- **Tests Passed**: 0
- **Success Rate**: 0.0%
- **Error**: uvmgr installation failed: Using CPython 3.13.0
Creating virtual environment at: .venv
warning: No `requires-python` value found in the workspace. Defaulting to `>=3.13`.
Resolved 207 packages in 29ms
   Building datascience-external-test @ file:///Users/sac/dev/uvmgr/external-project-testing/workspace/data-science
   Building uvmgr @ file:///Users/sac/dev/uvmgr
      Built datascience-external-test @ file:///Users/sac/dev/uvmgr/external-project-testing/workspace/data-science
      Built uvmgr @ file:///Users/sac/dev/uvmgr
Prepared 2 packages in 271ms
Installed 125 packages in 449ms
 + aiohappyeyeballs==2.6.1
 + aiohttp==3.12.13
 + aiosignal==1.3.2
 + alembic==1.16.2
 + annotated-types==0.7.0
 + anyio==4.9.0
 + apscheduler==3.11.0
 + asyncer==0.0.8
 + attrs==25.3.0
 + authlib==1.6.0
 + backoff==2.2.1
 + cachetools==6.1.0
 + certifi==2025.6.15
 + cffi==1.17.1
 + charset-normalizer==3.4.2
 + click==8.2.1
 + cloudpickle==3.1.1
 + colorlog==6.9.0
 + contourpy==1.3.2
 + cryptography==45.0.4
 + cycler==0.12.1
 + datascience-external-test==0.1.0 (from file:///Users/sac/dev/uvmgr/external-project-testing/workspace/data-science)
 + datasets==3.6.0
 + dill==0.3.8
 + diskcache==5.6.3
 + distro==1.9.0
 + dspy==2.6.27
 + ember-ai==0.0.1
 + exceptiongroup==1.3.0
 + fastapi==0.115.14
 + fastmcp==2.9.2
 + filelock==3.18.0
 + fonttools==4.58.4
 + frozenlist==1.7.0
 + fsspec==2025.3.0
 + h11==0.16.0
 + hf-xet==1.1.5
 + httpcore==1.0.9
 + httpx==0.28.1
 + httpx-sse==0.4.1
 + huggingface-hub==0.33.1
 + idna==3.10
 + importlib-metadata==8.7.0
 + iniconfig==2.1.0
 + jaraco-classes==3.4.0
 + jaraco-context==6.0.1
 + jaraco-functools==4.2.1
 + jinja2==3.1.6
 + jiter==0.10.0
 + joblib==1.5.1
 + json-repair==0.47.4
 + jsonschema==4.24.0
 + jsonschema-specifications==2025.4.1
 + keyring==25.6.0
 + kiwisolver==1.4.8
 + litellm==1.73.2
 + lxml==6.0.0
 + magicattr==0.1.6
 + mako==1.3.10
 + markdown-it-py==3.0.0
 + markupsafe==3.0.2
 + matplotlib==3.10.3
 + mcp==1.9.4
 + mdurl==0.1.2
 + more-itertools==10.7.0
 + multidict==6.6.2
 + multiprocess==0.70.16
 + numpy==2.3.1
 + openai==1.93.0
 + openapi-pydantic==0.5.1
 + opentelemetry-api==1.34.1
 + opentelemetry-sdk==1.34.1
 + opentelemetry-semantic-conventions==0.55b1
 + optuna==4.4.0
 + packaging==25.0
 + pandas==2.3.0
 + pastel==0.2.1
 + pillow==11.2.1
 + pluggy==1.6.0
 + poethepoet==0.35.0
 + propcache==0.3.2
 + pyarrow==20.0.0
 + pycparser==2.22
 + pydantic==2.11.7
 + pydantic-core==2.33.2
 + pydantic-settings==2.10.1
 + pygments==2.19.2
 + pyparsing==3.2.3
 + pyperclip==1.9.0
 + pytest==8.4.1
 + python-dateutil==2.9.0.post0
 + python-dotenv==1.1.1
 + python-multipart==0.0.20
 + pytz==2025.2
 + pyyaml==6.0.2
 + referencing==0.36.2
 + regex==2024.11.6
 + requests==2.32.4
 + rich==14.0.0
 + rpds-py==0.25.1
 + ruff==0.12.1
 + shellingham==1.5.4
 + six==1.17.0
 + sniffio==1.3.1
 + spiffworkflow==3.1.1
 + sqlalchemy==2.0.41
 + sse-starlette==2.3.6
 + starlette==0.46.2
 + tenacity==9.1.2
 + tiktoken==0.9.0
 + tokenizers==0.21.2
 + tqdm==4.67.1
 + typer==0.16.0
 + typing-extensions==4.14.0
 + typing-inspection==0.4.1
 + tzdata==2025.2
 + tzlocal==5.3.1
 + ujson==5.10.0
 + urllib3==2.5.0
 + uvicorn==0.35.0
 + uvmgr==0.0.0 (from file:///Users/sac/dev/uvmgr)
 + xxhash==3.5.0
 + yarl==1.20.1
 + zipp==3.23.0
 + zstandard==0.23.0
warning: No `requires-python` value found in the workspace. Defaulting to `>=3.13`.
Resolved 208 packages in 37ms
   Building datascience-external-test @ file:///Users/sac/dev/uvmgr/external-project-testing/workspace/data-science
      Built datascience-external-test @ file:///Users/sac/dev/uvmgr/external-project-testing/workspace/data-science
Prepared 1 package in 210ms
Uninstalled 1 package in 0.68ms
Installed 4 packages in 3ms
 + coverage==7.9.1
 ~ datascience-external-test==0.1.0 (from file:///Users/sac/dev/uvmgr/external-project-testing/workspace/data-science)
 + pytest-cov==6.2.1
 + pytest-mock==3.14.1


### substrate-template (substrate) - ❌ FAIL
- **Tests Run**: 0
- **Tests Passed**: 0
- **Success Rate**: 0.0%
- **Error**: uvmgr installation failed: Using CPython 3.13.0
Creating virtual environment at: .venv
warning: No `requires-python` value found in the workspace. Defaulting to `>=3.13`.
Resolved 128 packages in 25ms
   Building uvmgr @ file:///Users/sac/dev/uvmgr
   Building substrate-external-test @ file:///Users/sac/dev/uvmgr/external-project-testing/workspace/substrate-template
      Built substrate-external-test @ file:///Users/sac/dev/uvmgr/external-project-testing/workspace/substrate-template
      Built uvmgr @ file:///Users/sac/dev/uvmgr
Prepared 2 packages in 327ms
Installed 118 packages in 450ms
 + aiohappyeyeballs==2.6.1
 + aiohttp==3.12.13
 + aiosignal==1.3.2
 + alembic==1.16.2
 + annotated-types==0.7.0
 + anyio==4.9.0
 + apscheduler==3.11.0
 + asyncer==0.0.8
 + attrs==25.3.0
 + authlib==1.6.0
 + backoff==2.2.1
 + cachetools==6.1.0
 + certifi==2025.6.15
 + cffi==1.17.1
 + charset-normalizer==3.4.2
 + click==8.2.1
 + cloudpickle==3.1.1
 + colorlog==6.9.0
 + cryptography==45.0.4
 + datasets==3.6.0
 + dill==0.3.8
 + diskcache==5.6.3
 + distro==1.9.0
 + dspy==2.6.27
 + ember-ai==0.0.1
 + exceptiongroup==1.3.0
 + fastapi==0.115.14
 + fastmcp==2.9.2
 + filelock==3.18.0
 + frozenlist==1.7.0
 + fsspec==2025.3.0
 + h11==0.16.0
 + hf-xet==1.1.5
 + httpcore==1.0.9
 + httpx==0.28.1
 + httpx-sse==0.4.1
 + huggingface-hub==0.33.1
 + idna==3.10
 + importlib-metadata==8.7.0
 + iniconfig==2.1.0
 + jaraco-classes==3.4.0
 + jaraco-context==6.0.1
 + jaraco-functools==4.2.1
 + jinja2==3.1.6
 + jiter==0.10.0
 + joblib==1.5.1
 + json-repair==0.47.4
 + jsonschema==4.24.0
 + jsonschema-specifications==2025.4.1
 + keyring==25.6.0
 + litellm==1.73.2
 + lxml==6.0.0
 + magicattr==0.1.6
 + mako==1.3.10
 + markdown-it-py==3.0.0
 + markupsafe==3.0.2
 + mcp==1.9.4
 + mdurl==0.1.2
 + more-itertools==10.7.0
 + multidict==6.6.2
 + multiprocess==0.70.16
 + numpy==2.3.1
 + openai==1.93.0
 + openapi-pydantic==0.5.1
 + opentelemetry-api==1.34.1
 + opentelemetry-sdk==1.34.1
 + opentelemetry-semantic-conventions==0.55b1
 + optuna==4.4.0
 + packaging==25.0
 + pandas==2.3.0
 + pastel==0.2.1
 + pluggy==1.6.0
 + poethepoet==0.35.0
 + propcache==0.3.2
 + pyarrow==20.0.0
 + pycparser==2.22
 + pydantic==2.11.7
 + pydantic-core==2.33.2
 + pydantic-settings==2.10.1
 + pygments==2.19.2
 + pyperclip==1.9.0
 + pytest==8.4.1
 + python-dateutil==2.9.0.post0
 + python-dotenv==1.1.1
 + python-multipart==0.0.20
 + pytz==2025.2
 + pyyaml==6.0.2
 + referencing==0.36.2
 + regex==2024.11.6
 + requests==2.32.4
 + rich==14.0.0
 + rpds-py==0.25.1
 + ruff==0.12.1
 + shellingham==1.5.4
 + six==1.17.0
 + sniffio==1.3.1
 + spiffworkflow==3.1.1
 + sqlalchemy==2.0.41
 + sse-starlette==2.3.6
 + starlette==0.46.2
 + substrate-external-test==0.1.0 (from file:///Users/sac/dev/uvmgr/external-project-testing/workspace/substrate-template)
 + tenacity==9.1.2
 + tiktoken==0.9.0
 + tokenizers==0.21.2
 + tqdm==4.67.1
 + typer==0.16.0
 + typing-extensions==4.14.0
 + typing-inspection==0.4.1
 + tzdata==2025.2
 + tzlocal==5.3.1
 + ujson==5.10.0
 + urllib3==2.5.0
 + uvicorn==0.35.0
 + uvmgr==0.0.0 (from file:///Users/sac/dev/uvmgr)
 + xxhash==3.5.0
 + yarl==1.20.1
 + zipp==3.23.0
 + zstandard==0.23.0
warning: No `requires-python` value found in the workspace. Defaulting to `>=3.13`.
Resolved 129 packages in 22ms
   Building substrate-external-test @ file:///Users/sac/dev/uvmgr/external-project-testing/workspace/substrate-template
      Built substrate-external-test @ file:///Users/sac/dev/uvmgr/external-project-testing/workspace/substrate-template
Prepared 1 package in 300ms
Uninstalled 1 package in 1ms
Installed 4 packages in 9ms
 + coverage==7.9.1
 + pytest-cov==6.2.1
 + pytest-mock==3.14.1
 ~ substrate-external-test==0.1.0 (from file:///Users/sac/dev/uvmgr/external-project-testing/workspace/substrate-template)



## Conclusion

The external project testing FAILED the 8020 validation criteria.
uvmgr has issues integrating with external Python projects.

---
Generated by uvmgr External Project Tester
