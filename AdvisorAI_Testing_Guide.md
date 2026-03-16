# AdvisorAI Testing Guide

Welcome to the AdvisorAI testing phase! AdvisorAI is an intelligent RAG (Retrieval-Augmented Generation) based academic advisor designed specifically for the Stevens Institute of Technology.

This document outlines the core capabilities of the chatbot, the types of questions it is designed to answer, and what kind of responses you can expect during your testing.

## System Overview
AdvisorAI uses a hybrid knowledge approach:
1. **Vector Database Retrieval (RAG):** It queries an internal database of documents encompassing courses, faculty information, and faculty research.
2. **Personalized Context:** It has the ability to connect to user profiles to answer user-specific questions (if logged in/authenticated).
3. **Web Search Fallback:** If the internal database lacks the necessary current information (e.g., recent campus events or news), the chatbot can fall back to performing live web searches to find the most up-to-date information.

---

## 1. Course-Related Inquiries
The chatbot has access to curriculum data, course details, and academic requirements.

**Example Questions:**
- "What are the prerequisites for CS 559 (Machine Learning)?"
- "How many credits is the Software Engineering course?"
- "Can you give me a syllabus overview for Web Programming?"
- "What courses are typically required for a Master's in Computer Science?"

**Expected Answer Format:**
Detailed text explaining the course requirements, credit count, prerequisites, and a brief description of the syllabus or course outcomes.

---

## 2. Faculty Information
The chatbot can provide details about faculty members, their contact information, and their roles at the university.

**Example Questions:**
- "Who is the professor for the Algorithms class?"
- "What is Professor Smith's email address and office location?"
- "Which department does Dr. Johnson belong to?"

**Expected Answer Format:**
Direct, concise answers providing the faculty member's name, titles, contact information (email/phone), and office hours/location if available.

---

## 3. Faculty Research & Publications
The chatbot has specialized knowledge regarding the research focus and publications of the university's faculty.

**Example Questions:**
- "What is Professor Davis researching currently?"
- "Are there any professors at Stevens working on Artificial Intelligence or Robotics?"
- "Can you list some recent publications by Dr. Williams?"

**Expected Answer Format:**
A summary of the professor's research interests, laboratory affiliations, and a list of notable or recent publications and projects.

---

## 4. Personalized Student Advising (Profile-Based)
If the user account has associated profile data, the chatbot can provide personalized schedule and curriculum advice.

**Example Questions:**
- "Based on my current transcript, what core courses do I still need to take?"
- "Am I eligible to enroll in CS 559 next semester?"
- "How many more credits do I need to graduate?"

**Expected Answer Format:**
A tailored response that references the student's specific academic standing, completed courses, and clear next steps or recommendations for registration.

---

## 5. General Campus & Current Events
For general university queries or very recent updates not available in the static curriculum database, the chatbot will utilize its web-scraping agents to find live information about Stevens Institute of Technology.

**Example Questions:**
- "When is the next career fair on campus?"
- "What are the current library hours for the final exam week?"
- "Where can I find the academic calendar for the upcoming Fall semester?"

**Expected Answer Format:**
Synthesized answers formulated from top web search results (mostly from standard Stevens web pages or trusted academic sites), explicitly stating that the information was retrieved from the web if necessary.

---

## Testing Instructions & Feedback
While testing, please keep in mind:
- **Hallucinations:** Watch out for "hallucinated" or incorrect data, especially if a question is highly specific.
- **Outdated Info:** The internal database might sometimes lag behind newly announced changes. Test how well the chatbot falls back to web searches when its internal data is outdated.
- **Edge Cases:** Try asking complex, multi-part questions (e.g., "I am interested in AI and need a 3-credit course. What do you recommend and who teaches it?").

Please log any unexpected behaviors, crashes, or incorrect responses to help us improve the system prior to full deployment.
