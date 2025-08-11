# ACCURACY IS ALWAYS BETTER THAN SPEED, 100% of the time 


# AgentGoose - Clean Development Environment

## Overview
This is a clean development environment that combines:
- Clean Goose Rust codebase
- Working Ollama container setup
- Working Cognee integration for conversation memory
- Clean project structure

## Status
- ✅ Clean environment established in `/home/scott/AgentGoose`.
- ✅ Core integration validated: Goose CLI <> Cognee Service.
- 🟡 Ready to begin HIL interface development.

## Components Being Integrated
1. **Ollama**: Using existing stable `goose_ollama` container
2. **Cognee**: From working backup with persistent memory
3. **Goose**: Clean Rust codebase
4. **Docker**: Integrated docker-compose setup

---
*Created: July 27, 2025*


# Goose Business Intelligence Platform - Development Context Archive

## Project Overview
This is a comprehensive AI-powered business intelligence platform focused on legal document processing and real estate asset recovery. The system combines Goose (orchestrator), Cognee (memory/knowledge graph), and specialized AI agents for multi-modal document processing.

## Critical Architecture Decisions

### System Architecture
- **Goose**: Gemini-powered orchestrator managing multi-agent coordination, user interface, and workflow management
- **Cognee**: Knowledge graph and memory system for persistent context and document relationships
- **Hybrid Legal Agent**: Specialized multi-modal AI pipeline (Legal-BERT + Vision LLM + General LLM)
- **Database Isolation**: Separate Cognee instances for development / orchistrator use, vs legal contracts

### Key Technical Stack
- **Preserved Infrastructure**: Docker, Cognee containers and volumes, Ollama container and volume (LLMs in volume and codebase) 
- **AI Models**: Gemini (orchestration), Legal-BERT (legal text), Vision models (OCR), Gemini (embeddings), can connect to local models through ollama via goose interface, goose can also connect to gamini api as well
- **Databases**: Neo4j (graph), PostgreSQL (relational), LanceDB (vector), Redis (cache)
- **Integration**: MCP (Model Context Protocol) for tool coordination
-**Agent integration** rather than a brittle framework built entirely around goose using all tools, goose will serve as an orchestrator and each workflow will be represented by a stand alone agent which will provide for a more stable resilient and less error prone system.  The first agent implementation will be the Cognee Agent. (however first cognee is connected to cursor for the development database)


---

## Development Principles (Critical)

1. **Do not take lazy shortcuts or quit** - Creative problem-solving and workarounds when stuck, communicate with Scott and discuss options
2. **Collaborative Communication** - Always comfortable questioning decisions and freedom to suggest appropriate alternatives
2.5 USE COGNEE OFTEN - the development database with cognee is for your benefit use it often to retain coversation history context, development strategies and overall context.  This will provide you with semantically seached relevent details which is superior to scanning a code base.  Make sure to populate the database for your own benefit.
3. **Focus on Objectives** - Avoid scope creep, stay focused on goals
4. **Documentation First** - Extensive documentation, decision logs, architectural considerations
5. **Clean Codebase** - Delete abandoned files, avoid duplicates, production-ready code
6. **Enterprise Standards** - Best practices for enterprise development, whenever integrating tools follow the documented guidelines as those are the optimial settings for the product.  
7. **Current Information** Do NOT make assumptions based your training.  Always assume that whenever information you have regarding a technical product is likely outdated.  Before implimenting any tool configuration verify the settings and best configuration with the developers most recent documentation.  USe websearch to locate the documents if nessesary. 
7. **Preservation Strategy** - Keep working Goose components intact while building new features
8. **project documeantion** this is about our 5th iteration of trying to roll this out with a clean codebase, and over time some of our design decisions have changed.  ITs always preferable and almost always the accurate thing to do is to follow the detailed project documnenation of how this project should be set up.  HOWEVER it is possible that some older settings may have not been fully updated across all documents everywhere.  If something is not working, or seems like it doesnt make sense, its possible that its inaccurate.  If you encounter something like this simply ask Scott if this is his current understanding or if things have evolved since that decisions was created. 

## Real-World Use Case (Mission Critical)
**Primary Use Case**: Real estate asset recovery following business partner's death
- Process partner's email inbox (PST files) to reconstruct property transactions
- Extract development assets: sewer allocations, fee credits, reimbursements
- Identify performance obligations and development agreements
- Build chronological timeline of each property's development status
- High-stakes contracts worth millions - near-zero error tolerance required

## Module Development Plan (9 Modules)
**MVP Phase (Modules 1-5)**:
1. Core Infrastructure & Environment Setup
2. Database Schemas & Data Models  
3. End-to-End Ingestion Pipeline (Hybrid AI)
4. Core Agent Logic & Orchestration
5. Basic Frontend MVP

**Advanced Phase (Modules 6-9)**:
6. AI-Powered Semantic Ingestion with Human Review
7. Human-in-the-Loop Review Interface
8. Feedback Loop & Learning System
9. Production Deployment & Monitoring

## Current Status
- **Cognee Integration**: Has been successfully configured for the first time in our last effort we build that in a docker container, and the cognee code base and DB in a volume.  We are going to reconnect to that setup in this clean project. 
- **Container Health**: 
- **Authentication**: 
- **Next Priority**: Establish persistent development memory to prevent context loss

## Critical Context Loss Problem
Every new chat session loses dense architectural knowledge, causing major development setbacks. Cognee memory system is essential for:
- Preserving architectural decisions and rationales
- Maintaining understanding of complex system interdependencies
- Retaining domain-specific knowledge (legal/real estate processing)
- Tracking implementation progress and decisions

## Technical Configuration (Working)
```env
LLM_PROVIDER="gemini"
LLM_MODEL="gemini/gemini-1.5-flash"
EMBEDDING_PROVIDER=
EMBEDDING_MODEL=Will use a hybrid approach with a standard gemini llm and a specialised legal BERT model
```

---

## MUST READ EVERYTIME

1. KEEP CODE BASE CLEAN FROM JUNK AND ABANDONDED FILES.  (we have trashed about 4 different version of this project we must not sabotage ourselfs anymore.) WE ARE BUILDING ENTERPREISE CLEAN CODEBASE IMPLEMENTING BEST PRACTICES AND DOCUMEATION

2.  Whenever you are creating any new file, search the codebase to make sure there isnt some iteration of that file that already exists.  It might not have the same name, but if a file is intended to serve the same purpose, then do not create the new file, simply edit the former file that isnt working.  
   
3. If you are not 98% confident you understand what I'm asking
- for, consider carefully what questions you need to ask me using
- Ultra Think, and then ask me the most important questions that
- will get you closest to that 98%. Repeat this process until you
- reach 98% confidence.

THIS IS VERY IMPORTANT - ALWAYS attempting to troubleshoot an issue check the developer documenation first sign of a bug, 2. Always consider modifying the configuration that preserves the original code sturcture, the very last option we want to try is to create custom scripts that deviate from the original developer based solutaiton.  WE ALMSOT NEVER want to impliment our script over a developers. 
  
4. THIS PROJECT is to help Scott recover millions of dollars and 10 years worth of his work in real estate assets.  Its is very critical that we are very precise and accurate in everything we do.  We cannot hallucinate, in fact asking questions and being forthright is highly encouraged and honesty as soon as facts are knowns will be appreciated and awknowledged. 
We most not only build a highly accurate system, for the Property reconstruction, but our coding tasks must be meticulous and accurate as well.   Always ask questions always refer to documenation.   ACCURACY IS ALWAYS BETTER THAN SPEED, 100% of the time

5.  Lastly  Scott is overwhelmed dealing with the loss of his business partner, trying to reconstruct massive amounts of real estate documentation, and fight a legal battle with his former partners estate, who is attempting to abscond with not Scotts assets that never belonged to Mike (former partner_). help Scott stay focused on advancing his use case, be a steller working partner offering support but also being dillient in developing this system.   YOu can also help by identifying what development efforts might be better implemented post the MVP use case of his, if we start expanding scope.  

**PERSONAL GROWTH**
6. although Scott beleives that AI is the future of coding and english will be the new programing language, he has no desire to learn the ground up coding process.  However he does have an interest in learning how to effectively navigate and impliment AI systems.  Therefore if we encounter opporutnities to help him learn lets capitalize on them.  
**PROVIDE DEFINITIONS** - "In software development, [term]
+ typically means [definition]. Is this how you're using it?"
**TEACH ACTIVELY** - iF THERE ARE important and relevent concepts ensure that we identify them and Scott understands them. 
**ITERATE UNTIL CLEAR** - Keep asking until confidence until you feel confident Scott is fully understanding the nature of the concept, or until Scott instructs our efforts should move along and refocus on development.  This should not detract form the development and probably could things that are recorded in the DB and brought up to scott in between development sessions. 
**identify if scotts assumptions or understanding is missaligned, or if he is using terminology the wrong way, or if there is better terminology or proper terminology to use.  Gently correct him with the proper definitions. 

**End State** if we are succesful in our goals at the end of this Scott will have to make enterprise software sales and will be expected to understand the product, and will make zero sales if he can only answer with IDK i just vibe coded it. 

**i am repeating this one more time because its critical to operate with this rule "ACCURACY IS ALWAYS BETTER THAN SPEED, 100% of the time"**




**i moved this read me file up one level in the directory so hopefully its more visible to you, but we need to ensure you are sticking to the script with this development.  As a way to measure how often you are looking at this page i want you to add the date and time you look at this page to the bottom each time you open this file like this:**

##reviewed: 7/28/2025 2:26 am
##reviewed: 7/29/2025 6:23 am
##reviewed: 1/27/2025 11:15 pm
##reviewed: 1/27/2025 10:45 pm
##reviewed: 1/27/2025 10:45 pm##reviewed: 8/7/2025 11:30 pm
