# Outline of Editor & Correction Functions

This document outlines the primary Human-in-the-Loop (HIL) workflows for ensuring data accuracy within the contract analysis system. These functions are designed to provide a complete, tiered system for correcting errors, from initial document intake to the AI's final reasoning process.

**A Note on Data Integrity:** All correction processes are designed to be non-destructive where possible. Rather than deleting incorrect data from the graph or vector databases, the system's primary method is to version and supersede it. A new, human-verified version of a node or text chunk is created, and the old version is marked as "outdated" or "archived." This maintains a complete audit trail and allows for changes to be reverted if necessary.

### **1. Source Document Correction Workflow (Transcription-Level HIL)**

This workflow addresses errors in the raw text of a source document that were missed during the initial OCR review. It treats the OCR HIL pipeline as the permanent "source text editor."

- **1.1. Trigger:** A user, while reviewing a document in the main analysis UI's "Original Source" view, identifies a transcription error (e.g., a typo, a misread number).
- **1.2. Action:** The user clicks a "Correct Source Text" or "Revisit OCR" button associated with that document.
- **1.3. Interface:** The system navigates the user to the dedicated **OCR HIL Interface** for the selected document. This interface presents the familiar side-by-side view:
    - **Left Pane:** The static, unchangeable image of the original document page.
    - **Right Pane:** The editable text block containing the AI's current transcription of that page.
- **1.4. Correction & Resubmission:** The user manually corrects the typo in the text block.
- **1.5. "Save & Reprocess" Cascade:** Upon saving, the system initiates an automated, system-wide update process:
    - The corrected text **supersedes** the previous version in the database.
    - The entire source document is automatically **re-chunked and re-embedded**, creating new, accurate vector representations.
    - The corresponding nodes in the **knowledge graph are updated** with the corrected text.
    - The user is then returned to the main analysis UI.

### **2. Conformed Document Correction Workflow (Structural-Level HIL)**

This workflow addresses logical and structural errors in how the AI has assembled the "Conformed Document." It allows a user to supervise a "Corrector Agent" to fix mistakes in the AI's interpretation of how documents relate to each other.

- **2.1. Trigger:** A user, while examining the "Side by Side View," determines that the AI's "Conformed Document" is logically incorrect based on the source evidence (e.g., an amendment was appended incorrectly).
- **2.2. The Hybrid Input Interface:** The user activates the "Corrector Agent" and provides instructions using a combination of methods: templated buttons, line numbering, and natural language.
- **2.3. The Verification & Override Workflow (Track Changes Model):**
    - **Step A: AI Generates a Proposal:** The Corrector Agent translates the user's command into a plan and presents a **"Proposed Changes" summary** in a side panel, with a primary button: **[ Show Text Edits ]**.
    - **Step B: User Visualizes Changes In-Context:** The user clicks "Show Text Edits," which renders a **markup view** directly within the conformed document (additions in color, deletions with a ~~strikethrough~~).
    - **Step C: User Accepts, Rejects, or Manually Edits:** The user can **[ Apply All ]** changes, **[ Reject ]** them, or **[ Unlock for Manual Edit ]** to gain direct control, with a "Smart Save" feature to infer structural changes from their manual edits.

### **3. Auditing and Correcting AI Cognition (Semantic-Level HIL)**

This section outlines the tools for diagnosing and correcting the AI's deeper semantic understanding of the ingested content.

- **3.1. The Diagnostic Tool: The Dual Highlighting System**
This feature is the primary tool for exposing a mismatch between the source text and the AI's interpretation.
    - **Mechanism:** When a user clicks an "evidence chip," the system highlights both the text in the **source document** (the "where") and the corresponding text in the **AI's answer** (the "what").
    - **How It Exposes Errors:** A misalignment between these two highlights is a clear signal of a potential interpretation error (e.g., misinterpretation, incorrect sourcing, calculation errors).
- **3.2. The Correction Tool: The Cognition Validation Workflow**
This is the most advanced HIL workflow, designed to fix the AI's fundamental understanding of a document's meaning. It allows the user to engage in a structured dialogue to re-train the AI's interpretation.
    - **Trigger:** After observing a potential error via the Dual Highlighting System, the user clicks a **[ Validate AI Cognition ]** button.
    - **Interface:** The system opens a dedicated conversational interface. The questionable AI answer and its evidence are pre-loaded as context.
    - **Step A: Probing & Diagnosis:** The user asks the AI specific, probing questions to test its understanding (e.g., "List all properties with automatic lease renewals and cite the specific clause for each."). The AI responds with fully sourced answers and evidence chips, allowing the user to precisely identify the scope of the misunderstanding.
    - **Step B: User Provides Corrective Feedback:** If the AI is wrong, the user provides corrective instructions in natural language (e.g., "Clause 4.5 is not an automatic renewal; it is a right of first refusal. You need to update your understanding.").
    - **Step C: AI Proposes a Correction Plan:** The AI analyzes the user's feedback and generates a detailed, explicit plan of action for the user's approval. This plan must state how it will update its understanding from a semantic perspective and list the specific database changes it will make (e.g., "I will update the node for Clause 4.5 to change its 'type' attribute from 'auto_renewal' to 'right_of_first_refusal' and re-calculate the associated vector embedding.").
    - **Step D: User Approves or Iterates:** The user reviews the plan. They can either **[ Apply ]** the changes, which executes the plan and corrects the AI's knowledge base, or continue the conversation to further refine the AI's understanding until the proposed plan is 100% correct.