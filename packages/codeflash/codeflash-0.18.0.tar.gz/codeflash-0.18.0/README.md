![Codeflash-banner](https://i.postimg.cc/GmPRC52t/Codeflash-banner.png)
<p align="center">
   <a href="https://github.com/codeflash-ai/codeflash">
    <img src="https://img.shields.io/github/commit-activity/m/codeflash-ai/codeflash" alt="GitHub commit activity">
  </a>
  <a href="https://pypi.org/project/codeflash/"><img src="https://static.pepy.tech/badge/codeflash" alt="PyPI Downloads"></a>
  <a href="https://pypi.org/project/codeflash/">
    <img src="https://img.shields.io/pypi/v/codeflash?label=PyPI%20version" alt="PyPI Downloads">
  </a>
</p>

[Codeflash](https://www.codeflash.ai) is a general purpose optimizer for Python that helps you improve the performance of your Python code while maintaining its correctness.
It uses advanced LLMs to generate multiple optimization ideas for your code, tests them to be correct and benchmarks them for performance. It then creates merge-ready pull requests containing the best optimization found, which you can review and merge.

How to use Codeflash -
- Optimize an entire existing codebase by running `codeflash --all`
- Automate optimizing all __future__ code you will write by installing Codeflash as a GitHub action.
- Optimize a Python workflow `python myscript.py` end-to-end by running `codeflash optimize myscript.py`

Codeflash is used by top engineering teams at **Pydantic** [(PRs Merged)](https://github.com/pydantic/pydantic/pulls?q=is%3Apr+author%3Amisrasaurabh1+is%3Amerged), **Roboflow** [(PRs Merged 1](https://github.com/roboflow/inference/issues?q=state%3Aclosed%20is%3Apr%20author%3Amisrasaurabh1%20is%3Amerged), [PRs Merged 2)](https://github.com/roboflow/inference/issues?q=state%3Amerged%20is%3Apr%20author%3Acodeflash-ai%5Bbot%5D), **Unstructured** [(PRs Merged 1](https://github.com/Unstructured-IO/unstructured/pulls?q=is%3Apr+Explanation+and+details+in%3Abody+is%3Amerged), [PRs Merged 2)](https://github.com/Unstructured-IO/unstructured-ingest/pulls?q=is%3Apr+Explanation+and+details+in%3Abody+is%3Amerged), **Langflow** [(PRs Merged)](https://github.com/langflow-ai/langflow/issues?q=state%3Aclosed%20is%3Apr%20author%3Amisrasaurabh1) and many others to ship performant, expert level code.

Codeflash is great at optimizing AI Agents, Computer Vision algorithms, PyTorch code, numerical code, backend code or anything else you might write with Python.


## Installation

To install Codeflash, run:

```
pip install codeflash
```
Add codeflash as a development time dependency if you are using package managers like uv or poetry.
## Quick Start


1. To configure Codeflash for a project, at the root directory of your project where the pyproject.toml file is located, run:
   ```
   codeflash init
   ```
   - It will ask you a few questions about your project like the location of your code and tests
   - Ask you to generate an [API Key](https://app.codeflash.ai/app/apikeys) to access Codeflash's LLMs
   - Install a [GitHub app](https://github.com/apps/codeflash-ai/installations/select_target) to open Pull Requests on GitHub.
   - Ask if you want to setup a GitHub actions which will optimize all your future code.
   - The codeflash config is then saved in the pyproject.toml file.
   
2. Optimize your entire codebase:
   ```
   codeflash --all
   ```
   This can take a while to run for a large codebase, but it will keep opening PRs as it finds optimizations.
3. Optimize a script:
   ```
   codeflash optimize myscript.py
   ```

## Documentation
For detailed installation and usage instructions, visit our documentation at [docs.codeflash.ai](https://docs.codeflash.ai)

## Demo


- Optimizing the performance of new code for a Pull Request through GitHub Actions. This lets you ship code quickly while ensuring it remains performant.

https://github.com/user-attachments/assets/38f44f4e-be1c-4f84-8db9-63d5ee3e61e5

- Optiming a workflow end to end automatically with `codeflash optimize`


https://github.com/user-attachments/assets/355ba295-eb5a-453a-8968-7fb35c70d16c



## Support

Join our community for support and discussions. If you have any questions, feel free to reach out to us using one of the following methods:

- [Free live Installation Support](https://calendly.com/codeflash-saurabh/codeflash-setup)
- [Join our Discord](https://www.codeflash.ai/discord)
- [Follow us on Twitter](https://x.com/codeflashAI)
- [Follow us on Linkedin](https://www.linkedin.com/in/saurabh-misra/)

## License

Codeflash is licensed under the BSL-1.1 License. See the [LICENSE](https://github.com/codeflash-ai/codeflash/blob/main/codeflash/LICENSE) file for details.
