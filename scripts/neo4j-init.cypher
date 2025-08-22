// Neo4j Graph Database Schema for Contract Analysis System
// Handles document relationships, amendments, and conflict tracking

// Create constraints for unique identifiers
CREATE CONSTRAINT doc_sha256_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.sha256 IS UNIQUE;
CREATE CONSTRAINT extraction_id_unique IF NOT EXISTS FOR (e:Extraction) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT parcel_id_unique IF NOT EXISTS FOR (p:Parcel) REQUIRE p.parcel_id IS UNIQUE;
CREATE CONSTRAINT party_id_unique IF NOT EXISTS FOR (p:Party) REQUIRE p.party_id IS UNIQUE;

// Create indexes for performance
CREATE INDEX doc_filename IF NOT EXISTS FOR (d:Document) ON (d.filename);
CREATE INDEX doc_type IF NOT EXISTS FOR (d:Document) ON (d.document_type);
CREATE INDEX doc_uploaded IF NOT EXISTS FOR (d:Document) ON (d.uploaded_at);
CREATE INDEX extraction_field IF NOT EXISTS FOR (e:Extraction) ON (e.field_name);
CREATE INDEX party_name IF NOT EXISTS FOR (p:Party) ON (p.name);
CREATE INDEX parcel_number IF NOT EXISTS FOR (p:Parcel) ON (p.parcel_number);

// Node types for document analysis

// Document node - represents each uploaded document
// Properties: sha256, filename, document_type, uploaded_at, version, status
// Example:
// CREATE (d:Document {
//     sha256: 'abc123...',
//     filename: 'purchase_agreement.pdf',
//     document_type: 'purchase_agreement',
//     uploaded_at: datetime(),
//     version: 1,
//     status: 'processed'
// })

// Extraction node - represents extracted data points
// Properties: id, field_name, value, confidence, page, bbox
// Example:
// CREATE (e:Extraction {
//     id: 'uuid-123',
//     field_name: 'purchase_price',
//     value: 500000,
//     confidence: 0.95,
//     page: 3,
//     bbox: [100, 200, 300, 250]
// })

// Party node - represents legal entities
// Properties: party_id, name, role, entity_type
// Example:
// CREATE (p:Party {
//     party_id: 'party-001',
//     name: 'Coyne Development LLC',
//     role: 'buyer',
//     entity_type: 'LLC'
// })

// Parcel node - represents real estate parcels
// Properties: parcel_id, parcel_number, address, legal_description
// Example:
// CREATE (p:Parcel {
//     parcel_id: 'parcel-001',
//     parcel_number: '123-45-678',
//     address: '123 Main St',
//     legal_description: 'Lot 1, Block 2...'
// })

// Amendment node - represents document amendments
// Properties: amendment_number, effective_date
// Example:
// CREATE (a:Amendment {
//     amendment_number: 1,
//     effective_date: date('2024-01-15')
// })

// Relationship types

// Document relationships
// (:Document)-[:AMENDS]->(:Document) - one document amends another
// (:Document)-[:SUPERSEDES]->(:Document) - one document supersedes another
// (:Document)-[:REFERENCES]->(:Document) - one document references another
// (:Document)-[:PARENT_OF]->(:Document) - parent-child document relationship

// Extraction relationships
// (:Document)-[:CONTAINS]->(:Extraction) - document contains extraction
// (:Extraction)-[:DERIVED_FROM]->(:Extraction) - computed values
// (:Extraction)-[:CONFLICTS_WITH]->(:Extraction) - conflicting extractions
// (:Extraction)-[:SUPERSEDED_BY]->(:Extraction) - superseded values

// Party relationships
// (:Document)-[:INVOLVES]->(:Party) - document involves party
// (:Party)-[:REPRESENTS]->(:Party) - representation relationships
// (:Party)-[:AFFILIATED_WITH]->(:Party) - corporate affiliations

// Parcel relationships
// (:Document)-[:ENCUMBERS]->(:Parcel) - document encumbers parcel
// (:Document)-[:TRANSFERS]->(:Parcel) - document transfers parcel
// (:Parcel)-[:ADJACENT_TO]->(:Parcel) - parcel adjacency

// Table relationships
// (:Document)-[:HAS_TABLE]->(:Table) - document contains table
// (:Table)-[:HAS_CELL]->(:TableCell) - table contains cells
// (:TableCell)-[:REFERENCES]->(:Extraction) - cell links to extraction

// Conflict resolution relationships
// (:Conflict)-[:CHOOSES]->(:Extraction) - chosen value in conflict
// (:Conflict)-[:REJECTS]->(:Extraction) - rejected values
// (:Conflict)-[:RESOLVED_BY]->(:Rule) - rule that resolved conflict

// Sample graph pattern for document amendment chain
// MATCH path = (original:Document)-[:AMENDS*]->(final:Document)
// WHERE original.document_type = 'purchase_agreement'
// RETURN path

// Sample query for finding all encumbrances on a parcel
// MATCH (d:Document)-[:ENCUMBERS]->(p:Parcel {parcel_number: '123-45-678'})
// RETURN d.filename, d.document_type, d.uploaded_at
// ORDER BY d.uploaded_at DESC

// Sample query for conflict resolution
// MATCH (c:Conflict)-[:CHOOSES]->(chosen:Extraction),
//       (c)-[:REJECTS]->(rejected:Extraction)
// WHERE chosen.field_name = 'purchase_price'
// RETURN c, chosen, collect(rejected) as rejected_values

// Function to create document lineage
// CALL apoc.create.relationship(predecessor, 'SUPERSEDED_BY', {date: datetime()}, successor)

// Procedure to find document conflicts
// MATCH (d1:Document)-[:CONTAINS]->(e1:Extraction),
//       (d2:Document)-[:CONTAINS]->(e2:Extraction)
// WHERE e1.field_name = e2.field_name 
//   AND e1.value <> e2.value
//   AND d1.sha256 <> d2.sha256
// RETURN e1, e2, d1, d2