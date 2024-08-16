from transformers import T5ForConditionalGeneration, T5Tokenizer

# Initialize the model and tokenizer
model_name = "t5-small"  # You can also use 't5-base', 't5-large', etc. for larger models
model = T5ForConditionalGeneration.from_pretrained(model_name)
tokenizer = T5Tokenizer.from_pretrained(model_name)

def summarize_text(text, max_length=20, min_length=40):
    # Prepend "summarize: " to the input text for T5 models
    input_text = "summarize: " + text

    # Tokenize the input text
    inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)

    # Generate the summary
    summary_ids = model.generate(
        inputs,
        max_length=max_length,  # Set the maximum length of the summary
        min_length=min_length,  # Set the minimum length of the summary
        length_penalty=2.0,     # Optional: penalizes longer outputs
        num_beams=4,            # Number of beams for beam search
        early_stopping=True     # Stops early when a complete sequence is found
    )

    # Decode and return the summary
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# Example usage
large_text = """
It is worth noting that small hashes (i.e., a few elements with small values) are encoded in special way in memory that make them very memory efficient.

Basic commands
HSET: sets the value of one or more fields on a hash.
HGET: returns the value at a given field.
HMGET: returns the values at one or more given fields.
HINCRBY: increments the value at a given field by the integer provided.
See the complete list of hash commands.

Examples
Store counters for the number of times bike:1 has been ridden, has crashed, or has changed owners:

>_ Redis CLI
> HINCRBY bike:1:stats rides 1
(integer) 1
> HINCRBY bike:1:stats rides 1
(integer) 2
> HINCRBY bike:1:stats rides 1
(integer) 3
> HINCRBY bike:1:stats crashes 1
(integer) 1
> HINCRBY bike:1:stats owners 1
(integer) 1
> HGET bike:1:stats rides
"3"
> HMGET bike:1:stats owners crashes
1) "1"
2) "1"


Python

Node.js

Java

C#
Field expiration
New in Redis Community Edition 7.4 is the ability to specify an expiration time or a time-to-live (TTL) value for individual hash fields. This capability is comparable to key expiration and includes a number of similar commands.

Use the following commands to set either an exact expiration time or a TTL value for specific fields:

HEXPIRE: set the remaining TTL in seconds.
HPEXPIRE: set the remaining TTL in milliseconds.
HEXPIREAT: set the expiration time to a timestamp1 specified in seconds.
HPEXPIREAT: set the expiration time to a timestamp specified in milliseconds.
Use the following commands to retrieve either the exact time when or the remaining TTL until specific fields will expire:

HEXPIRETIME: get the expiration time as a timestamp in seconds.
HPEXPIRETIME: get the expiration time as a timestamp in milliseconds.
HTTL: get the remaining TTL in seconds.
HPTTL: get the remaining TTL in milliseconds.
Use the following command to remove the expiration of specific fields:

HPERSIST: remove the expiration.
Common field expiration use cases
Event Tracking: Use a hash key to store events from the last hour. Set each event's TTL to one hour. Use HLEN to count events from the past hour.

Fraud Detection: Create a hash with hourly counters for events. Set each field's TTL to 48 hours. Query the hash to get the number of events per hour for the last 48 hours.

Customer Session Management: Store customer data in hash keys. Create a new hash key for each session and add a session field to the customer’s hash key. Expire both the session key and the session field in the customer’s hash key automatically when the session expires.

Active Session Tracking: Store all active sessions in a hash key. Set each session's TTL to expire automatically after inactivity. Use HLEN to count active sessions.

Field expiration examples
Support for hash field expiration in the official client libraries is not yet available, but you can test hash field expiration now with beta versions of the Python (redis-py) and Java (Jedis) client libraries.

Following are some Python examples that demonstrate how to use field expiration.

Consider a hash data set for storing sensor data that has the following structure:
"""

# Set the desired output length
summary = summarize_text(large_text, max_length=5, min_length=5)
print("Summary:", summary)
