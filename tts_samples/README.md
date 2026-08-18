# TTS Comparison Samples

This directory contains four MP3 audio samples generated for the white paper comparison.
The sentence used for all providers is:
> "Hello, this is the automotive service team. I can help you schedule an appointment for your 2022 Lexus RX. I have availability next Tuesday at 2 PM. Would that work for you?"

## 1. Twilio + Amazon Polly (`twilio_polly_test.mp3`)
* **Provider:** Amazon Polly (simulating Twilio's default TTS configuration)
* **Model/Engine:** `standard` (or `neural` if configured for Twilio)
* **Voice:** `Joanna` (Female, en-US)
* **Configuration:** Sample rate 8000Hz (telephony), MP3 format. This replicates the exact audio Twilio streams to callers.

## 2. Amazon Polly Direct (`amazon_polly_test.mp3`)
* **Provider:** Amazon Polly (Direct AWS API)
* **Model/Engine:** `neural`
* **Voice:** `Joanna` (Female, en-US)
* **Configuration:** Sample rate 24000Hz (high-fidelity), MP3 format. This represents the high-quality output you get when bypassing telephony constraints.

## 3. Fish Audio (`fish_audio_test.mp3`)
* **Provider:** Fish Audio
* **Model/Engine:** `fish-audio-v1` (or latest)
* **Voice:** `alex` (or configured custom model ID)
* **Configuration:** Sample rate 44100Hz, MP3 format. Shows the quality of next-gen generative STT/TTS pipelines.

## 4. Amazon Polly Generative (`amazon_polly_generative_test.mp3`)
* **Provider:** Amazon Polly (Generative Engine)
* **Model/Engine:** `generative`
* **Voice:** `Matthew` (Male, en-US)
* **Configuration:** High fidelity generative voice engine for highly expressive delivery.
