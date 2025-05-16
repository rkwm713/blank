# Prompt Template Examples for Developers & AI Interaction

**Last Updated:** May 15, 2025

## 1. Introduction

Effective communication with AI models relies heavily on well-crafted prompts. This document provides a collection of prompt templates and examples designed to assist developers in various tasks, including Python coding, command-line operations, interacting with advanced AI models (like Claude and Gemini), and specifically for tasks related to the Make-Ready Report project.

## 2. General Prompting Best Practices

* **Be Specific & Clear:** The more precise your request, the better the AI can understand and fulfill it.
* **Provide Context:** Include relevant background information, existing code snippets, error messages, or references to project documents.
* **Define the Persona/Role:** Tell the AI what role it should adopt (e.g., "You are an expert Python developer," "You are a helpful assistant explaining CLI commands").
* **Specify the Output Format:** Request the output in a particular format (e.g., "Provide the answer as a Python function," "Explain in bullet points," "Generate a Markdown table").
* **Iterate and Refine:** If the first response isn't perfect, refine your prompt and try again. Break down complex tasks into smaller, manageable prompts.
* **Use Delimiters:** For code snippets or specific text to be processed, use delimiters like triple backticks (```), XML tags (`<example></example>`), or similar to clearly separate them from the rest of the prompt.

---

## 3. Python Development Prompt Templates

### 3.1. Code Generation

**Template:**
Act as an expert Python developer.Write a Python [function/class/script] that accomplishes the following:[Clearly describe the desired functionality, inputs, and expected outputs.]Inputs:[Parameter 1]: [Type], [Description][Parameter 2]: [Type], [Description]Outputs:[Return Value/Effect]: [Type], [Description]Requirements/Constraints:[e.g., Must use Python 3.9+][e.g., Handle potential errors like FileNotFoundError][e.g., Prioritize readability and include comprehensive comments]Example Usage (Optional):# How the function/class should be called
Example:Act as an expert Python developer.
Write a Python function called `normalize_pole_id` that takes a string `pole_label` as input.
The function should normalize pole identifiers by:
1. Removing leading/trailing whitespace.
2. Removing any prefix like "N-", "S-", or digits followed by a hyphen (e.g., "1-", "06-").
3. Converting the result to uppercase.

**Inputs:**
- `pole_label`: string, The raw pole label from SPIDAcalc or Katapult.

**Outputs:**
- Return Value: string, The normalized pole ID.

**Requirements/Constraints:**
- Must use Python 3.9+.
- Handle cases where `pole_label` might be None or empty by returning an empty string or None.
- Include comments explaining the regex or logic used.

**Example Usage:**
```python
print(normalize_pole_id("  1-PL123456  ")) # Expected: "PL123456"
print(normalize_pole_id("N-pl98765"))    # Expected: "PL98765"
print(normalize_pole_id("POLE777"))      # Expected: "POLE777"
3.2. Debugging CodeTemplate:Act as an expert Python debugger.
I have the following Python code that is not working as expected:

```python
[Paste your problematic code snippet here]
Problem Description:[Clearly describe what the code is supposed to do.][Clearly describe the error message received (if any, include full traceback).][Clearly describe the unexpected behavior if no error message.]What I've tried so far:[List any debugging steps you've already taken.]Please help me identify the issue and suggest a fix. Explain your reasoning.
### 3.3. Explaining Code

**Template:**
Act as an expert Python developer.Please explain the following Python code snippet in detail:[Paste the code snippet here]
Focus on:The overall purpose of the code.The functionality of each key function/class/method.Any complex logic or algorithms used.Potential edge cases or areas for improvement.Provide the explanation in [clear paragraphs / bullet points].
### 3.4. Refactoring Code

**Template:**
Act as an expert Python developer specializing in code optimization and readability.Please refactor the following Python code snippet to improve [readability / performance / maintainability / adherence to PEP 8]:[Paste your code snippet here]
Specific Goals for Refactoring:[e.g., Reduce complexity of function X][e.g., Make variable names more descriptive][e.g., Optimize the loop in function Y]Provide the refactored code and a brief explanation of the changes made and why.
### 3.5. Writing Unit Tests

**Template:**
Act as an expert Python developer proficient in writing unit tests using the unittest (or pytest) framework.Please write unit tests for the following Python function/class:[Paste the function/class definition here]
The tests should cover:[Happy path scenarios with typical inputs][Edge cases (e.g., empty inputs, None inputs, boundary values)][Error handling (if the function is expected to raise exceptions)]Provide the complete test script.
---

## 4. Command-Line Interface (CLI) Interaction Prompt Templates

### 4.1. Generating CLI Commands

**Template:**
Act as a CLI expert for [Operating System, e.g., Linux, macOS, Windows] using [Shell, e.g., bash, PowerShell].I need a command to accomplish the following:[Clearly describe the task you want to perform.]Context/Constraints:[e.g., Current directory is /home/user/projects][e.g., I want to find files modified in the last 7 days][e.g., The output should be redirected to a file named output.txt]Provide the command and a brief explanation of each part.
**Example:**
Act as a CLI expert for Linux using bash.I need a command to find all Python files (.py) in the current directory and its subdirectories that contain the string "TODO:" (case-insensitive).The output should list the filenames and the matching lines.Provide the command and a brief explanation of each part.
### 4.2. Explaining CLI Commands

**Template:**
Act as a CLI expert.Please explain the following command in detail:[Paste the CLI command here]
Break down each component of the command and explain its purpose and any common options used.Also, describe what the command achieves overall.
### 4.3. Troubleshooting CLI Errors

**Template:**
Act as a CLI troubleshooting expert for [Operating System/Shell].I ran the following command:[Paste the command you ran]
And I received this error message or unexpected output:[Paste the full error message or describe the output]
Context:[e.g., My current directory is...][e.g., The file 'xyz.txt' exists and has read permissions.]Please help me understand the error and suggest how to fix it.
---

## 5. Advanced AI Model (e.g., Claude, Gemini Advanced) Prompt Templates

*(These are more general and can be adapted. Focus on leveraging advanced reasoning, context handling, and instruction following.)*

### 5.1. Complex Task Decomposition & Planning

**Template:**
You are an AI project manager and technical architect.I need to develop a system that [describe the overall complex system or task].Please break this down into a series of manageable development phases or key components.For each phase/component, outline:Primary objectives.Key functionalities to implement.Potential challenges or considerations.Suggest a logical order for tackling these phases/components.Provide the output as a structured plan.
### 5.2. Multi-Document Analysis and Synthesis

**Template:**
You are an AI research assistant.I have provided [N] documents (or text snippets) below, delimited by <doc_N_start> and <doc_N_end>.<doc_1_start>[Content of document 1]<doc_1_end><doc_2_start>[Content of document 2]<doc_2_end>[... more documents ...]Please analyze these documents and synthesize the information to answer the following question(s):[Your specific question(s) that require information from multiple documents.]Highlight any conflicting information found across the documents.Provide a consolidated summary of [specific topic] based on all provided documents.
### 5.3. Creative Content Generation with Constraints

**Template:**
You are a creative [Writer/Poet/Scriptwriter].Please generate a [short story/poem/dialogue script] on the theme of [your theme].Key elements to include:Character A: [Description]Character B: [Description]Setting: [Description]Mood: [e.g., suspenseful, humorous, reflective]Specific constraint: [e.g., Must be exactly 100 words, Must include the phrase "...", Must be written in iambic pentameter]The output should be [desired format, e.g., plain text, Markdown].
---

## 6. Gemini Specific Prompt Templates

*(Leveraging Gemini's strengths, including potential for multimodality if applicable, strong reasoning, and code understanding.)*

### 6.1. Chain-of-Thought / Step-by-Step Reasoning

**Template:**
Solve the following problem step-by-step, explaining your reasoning at each stage.Problem: [Clearly state the problem, which could be logical, mathematical, or code-related.]Show your work and thought process clearly.
### 6.2. Code Review and Improvement Suggestions (with Rationale)

**Template:**
You are an expert AI code reviewer with a focus on best practices, security, and performance.Please review the following Python code snippet:[Paste Python code snippet]
Provide a comprehensive review covering:Correctness: Does the code achieve its intended purpose? Are there any logical errors?Readability & Maintainability: Is the code clear, well-commented, and easy to understand?Performance: Are there any obvious performance bottlenecks or areas for optimization?Security: Are there any potential security vulnerabilities (e.g., injection, insecure defaults)?Best Practices: Does the code adhere to Pythonic principles and PEP 8 guidelines?For each point, provide specific examples from the code and suggest improvements with clear rationale.Organize your feedback into sections.
### 6.3. Generating Explanations from Multiple Data Types (Conceptual for future multimodality)

*(This is more forward-looking if direct image/audio input isn't available in the current interface, but illustrates a Gemini strength.)*

**Template (Conceptual):**
Analyze the provided information:Image: [Description of an image, or imagine an image is uploaded]Code Snippet:[Python code related to the image's content]
Text Description: "[Text providing context for the image and code]"Based on all three pieces of information, explain [a specific concept or process].How does the code relate to the visual elements in the image and the textual description?
---

## 7. Make-Ready Report Project Specific Prompt Templates

*(These prompts leverage the context of your Katapult/SPIDAcalc project and the READMEs you've created.)*

### 7.1. Data Extraction Logic from JSON

**Template:**
Referring to the document [Katapult_JSON_Developer_Guide.md ID: katapult_json_developer_guide_v1 / SPIDAcalc_JSON_Developer_Guide.md ID: spidacalc_json_developer_guide_v1],I need to extract [specific data point, e.g., "Pole Owner," "Attachment Height for a wire in Measured Design"] from the [Katapult/SPIDAcalc] JSON.The relevant JSON structure for [the element containing the data, e.g., a 'node' object, a 'wire' object within a design] looks like this:[Paste a relevant snippet of the JSON structure]
Provide a Python code snippet that extracts this data, including necessary error handling for missing keys (e.g., using dict.get()).Assume the input is a Python dictionary named [e.g., pole_data, wire_attachment_data].
**Example (Make-Ready Project):**
Referring to Developer's Guide to Katapult JSON Structure with Examples (ID: katapult_json_developer_guide_v1),I need to extract the 'PoleNumber' from a Katapult node's attributes.The relevant JSON structure for the 'attributes' object within a node is:{
  "PoleNumber": {
    "-Imported": "PL370858",
    "_created": { /* ... */ }
  },
  "PL_number": { "-Imported": "PL370858", /* ... */ }
  // ... other attributes
}
Sometimes 'PoleNumber' might have an 'assessment' key instead of '-Imported'.Provide a Python function get_katapult_pole_number(node_attributes_dict) that extracts the pole number, prioritizing '-Imported' then 'assessment', and returns it. Handle cases where 'PoleNumber' or its sub-keys might be missing.
### 7.2. Querying Excel Report Mapping Rules

**Template:**
Based on the README: Make-Ready Excel Report - Structure and Data Mapping (ID: excel_report_readme_v1):Which JSON source (Katapult or SPIDAcalc) is primarily used for Excel Column [Letter/Name, e.g., "M: Attachment Height - Existing"]?What is the specific JSON path (or paths if multiple fallbacks) to find the data for this column?Are there any specific transformations (e.g., unit conversion, normalization) mentioned for this column's data?Explain the logic for populating the "From Pole / To Pole" boxes in Column [J/K].
### 7.3. Drafting Sections for `task_notes.md`

**Template:**
I am creating a task_notes.md file for a new Make-Ready report generation task, using the template (ID: task_notes_template_v2).The input files for this task are:Katapult JSON: [filename_katapult.json]SPIDAcalc JSON: [filename_spidacalc.json] (or "Not available for this task")The objective is to [briefly describe the main goal, e.g., "generate the standard report focusing on PLA and mid-span data for Job XYZ"].Please help me draft the following sections for the task_notes.md:Section 1: Objective (based on my description)Section 2: Input Artifacts (listing the provided files)Section 4: Processing Requirements & Logic (populate the placeholders for Pole Identification, Height Data, PLA, and Attacher Name Normalization with standard project rules, noting any specific focus areas).Section 7: References & Linked Project Documents (ensure correct document IDs are used).Assume standard processing rules apply unless otherwise specified.
### 7.4. Generating CLI Arguments for `final_code_output.py`

**Template:**
I need to run the final_code_output.py script (which uses CLI arguments as defined in our project's .clinerules equivalent).For a specific task, I have the following requirements:Katapult JSON path: [path/to/katapult.json]SPIDAcalc JSON path: [path/to/spidacalc.json] (or "None")Target specific poles: [Yes/No]. If Yes, poles are: [PL123,PL456] (or path/to/poles.txt)Conflict strategy for existing height: [katapult/spida/highlight]Output file path: [path/to/output_report.xlsx] (or "Use default")Verbose output: [Yes/No]Generate the full command-line string to execute final_code_output.py with these parameters.
---

## 8. Conclusion

These templates are starting points. The key to successful AI interaction is to be clear, contextual, and iterative. Experiment with different phrasing and levels of detail to find what works best for your specific needs and the AI model you are using.
