# Detailed summary prompt (for video detail page)
GEMINI_DETAILED_PROMPT = """
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

# Short summary prompt (for video list page)
GEMINI_SHORT_PROMPT = """
Provide a concise summary of the following video transcript in 50-100 words. The summary should capture the main topic and key takeaways. If the provided transcript is in Polish, the summary must be in Polish. If the transcript is in English, the summary must be in English.

Here is the transcript:

---
{caption_text}
---

Provide only the summary text, no additional formatting or sections.
"""

# Backward compatibility - keep GEMINI_PROMPT as alias for detailed prompt
GEMINI_PROMPT = GEMINI_DETAILED_PROMPT

# Date range summary prompt (for date range analysis)
GEMINI_DATE_RANGE_PROMPT = """
You are analyzing a collection of {video_count} YouTube videos that were published between {start_date} and {end_date}.

Based on the video titles and summaries provided below, create a comprehensive analysis report that includes:

**1. Overview:**
   - Number of videos processed
   - Date range covered
   - Number of unique channels

**2. Main Themes & Topics:**
   - Identify the dominant themes and topics across all videos
   - Group related videos by topic
   - Highlight any recurring subjects or trends

**3. Key Insights:**
   - What are the most important takeaways from this collection?
   - Are there any notable patterns or connections between videos?
   - What topics generated the most discussion or coverage?

**4. Chronological Highlights:**
   - Brief timeline of notable videos in chronological order
   - Any evolution of topics over the time period?

**5. Channel Analysis:**
   - Which channels contributed the most content?
   - Any notable differences in content style or focus between channels?

Here are the videos:

---
{videos_content}
---

Please format the output clearly using markdown. Write the entire summary in {language}.
"""
