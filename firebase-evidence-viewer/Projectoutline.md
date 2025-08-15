### Agent Response Protocol

For your system to be reliable, every agent's return should follow a strict protocol.

- **Extraction Agents:** When extracting a name, date, or number, the agent must return the extracted value **along with the page number and a text snippet or bounding box** that shows exactly where that value was found in the original document. .
- **Analysis Agents:** When an agent provides an analysis, such as identifying a risk or a specific obligation, its response must include a **list of source documents** and a **summary of the relevant clauses** that support its conclusion.

### UI Sourcing

The user interface must be designed to display this information clearly. When a user sees an extracted data point, they should be able to click on it and immediately be taken to the exact location in the source document where that information was found. This provides a clear audit trail and builds user trust.

### Phase 1: Core GUI Framework (MVP)

The goal of this phase is to build a minimal GUI that allows a user to interact with a single document.

- **GUI Document Viewer:** Develop a web-based document viewer that can render PDFs and images. This viewer will be the central hub for all HIL interactions.
- **Document-to-Record Linking:** Implement functionality to link a document view directly to a specific record in the database. This allows a user to select a record (e.g., an APN) and see the original document that record was extracted from.
- **OCR Cleanup & HIL Feedback Form:** When a document is flagged for review, the GUI will highlight the low-confidence text section. A side panel will provide a form where the user can:
    - Manually transcribe the unreadable text.
    - Upload a supplemental document (e.g., a clearer scan).
    - Mark the section as "not needed for interpretation" (e.g., boilerplate text).

---

### Phase 2: Advanced HIL and Linking

This phase will build on the core GUI to create a more powerful and intuitive user experience.

- **OCR Highlighting:** The GUI will visually highlight the text that was extracted via OCR. The user will be able to click on a word in the text and see its corresponding location in the original document image. .
- **Inter-document Linking:** This is a key feature for a real estate platform. The GUI will allow users to link related documents directly. For example, a user viewing a "First Amendment" can create a link to the "Original Agreement" with a single click.
- **Graphical Map Interface:** Develop a view that can display a parcel map. Users can click on a specific lot number in the map, and the GUI will display all the legal documents related to that parcel.

---

### Phase 3: Automation and Learning

This final phase automates the HIL process and introduces a feedback loop for the AI agents.

- **Automated Review Queue:** The GUI will present the flagged documents in a clear, prioritized list, allowing a user to process them efficiently.
- **Agent Learning:** The system will use the data from the HIL feedback form to retrain or fine-tune the agents. For example, if a user consistently corrects how a specific type of date is extracted, the `FinancialAnalysisAgent` will learn from that input and improve its accuracy over time.
- **Automated Workflow Triggering:** The system will automatically trigger a new workflow once a document is fully processed by the HIL system. For example, once the OCR cleanup is complete, the document can be sent back to the agent system for final analysis.