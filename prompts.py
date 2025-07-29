GEMINI_PROMPT = """
Provide a very detailed summary of the following video transcript. The summary should be well-structured and easy to read. If the provided transcript is in Polish, the summary must be in Polish. If the transcript is in English, the summary must be in English. Please include the following sections:

**1. Key Points Discussed:**
   - Bulleted list of the main topics and ideas presented.

**2. Detailed Summary of Each Point:**
   - For each key point, provide a detailed explanation, elaborating on the concepts and arguments.

**3. Notable Quotes:**
   - Extract significant quotes from the transcript that capture the essence of the discussion.

**4. In-depth Analysis:**
   - Provide an analysis of the content. What are the implications of the topics discussed? What is the overall tone and sentiment?

Here is the transcript:

---
{caption_text}
---

Please format the output clearly using markdown.
"""
