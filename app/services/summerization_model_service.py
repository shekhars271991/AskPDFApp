from transformers import T5ForConditionalGeneration, T5Tokenizer

model_name = "t5-small"  # 't5-base', 't5-large', etc. for larger models
model = T5ForConditionalGeneration.from_pretrained(model_name)
tokenizer = T5Tokenizer.from_pretrained(model_name)

def summarize_text(text, max_length=6, min_length=6):
    input_text = "summarize: " + text

    # Tokenize the input text
    inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)

    # Generate the summary
    summary_ids = model.generate(
        inputs,
        max_length=max_length,  # Set the maximum length of the summary to 20 tokens
        min_length=min_length,  # Set the minimum length of the summary
        length_penalty=2.0,     # Increase penalty for longer summaries
        num_beams=4,            # Number of beams for beam search
        early_stopping=True     # Stops early when a complete sequence is found
    )

    # Decode and return the summary
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary