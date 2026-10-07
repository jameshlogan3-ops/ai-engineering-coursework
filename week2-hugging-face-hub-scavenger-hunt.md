# Week 2: Hugging Face Hub Scavenger Hunt

**James Logan III — CSC 595 AI Agent Architecture & Development**

I picked models I'd actually consider for my term project. It's a change review and CMDB hygiene agent, and one of my requirements is a local option that someone can run without my API key. So I went with three different vendors and three sizes: small, mid, and large.

## Part 2: Findings

| Model | Link | Parameter count / size | Architecture family | License | Tokenizer / vocab size |
|---|---|---|---|---|---|
| Model 1: Llama 3.2 3B Instruct (Meta) | [meta-llama/Llama-3.2-3B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) | 3.21B | Decoder-only transformer, Llama family (the card says only "optimized transformer architecture") | Llama 3.2 Community License (custom) | 128,256 (128,000 BPE tokens + 256 special tokens). **Not stated on the card**, and the config files are gated behind accepting the license, so I measured it from Meta's published tokenizer file. |
| Model 2: Qwen2.5 7B Instruct (Alibaba) | [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) | 7.61B (6.53B non-embedding) | Decoder-only transformer, `Qwen2ForCausalLM` (RoPE, SwiGLU, RMSNorm, grouped-query attention) | Apache 2.0 | 152,064 in `config.json` (151,643 BPE tokens plus special tokens, padded) |
| Model 3: Mistral Small 24B Instruct 2501 (Mistral AI) | [mistralai/Mistral-Small-24B-Instruct-2501](https://huggingface.co/mistralai/Mistral-Small-24B-Instruct-2501) | 24B | Dense decoder-only transformer, Mistral family | Apache 2.0 | 131,072 (Tekken tokenizer; the card rounds to "131k") |

## Part 3: Tokenizer Comparison

**Method:** I counted tokens with each model's own tokenizer in Python: Meta's Llama 3 tokenizer file, the Qwen BPE vocabulary, and Mistral's Tekken tokenizer from `mistral-common`. Counts exclude beginning- and end-of-sequence tokens.

- **Test sentence:** "I love learning about artificial intelligence."
- **Language A (Spanish):** "Me encanta aprender sobre inteligencia artificial."
- **Language B (Japanese):** "私は人工知能について学ぶのが大好きです。"

| Model | Test sentence tokens | Language A used | Language A tokens | Language B used | Language B tokens |
|---|---|---|---|---|---|
| Model 1: Llama 3.2 3B | 7 | Spanish | 9 | Japanese | 13 |
| Model 2: Qwen2.5 7B | 7 | Spanish | 9 | Japanese | 12 |
| Model 3: Mistral Small 24B | 7 | Spanish | 8 | Japanese | 14 |

All three tokenize English identically. Spanish costs 14–29% more tokens than English, and Japanese costs 71–100% more. Qwen is the most efficient on Japanese and Mistral the least, which matches Qwen's heavy Chinese and Japanese training data.

## Part 4: Context Window Check

| Model | Context window (tokens) | Source |
|---|---|---|
| Model 1: Llama 3.2 3B | 128,000 | [Model card](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) |
| Model 2: Qwen2.5 7B | 32,768 by default; 131,072 with YaRN scaling enabled | [Model card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) and `config.json` (`max_position_embeddings: 32768`) |
| Model 3: Mistral Small 24B | 32,000 | [Model card](https://huggingface.co/mistralai/Mistral-Small-24B-Instruct-2501) |

**Chapter 2 estimate:**

- Words: 62 pages × 500 to 600 words per page = **31,000 to 37,200 words**
- Tokens: words ÷ 0.75 words per token = 31,000 ÷ 0.75 to 37,200 ÷ 0.75 = **about 41,300 to 49,600 tokens**

**Conclusions:**

- **Llama 3.2 3B (128,000):** The whole chapter fits in one call, with roughly 78,000 to 87,000 tokens left for instructions and a response.
- **Qwen2.5 7B (32,768 default):** It does not fit. The chapter overflows the window by about 8,500 to 16,800 tokens before any response. With YaRN enabled (131,072), it fits with room to spare, but that requires changing the configuration, and the card notes static YaRN can reduce quality on shorter texts.
- **Mistral Small 24B (32,000):** It does not fit. The chapter would need to be split into chunks or retrieved selectively (RAG).

## Part 5: Comparison Reflection

What surprised me most is that size wasn't the biggest difference. Mistral Small is more than seven times bigger than Llama 3.2 3B, but Llama can hold four times as much text in one request. The bigger model is not automatically the more capable one for every job.

Licensing was the other real split. Qwen and Mistral are Apache 2.0, which is about as clean as it gets. Llama has Meta's own community license, with an acceptable use policy and extra terms for very large companies. Coming from a compliance background, that's the kind of thing I'd want legal to look at before anything went to production. Documentation was uneven too. Llama's card never states its vocabulary size, and the config files are locked behind the license agreement, so I had to measure it myself.

For my project, I'd pick Qwen2.5 7B as the local model. My agent reads change requests, checks them against CMDB records, and has to return a strict JSON result, and Qwen's card specifically calls out structured data and JSON output. The Apache license means no licensing questions. At 7B it runs on a normal laptop through Ollama, which is what I need so my professor or anyone else can run the project without my key. Mistral would probably make better calls, but 24B needs more memory than most laptops have, and my inputs are short. When I built the CMDB-derived database supporting zero trust across 250+ applications, the right answer was rarely the heaviest tool. It was the one the team could actually run and maintain. The same logic applies here.

For multilingual or cost-sensitive work, I'd still pick Qwen. It used the fewest tokens on Japanese, and on a hosted API, tokens are money and time. Twelve versus fourteen tokens looks small on one sentence, but it adds up over thousands of requests. Mistral did slightly better on Spanish, so for European languages the difference mostly washes out.

For long documents, I'd switch to Llama 3.2 3B. It's the only one that fits the whole chapter without any tricks. Qwen can stretch to about 131,000 tokens, but only after a configuration change that the card warns can hurt quality on shorter text. My change requests are short, so this matters little for now. If the agent ever reads full audit reports, I'd need Llama's longer window or a retrieval step.

## Part 6: Graduate Extension — Qwen2.5 Technical Report

I read the [Qwen2.5 Technical Report](https://arxiv.org/abs/2412.15115) from the Qwen team (arXiv 2412.15115).

**Something that isn't on the model card:** The card says almost nothing about the training data. The report does. Qwen2.5 was trained on 18 trillion tokens, up from 7 trillion for Qwen2. The team used their own earlier Qwen2 models to score and filter the data, and they deliberately rebalanced it: less e-commerce, social media, and entertainment content, and more technology, science, and academic material. After that came over a million supervised fine-tuning examples and two rounds of reinforcement learning (DPO on about 150,000 preference pairs, then GRPO). They also describe removing training data that overlapped with benchmark test sets, so the scores aren't inflated by memorized answers.

**A limitation they admit:** In the long-context section, the authors say plainly that reinforcement learning on long inputs is expensive and that good reward models for long text are hard to find. So they only ran RL on short instructions and relied on that carrying over to long ones. Put simply, the model's long-context behavior was never directly tuned. Their own tables also show the flagship model trailing a much larger Llama model on at least one coding benchmark, and they don't hide it.

**My take:** Reading the paper raised my trust in some places and lowered it in others. The decontamination work makes me more confident the benchmark numbers mean something, and you can't tell that from the card. On the other hand, using older Qwen models to decide what counts as "good" data means the new model inherits some of the old model's judgment and blind spots. That's something I'd want explained before using it anywhere regulated. The long-context admission matters most to me. The card just lists 131,072 tokens as a feature. The paper tells me that capability was never trained as directly as short-input behavior. The Army taught me to know the limits of my equipment before relying on it in the field, and this is the kind of limitation I'd want briefed before deployment, not discovered during. So I'd trust Qwen with short, structured inputs like change requests, but I'd test it hard before handing it a long audit document. That's my main takeaway: the card tells you what a model will accept, and the paper tells you what it was actually built to do well.
