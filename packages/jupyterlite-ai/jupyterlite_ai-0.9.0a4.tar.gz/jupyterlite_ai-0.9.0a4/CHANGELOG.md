# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

## 0.9.0a4

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.9.0a3...72563be35fc0f3fbfb31b6391516660f2ba3b9f2))

### Enhancements made

- Split and unified cell diffs [#213](https://github.com/jupyterlite/ai/pull/213) ([@jtpio](https://github.com/jtpio))
- Making Ai Agent able to Reading content for attached cells [#209](https://github.com/jupyterlite/ai/pull/209) ([@nakul-py](https://github.com/nakul-py))
- Better file tools [#206](https://github.com/jupyterlite/ai/pull/206) ([@jtpio](https://github.com/jtpio))
- Show completion prompt in the AI Settings panel [#203](https://github.com/jupyterlite/ai/pull/203) ([@jtpio](https://github.com/jtpio))
- Support Claude Haiku 4.5 [#202](https://github.com/jupyterlite/ai/pull/202) ([@jtpio](https://github.com/jtpio))
- Move the secrets manager toggle below the providers [#200](https://github.com/jupyterlite/ai/pull/200) ([@jtpio](https://github.com/jtpio))
- Better format tool calls that need approval [#198](https://github.com/jupyterlite/ai/pull/198) ([@jtpio](https://github.com/jtpio))
- Support discovering commands with a query [#195](https://github.com/jupyterlite/ai/pull/195) ([@jtpio](https://github.com/jtpio))

### Bugs fixed

- Fixing attachments attaches to old messages bug [#208](https://github.com/jupyterlite/ai/pull/208) ([@nakul-py](https://github.com/nakul-py))
- Debounce settings updates when editing the system prompt [#204](https://github.com/jupyterlite/ai/pull/204) ([@jtpio](https://github.com/jtpio))
- Copy the keys to secrets manager when switching [#201](https://github.com/jupyterlite/ai/pull/201) ([@brichet](https://github.com/brichet))
- Fixing clear attachments bug [#196](https://github.com/jupyterlite/ai/pull/196) ([@nakul-py](https://github.com/nakul-py))

### Maintenance and upkeep improvements

- Drop `skipLibCheck` [#214](https://github.com/jupyterlite/ai/pull/214) ([@jtpio](https://github.com/jtpio))
- Increase timeout for the code completion tests [#212](https://github.com/jupyterlite/ai/pull/212) ([@jtpio](https://github.com/jtpio))
- Minor fixes and clean up [#197](https://github.com/jupyterlite/ai/pull/197) ([@jtpio](https://github.com/jtpio))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-10-15&to=2025-10-24&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-10-15..2025-10-24&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Ajtpio+updated%3A2025-10-15..2025-10-24&type=Issues) | [@nakul-py](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Anakul-py+updated%3A2025-10-15..2025-10-24&type=Issues)

<!-- <END NEW CHANGELOG ENTRY> -->

## 0.9.0a3

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.9.0a2...3fbe54ef55d08c0d4042804fe98774ed9b9efc1f))

### Enhancements made

- Add Google Generative AI provider [#185](https://github.com/jupyterlite/ai/pull/185) ([@jtpio](https://github.com/jtpio))
- Allow specifying an API key for the generic OpenAI compatible provider [#179](https://github.com/jupyterlite/ai/pull/179) ([@jtpio](https://github.com/jtpio))
- Switch to ai-sdk and openai-agent [#176](https://github.com/jupyterlite/ai/pull/176) ([@brichet](https://github.com/brichet))
- Add multichat panel [#169](https://github.com/jupyterlite/ai/pull/169) ([@brichet](https://github.com/brichet))
- Custom base URL and generic provider (OpenAI compatible) [#171](https://github.com/jupyterlite/ai/pull/171) ([@jtpio](https://github.com/jtpio))

### Bugs fixed

- Token usage accumulation [#175](https://github.com/jupyterlite/ai/pull/175) ([@brichet](https://github.com/brichet))

### Maintenance and upkeep improvements

- Single provider registry [#191](https://github.com/jupyterlite/ai/pull/191) ([@jtpio](https://github.com/jtpio))
- Drop Python 3.8 [#183](https://github.com/jupyterlite/ai/pull/183) ([@jtpio](https://github.com/jtpio))
- Add `PWVIDEO` and `PWSLOWMO` to record videos from UI tests [#181](https://github.com/jupyterlite/ai/pull/181) ([@jtpio](https://github.com/jtpio))
- Add UI tests for remote MCP servers [#180](https://github.com/jupyterlite/ai/pull/180) ([@jtpio](https://github.com/jtpio))
- Update dependencies and default models [#174](https://github.com/jupyterlite/ai/pull/174) ([@jtpio](https://github.com/jtpio))
- Re-enable UI tests [#172](https://github.com/jupyterlite/ai/pull/172) ([@jtpio](https://github.com/jtpio))

### Documentation improvements

- Document Ollama and generic, remove ChromeAI [#189](https://github.com/jupyterlite/ai/pull/189) ([@jtpio](https://github.com/jtpio))
- Documentation about secrets manager [#188](https://github.com/jupyterlite/ai/pull/188) ([@brichet](https://github.com/brichet))
- Add documentation for custom providers [#184](https://github.com/jupyterlite/ai/pull/184) ([@jtpio](https://github.com/jtpio))
- Update README to reflect the latest iterations [#178](https://github.com/jupyterlite/ai/pull/178) ([@jtpio](https://github.com/jtpio))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-09-26&to=2025-10-15&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-09-26..2025-10-15&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Ajtpio+updated%3A2025-09-26..2025-10-15&type=Issues)

## 0.9.0a2

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.9.0a1...0a63b33304b70c8fa8461a2e36bba97d12f3d2d9))

### Bugs fixed

- Bump @jupyter/chat to 0.18.1 [#168](https://github.com/jupyterlite/ai/pull/168) ([@brichet](https://github.com/brichet))
- Fix token usage [#167](https://github.com/jupyterlite/ai/pull/167) ([@jtpio](https://github.com/jtpio))
- Disable tracing when creating a new `Runner` [#166](https://github.com/jupyterlite/ai/pull/166) ([@jtpio](https://github.com/jtpio))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-09-25&to=2025-09-26&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-09-25..2025-09-26&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Ajtpio+updated%3A2025-09-25..2025-09-26&type=Issues)

## 0.9.0a1

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.9.0a0...59b5a7c9f4d61cd4ef9e23e7a3cf504878881d07))

### Enhancements made

- Call the diff command directly when setting the cell content [#162](https://github.com/jupyterlite/ai/pull/162) ([@jtpio](https://github.com/jtpio))
- Add the secrets manager [#159](https://github.com/jupyterlite/ai/pull/159) ([@brichet](https://github.com/brichet))
- Re-add OpenAI [#147](https://github.com/jupyterlite/ai/pull/147) ([@jtpio](https://github.com/jtpio))

### Bugs fixed

- Get active cell info [#161](https://github.com/jupyterlite/ai/pull/161) ([@brichet](https://github.com/brichet))

### Maintenance and upkeep improvements

- Update @jupyter/chat and @mui dependencies [#164](https://github.com/jupyterlite/ai/pull/164) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-09-18&to=2025-09-25&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-09-18..2025-09-25&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Ajtpio+updated%3A2025-09-18..2025-09-25&type=Issues)

## 0.9.0a0

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.8.1...01723cd4d0ffa484afb560b085bd26ab033d7c75))

### New features added

- Add `jupyterlab-cell-diff` [#153](https://github.com/jupyterlite/ai/pull/153) ([@jtpio](https://github.com/jtpio))
- Agent workflows [#145](https://github.com/jupyterlite/ai/pull/145) ([@jtpio](https://github.com/jtpio))

### Enhancements made

- Add `supportsToolCalling` provider setting [#151](https://github.com/jupyterlite/ai/pull/151) ([@jtpio](https://github.com/jtpio))

### Bugs fixed

- Fix parameters for `discover_commands` [#157](https://github.com/jupyterlite/ai/pull/157) ([@jtpio](https://github.com/jtpio))
- Fix valid model check [#149](https://github.com/jupyterlite/ai/pull/149) ([@jtpio](https://github.com/jtpio))

### Maintenance and upkeep improvements

- Expose settings model and tool registry tokens, and use chat context [#152](https://github.com/jupyterlite/ai/pull/152) ([@brichet](https://github.com/brichet))
- Bump dependencies, disable tracing for now [#150](https://github.com/jupyterlite/ai/pull/150) ([@jtpio](https://github.com/jtpio))
- More cleanup [#148](https://github.com/jupyterlite/ai/pull/148) ([@jtpio](https://github.com/jtpio))

### API and Breaking Changes

- Agent workflows [#145](https://github.com/jupyterlite/ai/pull/145) ([@jtpio](https://github.com/jtpio))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-08-04&to=2025-09-18&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-08-04..2025-09-18&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Ajtpio+updated%3A2025-08-04..2025-09-18&type=Issues) | [@nakul-py](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Anakul-py+updated%3A2025-08-04..2025-09-18&type=Issues)

## 0.8.1

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.8.0...6627589bb83cfb1ab891d9ce3f3e4df8336f9a62))

### Bugs fixed

- Fix deferred providers on first load [#127](https://github.com/jupyterlite/ai/pull/127) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-07-09&to=2025-08-04&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-07-09..2025-08-04&type=Issues)

## 0.8.0

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.7.0...c736eca4e55cf491105aee04c01de8e9f7982b4a))

### Enhancements made

- Update to `@jupyter/chat` 0.14.0 [#108](https://github.com/jupyterlite/ai/pull/108) ([@jtpio](https://github.com/jtpio))
- Allow different providers for the chat and the completer [#105](https://github.com/jupyterlite/ai/pull/105) ([@brichet](https://github.com/brichet))
- Open the settings from the chat panel [#101](https://github.com/jupyterlite/ai/pull/101) ([@jtpio](https://github.com/jtpio))
- Gemini [#100](https://github.com/jupyterlite/ai/pull/100) ([@jtpio](https://github.com/jtpio))
- System prompt configurable [#96](https://github.com/jupyterlite/ai/pull/96) ([@brichet](https://github.com/brichet))
- Chat panel tweaks [#92](https://github.com/jupyterlite/ai/pull/92) ([@jtpio](https://github.com/jtpio))
- Improve Mistral completions [#85](https://github.com/jupyterlite/ai/pull/85) ([@jtpio](https://github.com/jtpio))

### Bugs fixed

- Fix secret fields initialization when using the secrets manager [#120](https://github.com/jupyterlite/ai/pull/120) ([@brichet](https://github.com/brichet))
- Fix the notification in settings [#119](https://github.com/jupyterlite/ai/pull/119) ([@brichet](https://github.com/brichet))
- Fix the messages datetime [#94](https://github.com/jupyterlite/ai/pull/94) ([@brichet](https://github.com/brichet))

### Maintenance and upkeep improvements

- Update langchain packages [#117](https://github.com/jupyterlite/ai/pull/117) ([@jtpio](https://github.com/jtpio))
- Remove provider settings check/generation [#113](https://github.com/jupyterlite/ai/pull/113) ([@brichet](https://github.com/brichet))
- Deduplicate npm dependencies [#109](https://github.com/jupyterlite/ai/pull/109) ([@brichet](https://github.com/brichet))
- Add UI tests [#97](https://github.com/jupyterlite/ai/pull/97) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-06-05&to=2025-07-09&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-06-05..2025-07-09&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Ajtpio+updated%3A2025-06-05..2025-07-09&type=Issues)

## 0.7.0

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.6.2...317fedd438232fb3add50e28037adb637cbc0814))

### Enhancements made

- Add a welcome message [#89](https://github.com/jupyterlite/ai/pull/89) ([@brichet](https://github.com/brichet))
- Handle compatibility with chromeAI and WebLLM [#87](https://github.com/jupyterlite/ai/pull/87) ([@brichet](https://github.com/brichet))
- Do not expose providers api [#84](https://github.com/jupyterlite/ai/pull/84) ([@brichet](https://github.com/brichet))
- Remove the custom settings connector [#81](https://github.com/jupyterlite/ai/pull/81) ([@brichet](https://github.com/brichet))
- Upgrade secrets manager [#75](https://github.com/jupyterlite/ai/pull/75) ([@brichet](https://github.com/brichet))
- Better handling of default values in settings [#73](https://github.com/jupyterlite/ai/pull/73) ([@brichet](https://github.com/brichet))
- Add Ollama provider [#69](https://github.com/jupyterlite/ai/pull/69) ([@brichet](https://github.com/brichet))
- WebLLM [#47](https://github.com/jupyterlite/ai/pull/47) ([@jtpio](https://github.com/jtpio))

### Bugs fixed

- Export the IAIProviderRegistry token [#88](https://github.com/jupyterlite/ai/pull/88) ([@brichet](https://github.com/brichet))
- Update `@langchain/community` to fix ChromeAI [#76](https://github.com/jupyterlite/ai/pull/76) ([@jtpio](https://github.com/jtpio))

### Maintenance and upkeep improvements

- Pin PyPI version of jupyter-secrets-manager [#86](https://github.com/jupyterlite/ai/pull/86) ([@brichet](https://github.com/brichet))
- Install `ipywidgets` for the demo deployed on GitHub Pages [#79](https://github.com/jupyterlite/ai/pull/79) ([@jtpio](https://github.com/jtpio))

### Documentation improvements

- Mention JupyterLab 4.4 and Notebook 7.4 final in the README [#83](https://github.com/jupyterlite/ai/pull/83) ([@jtpio](https://github.com/jtpio))
- Update Ollama instructions [#82](https://github.com/jupyterlite/ai/pull/82) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-05-13&to=2025-06-05&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-05-13..2025-06-05&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Ajtpio+updated%3A2025-05-13..2025-06-05&type=Issues) | [@trungleduc](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Atrungleduc+updated%3A2025-05-13..2025-06-05&type=Issues)

## 0.6.2

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.6.1...8cf12919ab5922b2ec7ed8f284299725a493d349))

### Bugs fixed

- Fix completer settings [#70](https://github.com/jupyterlite/ai/pull/70) ([@brichet](https://github.com/brichet))
- Fix the API keys in provider when using the secrets manager [#68](https://github.com/jupyterlite/ai/pull/68) ([@brichet](https://github.com/brichet))

### Maintenance and upkeep improvements

- Align the version of rjsf dependencies [#72](https://github.com/jupyterlite/ai/pull/72) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-05-02&to=2025-05-13&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-05-02..2025-05-13&type=Issues)

## 0.6.1

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.6.0...52376d7823635a8561eda88d6fcd7acd615c50c8))

### Enhancements made

- Allow to avoid displaying the secret fields of the settings UI [#65](https://github.com/jupyterlite/ai/pull/65) ([@brichet](https://github.com/brichet))
- Update secrets manager to >=0.3.0 [#63](https://github.com/jupyterlite/ai/pull/63) ([@brichet](https://github.com/brichet))

### Maintenance and upkeep improvements

- Update secrets manager to >=0.3.0 [#63](https://github.com/jupyterlite/ai/pull/63) ([@brichet](https://github.com/brichet))
- Update to jupyterlab>=4.4.0 [#62](https://github.com/jupyterlite/ai/pull/62) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-03-31&to=2025-05-02&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-03-31..2025-05-02&type=Issues)

## 0.6.0

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.5.0...15b6de565429273e0b159fa1a66712575449605d))

### Enhancements made

- Stop streaming [#61](https://github.com/jupyterlite/ai/pull/61) ([@brichet](https://github.com/brichet))
- Do not store passwords to server settings [#60](https://github.com/jupyterlite/ai/pull/60) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-03-21&to=2025-03-31&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-03-21..2025-03-31&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Ajtpio+updated%3A2025-03-21..2025-03-31&type=Issues)

## 0.5.0

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.4.0...f37fb548ee1c49f5600495ccb6be35ab976a3bce))

### Enhancements made

- Default providers refactoring [#58](https://github.com/jupyterlite/ai/pull/58) ([@brichet](https://github.com/brichet))
- Use the secrets manager [#53](https://github.com/jupyterlite/ai/pull/53) ([@brichet](https://github.com/brichet))

### Bugs fixed

- Avoid building settings schemas when building javascript [#59](https://github.com/jupyterlite/ai/pull/59) ([@brichet](https://github.com/brichet))

### Maintenance and upkeep improvements

- Default providers refactoring [#58](https://github.com/jupyterlite/ai/pull/58) ([@brichet](https://github.com/brichet))
- Update @jupyter/chat to v0.8.1 [#57](https://github.com/jupyterlite/ai/pull/57) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-03-10&to=2025-03-21&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-03-10..2025-03-21&type=Issues)

## 0.4.0

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.3.0...bd9c07a7fec2bfb62c6863a0aacdaefbf22bcd82))

### Enhancements made

- Provider registry [#50](https://github.com/jupyterlite/ai/pull/50) ([@brichet](https://github.com/brichet))
- Completer plugin [#49](https://github.com/jupyterlite/ai/pull/49) ([@brichet](https://github.com/brichet))
- Settings UI improvement [#48](https://github.com/jupyterlite/ai/pull/48) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2025-02-19&to=2025-03-10&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2025-02-19..2025-03-10&type=Issues)

## 0.3.0

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.2.0...1b482ade692e42ad8885aaf3211502720cadeecf))

### Enhancements made

- Add chat autocompletion and the `/clear` command [#41](https://github.com/jupyterlite/ai/pull/41) ([@jtpio](https://github.com/jtpio))
- Add icon and name for the AI assistant [#40](https://github.com/jupyterlite/ai/pull/40) ([@jtpio](https://github.com/jtpio))
- Stream responses [#39](https://github.com/jupyterlite/ai/pull/39) ([@jtpio](https://github.com/jtpio))
- Use a chat model instead of LLM for codestral completion [#31](https://github.com/jupyterlite/ai/pull/31) ([@brichet](https://github.com/brichet))
- Add initial system prompt in ChatHandler and completion [#28](https://github.com/jupyterlite/ai/pull/28) ([@brichet](https://github.com/brichet))
- Add `ChromeAI` [#27](https://github.com/jupyterlite/ai/pull/27) ([@jtpio](https://github.com/jtpio))
- Anthropic (Claude) provider [#22](https://github.com/jupyterlite/ai/pull/22) ([@brichet](https://github.com/brichet))
- Add OpenAI provider [#19](https://github.com/jupyterlite/ai/pull/19) ([@brichet](https://github.com/brichet))
- Dynamic settings for providers [#14](https://github.com/jupyterlite/ai/pull/14) ([@brichet](https://github.com/brichet))

### Bugs fixed

- Update to a newer `@langchain/community` to fix ChromeAI integration [#43](https://github.com/jupyterlite/ai/pull/43) ([@jtpio](https://github.com/jtpio))
- Upgrade the jupyterlite-core package in deployment [#30](https://github.com/jupyterlite/ai/pull/30) ([@brichet](https://github.com/brichet))

### Maintenance and upkeep improvements

- Deployment with prereleased jupyterlite-pyodide-kernel [#33](https://github.com/jupyterlite/ai/pull/33) ([@brichet](https://github.com/brichet))
- Fix installation of pre-released jupyterlite in deployment [#32](https://github.com/jupyterlite/ai/pull/32) ([@brichet](https://github.com/brichet))
- Upgrade the jupyterlite-core package in deployment [#30](https://github.com/jupyterlite/ai/pull/30) ([@brichet](https://github.com/brichet))

### Documentation improvements

- Update README.md [#26](https://github.com/jupyterlite/ai/pull/26) ([@jtpio](https://github.com/jtpio))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2024-12-04&to=2025-02-19&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2024-12-04..2025-02-19&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Ajtpio+updated%3A2024-12-04..2025-02-19&type=Issues)

## 0.2.0

([Full Changelog](https://github.com/jupyterlite/ai/compare/v0.1.0...8c41100bf87c99e377fd4752c50853dace7667e1))

### Enhancements made

- Refactoring AIProvider and handling errors [#15](https://github.com/jupyterlite/ai/pull/15) ([@brichet](https://github.com/brichet))
- Making the LLM providers more generics [#10](https://github.com/jupyterlite/ai/pull/10) ([@brichet](https://github.com/brichet))
- Use a throttler instead of a debouncer for code completion [#8](https://github.com/jupyterlite/ai/pull/8) ([@brichet](https://github.com/brichet))
- Update @jupyter/chat to 0.5.0 [#7](https://github.com/jupyterlite/ai/pull/7) ([@brichet](https://github.com/brichet))
- Switch to using langchain.js [#6](https://github.com/jupyterlite/ai/pull/6) ([@jtpio](https://github.com/jtpio))

### Bugs fixed

- Improves the relevance of codestral completion [#18](https://github.com/jupyterlite/ai/pull/18) ([@brichet](https://github.com/brichet))

### Maintenance and upkeep improvements

- Update references to the repo after the rename [#21](https://github.com/jupyterlite/ai/pull/21) ([@jtpio](https://github.com/jtpio))
- Rename the extension `jupyterlite_ai` [#20](https://github.com/jupyterlite/ai/pull/20) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2024-06-24&to=2024-12-04&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Abrichet+updated%3A2024-06-24..2024-12-04&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Ajtpio+updated%3A2024-06-24..2024-12-04&type=Issues)

## 0.1.0

([Full Changelog](https://github.com/jupyterlite/ai/compare/9c8d350b8876ad3a9ffe8dbe723ca093bb680681...b77e9e9a563cda3b9d37972248e738746f7370a8))

### Maintenance and upkeep improvements

- Reset version [#4](https://github.com/jupyterlite/ai/pull/4) ([@jtpio](https://github.com/jtpio))

### Documentation improvements

- Add disclaimer [#3](https://github.com/jupyterlite/ai/pull/3) ([@jtpio](https://github.com/jtpio))
- Update links to the repo [#2](https://github.com/jupyterlite/ai/pull/2) ([@jtpio](https://github.com/jtpio))
- Add files for a JupyterLite demo [#1](https://github.com/jupyterlite/ai/pull/1) ([@jtpio](https://github.com/jtpio))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterlite/ai/graphs/contributors?from=2024-06-10&to=2024-06-24&type=c))

[@jtpio](https://github.com/search?q=repo%3Ajupyterlite%2Fai+involves%3Ajtpio+updated%3A2024-06-10..2024-06-24&type=Issues)
