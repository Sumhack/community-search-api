"""
Fuzzy Matching Layer for Entity Normalization
Handles abbreviations for institutes + fuzzy matching for all entities
"""

from typing import List, Dict, Optional
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from db_config import get_db_connection, close_db_connection

SIMILARITY_THRESHOLD = 75

# ============================================================================
# ABBREVIATION MAPPINGS (Only for Institutes)
# ============================================================================

INSTITUTE_ABBREVIATIONS = {
    # IITs (Indian Institute of Technology)
    "iit b": "Indian Institute of Technology, Bombay",
    "iit bombay": "Indian Institute of Technology, Bombay",
    "iit d": "Indian Institute of Technology, Delhi",
    "iit delhi": "Indian Institute of Technology, Delhi",
    "iit k": "Indian Institute of Technology, Kharagpur",
    "iit kharagpur": "Indian Institute of Technology, Kharagpur",
    "iit m": "Indian Institute of Technology, Madras",
    "iit madras": "Indian Institute of Technology, Madras",
    "iit g": "Indian Institute of Technology, Guwahati",
    "iit guwahati": "Indian Institute of Technology, Guwahati",
    "iit r": "Indian Institute of Technology, Roorkee",
    "iit roorkee": "Indian Institute of Technology, Roorkee",
    "iit kgp": "Indian Institute of Technology, Kharagpur",
    "iit kanpur": "Indian Institute of Technology, Kanpur",
    "iit bhu": "Indian Institute of Technology, Varanasi",
    
    # IIMs (Indian Institute of Management)
    "iim a": "Indian Institute of Management, Ahmedabad",
    "iim ahmedabad": "Indian Institute of Management, Ahmedabad",
    "iim b": "Indian Institute of Management, Bangalore",
    "iim bangalore": "Indian Institute of Management, Bangalore",
    "iim c": "Indian Institute of Management, Calcutta",
    "iim calcutta": "Indian Institute of Management, Calcutta",
    "iim l": "Indian Institute of Management, Lucknow",
    "iim lucknow": "Indian Institute of Management, Lucknow",
    
    # International Universities
    "mit": "Massachusetts Institute of Technology",
    "stanford": "Stanford University",
    "harvard": "Harvard University",
    "oxford": "University of Oxford",
    "cambridge": "University of Cambridge",
    "berkeley": "University of California, Berkeley",
    "caltech": "California Institute of Technology",
    
    # Other Popular Institutes
    "bits": "Birla Institute of Technology and Science",
    "bits pilani": "Birla Institute of Technology and Science, Pilani",
    "iiit": "International Institute of Information Technology",
    "nit": "National Institute of Technology",
}

# ============================================================================
# ENTITY EXTRACTOR (Regex-based)
# ============================================================================

class EntityExtractor:
    """Extract entities from query using regex patterns"""
    
    def __init__(self):
        pass
    
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract entities from query by searching for keywords
        Returns dict with extracted entity values
        """
        
        entities = {
            "companies": [],
            "roles": [],
            "cities": [],
            "states": [],
            "countries": [],
            "institutes": [],
            "degrees": [],
            "domains": [],
            "years": []
        }
        
        query_lower = query.lower()
        
        # Get all unique values from DB for matching
        db_context = self._get_db_context()
        
        # Extract companies
        for company in db_context.get("companies", []):
            if company and company.lower() in query_lower:
                entities["companies"].append(company)
        
        # Extract roles
        for role in db_context.get("roles", []):
            if role and role.lower() in query_lower:
                entities["roles"].append(role)
        
        # Extract cities
        for city in db_context.get("cities", []):
            if city and city.lower() in query_lower:
                entities["cities"].append(city)
        
        # Extract states
        for state in db_context.get("states", []):
            if state and state.lower() in query_lower:
                entities["states"].append(state)
        
        # Extract countries
        for country in db_context.get("countries", []):
            if country and country.lower() in query_lower:
                entities["countries"].append(country)
        
        # Extract institutes (both abbreviations and DB values)
        for abbrev in INSTITUTE_ABBREVIATIONS.keys():
            if abbrev in query_lower:
                entities["institutes"].append(abbrev)
        
        for institute in db_context.get("institutes", []):
            if institute and institute.lower() in query_lower:
                entities["institutes"].append(institute)
        
        # Extract degrees
        for degree in db_context.get("degrees", []):
            if degree and degree.lower() in query_lower:
                entities["degrees"].append(degree)
        
        # Extract domains
        for domain in db_context.get("domains", []):
            if domain and domain.lower() in query_lower:
                entities["domains"].append(domain)
        
        # Extract years
        import re
        year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', query)
        entities["years"] = [int(y) for y in year_matches]
        
        # Remove duplicates
        for key in entities:
            if isinstance(entities[key], list) and key != "years":
                entities[key] = list(set(entities[key]))
        
        return entities
    
    def _get_db_context(self) -> Dict[str, List[str]]:
        """Get all unique values from database"""
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            context = {}
            
            # Get all unique companies
            cursor.execute("SELECT DISTINCT company FROM experiences WHERE company IS NOT NULL")
            context["companies"] = [row[0] for row in cursor.fetchall()]
            
            # Get all unique roles
            cursor.execute("SELECT DISTINCT role FROM experiences WHERE role IS NOT NULL")
            context["roles"] = [row[0] for row in cursor.fetchall()]
            
            # Get all unique cities
            cursor.execute("SELECT DISTINCT city FROM experiences WHERE city IS NOT NULL")
            context["cities"] = [row[0] for row in cursor.fetchall()]
            
            # Get all unique states
            cursor.execute("SELECT DISTINCT state FROM experiences WHERE state IS NOT NULL")
            context["states"] = [row[0] for row in cursor.fetchall()]
            
            # Get all unique countries
            cursor.execute("SELECT DISTINCT country FROM experiences WHERE country IS NOT NULL")
            context["countries"] = [row[0] for row in cursor.fetchall()]
            
            # Get all unique institutes
            cursor.execute("SELECT DISTINCT institute FROM education WHERE institute IS NOT NULL")
            context["institutes"] = [row[0] for row in cursor.fetchall()]
            
            # Get all unique degrees
            cursor.execute("SELECT DISTINCT degree FROM education WHERE degree IS NOT NULL")
            context["degrees"] = [row[0] for row in cursor.fetchall()]
            
            # Get all unique domains
            cursor.execute("SELECT DISTINCT domain_name FROM domains WHERE domain_name IS NOT NULL")
            context["domains"] = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            close_db_connection(conn)
            return context
        
        except Exception as e:
            print(f"⚠️  Error getting DB context: {str(e)}")
            return {}

# ============================================================================
# FUZZY MATCHER
# ============================================================================

class FuzzyMatcher:
    """Normalize entities using fuzzy matching and abbreviations"""
    
    def __init__(self, threshold: int = SIMILARITY_THRESHOLD):
        self.threshold = threshold
        self.extractor = EntityExtractor()
    
    def match_entity(self, user_input: str, db_values: List[str]) -> List[str]:
        """
        Fuzzy match user input against database values
        Returns list of matched values above threshold
        """
        
        if not user_input or not db_values:
            return []
        
        # Filter out None/empty values
        db_values = [v for v in db_values if v]
        
        if not db_values:
            return []
        
        # Use token_set_ratio for partial matching
        matches = process.extract(
            user_input.lower(),
            [v.lower() for v in db_values],
            scorer=fuzz.token_set_ratio,
            limit=10
        )
        
        # Map back to original casing
        db_values_lower = {v.lower(): v for v in db_values}
        matched_values = []
        
        for match, score in matches:
            if score >= self.threshold:
                original = db_values_lower.get(match.lower(), match)
                matched_values.append(original)
        
        return list(set(matched_values))  # Remove duplicates
    
    def normalize_institutes(self, institute_inputs: List[str]) -> Dict[str, List[str]]:
        """
        Normalize institutes using abbreviations OR fuzzy matching (not both)
        Abbreviations take priority over fuzzy matching
        Returns: {"IIT B": ["Indian Institute of Technology, Bombay"], ...}
        """
        
        db_institutes = self.extractor._get_db_context().get("institutes", [])
        result = {}
        
        for institute in institute_inputs:
            institute_lower = institute.lower()
            matches = []
            
            # Phase 1: Check abbreviation mapping FIRST
            if institute_lower in INSTITUTE_ABBREVIATIONS:
                # If abbreviation found, ONLY return the mapped value
                mapped_value = INSTITUTE_ABBREVIATIONS[institute_lower]
                matches = [mapped_value]
            else:
                # Phase 2: If NOT an abbreviation, then fuzzy match against DB
                fuzzy_matches = self.match_entity(institute, db_institutes)
                if fuzzy_matches:
                    # Include original value first, then fuzzy matches
                    matches = [institute] + fuzzy_matches
            
            # Store results
            if matches:
                result[institute] = list(set(matches))  # Remove duplicates
        
        return result
    
    def normalize_companies(self, company_inputs: List[str]) -> Dict[str, List[str]]:
        """Normalize companies using fuzzy matching against DB"""
        
        db_companies = self.extractor._get_db_context().get("companies", [])
        result = {}
        
        for company in company_inputs:
            fuzzy_matches = self.match_entity(company, db_companies)
            if fuzzy_matches:
                # Include original value first
                result[company] = [company] + fuzzy_matches
        
        return result
    
    def normalize_roles(self, role_inputs: List[str]) -> Dict[str, List[str]]:
        """Normalize roles using fuzzy matching against DB"""
        
        db_roles = self.extractor._get_db_context().get("roles", [])
        result = {}
        
        for role in role_inputs:
            fuzzy_matches = self.match_entity(role, db_roles)
            if fuzzy_matches:
                # Include original value first
                result[role] = [role] + fuzzy_matches
        
        return result
    
    def normalize_cities(self, city_inputs: List[str]) -> Dict[str, List[str]]:
        """Normalize cities using fuzzy matching against DB"""
        
        db_cities = self.extractor._get_db_context().get("cities", [])
        result = {}
        
        for city in city_inputs:
            fuzzy_matches = self.match_entity(city, db_cities)
            if fuzzy_matches:
                # Include original value first
                result[city] = [city] + fuzzy_matches
        
        return result
    
    def normalize_states(self, state_inputs: List[str]) -> Dict[str, List[str]]:
        """Normalize states using fuzzy matching against DB"""
        
        db_states = self.extractor._get_db_context().get("states", [])
        result = {}
        
        for state in state_inputs:
            fuzzy_matches = self.match_entity(state, db_states)
            if fuzzy_matches:
                # Include original value first
                result[state] = [state] + fuzzy_matches
        
        return result
    
    def normalize_countries(self, country_inputs: List[str]) -> Dict[str, List[str]]:
        """Normalize countries using fuzzy matching against DB"""
        
        db_countries = self.extractor._get_db_context().get("countries", [])
        result = {}
        
        for country in country_inputs:
            fuzzy_matches = self.match_entity(country, db_countries)
            if fuzzy_matches:
                # Include original value first
                result[country] = [country] + fuzzy_matches
        
        return result
    
    def normalize_domains(self, domain_inputs: List[str]) -> Dict[str, List[str]]:
        """Normalize domains using fuzzy matching against DB"""
        
        db_domains = self.extractor._get_db_context().get("domains", [])
        result = {}
        
        for domain in domain_inputs:
            fuzzy_matches = self.match_entity(domain, db_domains)
            if fuzzy_matches:
                # Include original value first
                result[domain] = [domain] + fuzzy_matches
        
        return result
    
    def normalize_degrees(self, degree_inputs: List[str]) -> Dict[str, List[str]]:
        """Normalize degrees using fuzzy matching against DB"""
        
        db_degrees = self.extractor._get_db_context().get("degrees", [])
        result = {}
        
        for degree in degree_inputs:
            fuzzy_matches = self.match_entity(degree, db_degrees)
            if fuzzy_matches:
                # Include original value first
                result[degree] = [degree] + fuzzy_matches
        
        return result
    
    def normalize_all(self, extracted_entities: Dict[str, List[str]]) -> Dict[str, Dict[str, List[str]]]:
        """Normalize all extracted entities"""
        
        normalized = {}
        
        if extracted_entities.get("companies"):
            normalized["companies"] = self.normalize_companies(extracted_entities["companies"])
        
        if extracted_entities.get("roles"):
            normalized["roles"] = self.normalize_roles(extracted_entities["roles"])
        
        if extracted_entities.get("cities"):
            normalized["cities"] = self.normalize_cities(extracted_entities["cities"])
        
        if extracted_entities.get("states"):
            normalized["states"] = self.normalize_states(extracted_entities["states"])
        
        if extracted_entities.get("countries"):
            normalized["countries"] = self.normalize_countries(extracted_entities["countries"])
        
        if extracted_entities.get("institutes"):
            normalized["institutes"] = self.normalize_institutes(extracted_entities["institutes"])
        
        if extracted_entities.get("degrees"):
            normalized["degrees"] = self.normalize_degrees(extracted_entities["degrees"])
        
        if extracted_entities.get("domains"):
            normalized["domains"] = self.normalize_domains(extracted_entities["domains"])
        
        if extracted_entities.get("years"):
            normalized["years"] = {str(year): [str(year)] for year in extracted_entities["years"]}
        
        return normalized

# ============================================================================
# QUERY NORMALIZER (Orchestrator)
# ============================================================================

class QueryNormalizer:
    """Normalize user query by extracting and normalizing entities"""
    
    def __init__(self, threshold: int = SIMILARITY_THRESHOLD):
        self.extractor = EntityExtractor()
        self.matcher = FuzzyMatcher(threshold)
    
    def normalize_query(self, user_query: str) -> Dict:
        """
        Normalize a user query
        Returns dict with original query, extracted entities, and normalized entities
        """
        
        # Step 1: Extract entities
        extracted = self.extractor.extract_entities(user_query)
        
        # Step 2: Normalize entities
        normalized = self.matcher.normalize_all(extracted)
        
        # Step 3: Build hints
        hints = self._build_hints(extracted, normalized)
        
        return {
            "original_query": user_query,
            "extracted_entities": extracted,
            "normalized_entities": normalized,
            "normalization_hints": hints
        }
    
    def _build_hints(self, extracted: Dict, normalized: Dict) -> str:
        """Build human-readable hints about normalization"""
        
        hints = []
        
        entity_types = ["companies", "roles", "cities", "states", "countries", 
                       "institutes", "degrees", "domains"]
        
        for entity_type in entity_types:
            if entity_type in normalized and normalized[entity_type]:
                for original, matches in normalized[entity_type].items():
                    hint = f"{entity_type.title()}: {original} → {', '.join(matches)}"
                    hints.append(hint)
        
        return " | ".join(hints) if hints else "No entities found"

# ============================================================================
# TESTING
# ============================================================================

def main():
    """Test fuzzy matching"""
    
    print("\n" + "="*70)
    print("FUZZY MATCHING WITH ABBREVIATIONS - TEST")
    print("="*70)
    
    normalizer = QueryNormalizer()
    
    test_queries = [
        "Who worked at Stripe in Bangalore?",
        "Who studied at IIT B?",
        "Who studied at IIT D?",
        "Who is a founder?",
        "Who works on AI?",
        "Who studied at MIT?",
        "Who worked at Amazon and studied at IIM A?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = normalizer.normalize_query(query)
        
        print(f"Extracted: {result['extracted_entities']}")
        print(f"Normalized: {result['normalized_entities']}")
        print(f"Hints: {result['normalization_hints']}")
        print("-" * 70)

if __name__ == "__main__":
    main()