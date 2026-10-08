# Ollama Session Notes

**Model:** llama3.2:3b
**Machine:** Windows laptop, run locally through Ollama in PowerShell
**Result:** Worked. Screenshot saved as `ollama_session.png`.

## Question asked

"What is the difference between a hosted AI model and a local one?"

## Observations

Llama returned a long, well-organized answer covering both approaches, their characteristics, and the key differences, all generated on my own laptop with no API key and no data leaving the machine.

Its formatting showed raw Markdown symbols (`**bold**`) because the terminal doesn't render them, so the output is less readable than in a web chat interface.

A few points in the answer are oversimplified or debatable. It says hosted models are "generally more secure due to cloud provider measures," which leaves out the main security tradeoff: with a hosted model, every prompt and its data leave your environment and go to a third party. It also says a local model is "trained and optimized for the specific device," when in practice a general pretrained model is downloaded and run as-is. From a security perspective, data residency is one of the strongest reasons to choose a local model, and the answer underplays it. That's a useful reminder that a small model's output reads confidently even where it's incomplete.
