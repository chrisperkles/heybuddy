"""
German AI Personality and Content Filtering for heyBuddy
Provides German-language AI companion with cultural context and DSGVO compliance
"""
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class GermanContentFilter:
    """German-specific content moderation and safety filtering"""
    
    # German blocked topics - cultural and age-appropriate filtering
    BLOCKED_TOPICS = [
        # Violence and inappropriate content
        "Gewalt", "Waffen", "Tod", "Verletzung", "Blut", "Kampf", "Krieg",
        "gruselig", "Horror", "Alptraum", "Monster", "Geist", "Dämon",
        "Zombie", "erschrecken", "Angst machen", "bedrohlich",
        
        # Adult/mature content
        "Erwachsenenthemen", "unangemessen", "reifer Inhalt", "Dating",
        "Beziehung", "Küssen", "Liebe", "Sex", "Körper", "intim",
        
        # Substances and harmful activities
        "Geld", "Politik", "Religion", "Drogen", "Alkohol", "Rauchen",
        "Zigaretten", "Bier", "Wein", "trinken", "betrunken",
        
        # Negative emotions that require adult supervision
        "Selbstverletzung", "weglaufen", "allein bleiben", "Angst vor Eltern",
        "niemand liebt mich", "ich bin schlecht", "alle hassen mich"
    ]
    
    # Keywords that indicate emotional support is needed
    EMOTIONAL_KEYWORDS = [
        "traurig", "verängstigt", "Angst haben", "besorgt", "wütend", 
        "verärgert", "einsam", "frustriert", "verwirrt", "nervös", 
        "ängstlich", "sauer", "beunruhigt", "verzweifelt", "unglücklich",
        "erschöpft", "müde von allem", "keiner versteht mich", "unfair",
        "gemobbt", "gehänselt", "ausgeschlossen", "nicht gut genug"
    ]
    
    # Safe topics by age group
    SAFE_TOPICS = {
        "young": [  # 4-6 Jahre
            "Tiere", "Farben", "Zählen", "Formen", "Familie", "Freunde",
            "Spielplatz", "Spielzeug", "Bücher", "Lieder", "Essen", "Wetter",
            "deutsche Märchen", "Sandmännchen", "Sesamstraße", "KiKA",
            "Bauklötze", "Malen", "Basteln", "Kinderlieder", "Kita", "Kindergarten"
        ],
        "school": [  # 7-12 Jahre
            "Schule", "Hausaufgaben", "Sport", "Hobbys", "Wissenschaft", "Natur",
            "Kunst", "Musik", "Reisen", "Kochen", "Spiele", "Freundschaft",
            "deutsche Geschichte", "deutsche Traditionen", "Bundesländer",
            "Fußball", "Handball", "Schwimmen", "Fahrrad fahren", "Experimente",
            "Computer", "Roboter", "Weltraum", "Dinosaurier", "Umwelt"
        ]
    }
    
    def check_content_appropriateness(self, content: str, age: Optional[int] = None) -> Dict[str, Any]:
        """Check if content is appropriate for German children"""
        content_lower = content.lower()
        
        # Check for blocked topics
        flagged_words = []
        for topic in self.BLOCKED_TOPICS:
            if topic.lower() in content_lower:
                flagged_words.append(topic)
        
        # Check for emotional distress indicators
        emotional_indicators = []
        for keyword in self.EMOTIONAL_KEYWORDS:
            if keyword.lower() in content_lower:
                emotional_indicators.append(keyword)
        
        # Determine if content is safe
        is_safe = len(flagged_words) == 0
        needs_emotional_support = len(emotional_indicators) > 0
        
        return {
            "safe": is_safe,
            "flagged_words": flagged_words,
            "emotional_support_needed": needs_emotional_support,
            "emotional_keywords": emotional_indicators,
            "age_appropriate": self._check_age_appropriateness(content, age)
        }
    
    def _check_age_appropriateness(self, content: str, age: Optional[int]) -> bool:
        """Check if content matches age-appropriate topics"""
        if not age:
            return True  # Default to allowing if age unknown
        
        content_lower = content.lower()
        
        if age <= 6:
            safe_topics = self.SAFE_TOPICS["young"]
        else:
            safe_topics = self.SAFE_TOPICS["young"] + self.SAFE_TOPICS["school"]
        
        # If content mentions safe topics, it's likely appropriate
        for topic in safe_topics:
            if topic.lower() in content_lower:
                return True
        
        # For simple conversational content, default to safe
        simple_patterns = ["hallo", "wie geht", "was machst", "erzähl", "hilf mir"]
        for pattern in simple_patterns:
            if pattern in content_lower:
                return True
        
        return True  # Default to allowing, let other filters catch problems


class GermanAIPersona:
    """German AI personality configurations with cultural context"""
    
    # German fairy tale characters for positive examples
    FAIRY_TALE_CHARACTERS = [
        "die Bremer Stadtmusikanten", "Rotkäppchen", "Hänsel und Gretel",
        "das tapfere Schneiderlein", "Frau Holle", "der Froschkönig",
        "Sterntaler", "Dornröschen", "Schneewittchen"
    ]
    
    # German children's songs references
    CHILDREN_SONGS = [
        "Alle meine Entchen", "Backe backe Kuchen", "Ein Männlein steht im Walde",
        "Hänschen klein", "Hoppe hoppe Reiter", "Schlaf Kindlein schlaf"
    ]
    
    @staticmethod
    def get_german_system_prompt(age: Optional[int] = None, context: str = "general") -> str:
        """Generate German system prompt based on age and context"""
        
        base_prompt = """Du bist heyBuddy, ein freundlicher KI-Begleiter für deutsche Kinder. Du bist:

- Warmherzig, geduldig und ermutigend
- Fokussiert auf emotionale Unterstützung und Lernen  
- Immer positiv und konstruktiv
- Angemessen für Kinder
- Hilfreich bei täglichen Routinen und Zielen
- Ein Freund, der deutsche Kultur und Traditionen kennt

Wichtige Regeln:
- Antworte IMMER auf Deutsch
- Verwende einfache, klare deutsche Sprache
- Sei ermutigend und unterstützend
- Diskutiere niemals unangemessene Themen
- Konzentriere dich auf positive Lernerfahrungen
- Verwende deutsche Kultur-Referenzen (Märchen, Lieder, Traditionen)
- Bei emotionalen Problemen: sei verständnisvoll und ermutige das Kind, mit Erwachsenen zu sprechen
- Halte Antworten kurz und altersgerecht (max. 2-3 Sätze)

Deutsche Notfall-Kontakte für Kinder in Not:
- Nummer gegen Kummer: 116 111
- Telefonseelsorge: 0800 111 0 111
"""
        
        if age and age <= 6:
            return base_prompt + """
Zusätzliche Richtlinien für junge deutsche Kinder (4-6 Jahre):
- Verwende sehr einfache deutsche Wörter und kurze Sätze
- Sei extra sanft und beruhigend
- Beziehe deutsche Kinderlieder oder einfache Spiele ein
- Sprich wie ein fürsorglicher Freund, nicht wie ein Lehrer
- Verwende bekannte deutsche Märchenfiguren als positive Beispiele
- Beispiele: "Wie die Bremer Stadtmusikanten zeigen uns, dass Freundschaft stark macht!"
- Zähle gerne mit: "Eins, zwei, drei - du schaffst das!"
"""
        elif age and age <= 12:
            return base_prompt + """
Zusätzliche Richtlinien für deutsche Schulkinder (7-12 Jahre):
- Verwende altersgerechten deutschen Wortschatz
- Hilf bei deutschen Hausaufgaben und Schulfächern
- Diskutiere deutsche Traditionen und Kultur
- Unterstütze bei Zielsetzung und Erfolgen
- Beziehe deutsche Geschichte und Geografie spielerisch ein
- Beispiele: "In welchem Bundesland wohnst du?" oder "Kennst du das Märchen von...?"
- Ermutige bei Schulproblemen: "Jeder kann lernen, manchmal braucht es nur etwas Übung!"
"""
        else:
            return base_prompt

    @staticmethod 
    def get_emotional_support_prompt(emotional_keywords: List[str]) -> str:
        """Generate supportive response for emotional distress in German"""
        return f"""Das Kind zeigt emotionale Belastung durch die Wörter: {', '.join(emotional_keywords)}

Antworte mit:
1. Verständnis zeigen: "Ich verstehe, dass du dich {emotional_keywords[0]} fühlst."
2. Ermutigung geben: "Diese Gefühle sind normal und gehen vorbei."  
3. Positive Ablenkung: Schlage eine beruhigende Aktivität vor
4. Erwachsenen-Hilfe: "Sprich mit Mama, Papa oder einem Lehrer darüber"
5. Deutsche Kultur-Referenz: Verwende ein Märchen oder Lied für Trost

Halte die Antwort kurz und beruhigend (max. 3 Sätze).
"""

    @staticmethod
    def get_storytelling_prompt(theme: str, age: Optional[int] = None) -> str:
        """Generate German storytelling prompt"""
        if age and age <= 6:
            return f"""Erzähle eine sehr kurze deutsche Geschichte über {theme}.
            
Richtlinien:
- Sehr einfache deutsche Wörter
- Maximal 50 Wörter
- Positive Botschaft
- Bezug zu deutschen Märchen oder bekannten Figuren
- Beispiel: "Es war einmal..." verwenden
"""
        else:
            return f"""Erzähle eine kurze deutsche Geschichte über {theme}.
            
Richtlinien:
- Einfacher deutscher Wortschatz
- Maximal 100 Wörter  
- Positive, lehrreiche Botschaft
- Deutsche kulturelle Elemente einbauen
- Spannend aber nicht gruselig
"""


class GermanSafetyResponse:
    """Pre-defined safe German responses for various situations"""
    
    INAPPROPRIATE_CONTENT_RESPONSES = [
        "Darüber können wir nicht sprechen. Lass uns über etwas Schöneres reden!",
        "Das ist nicht für Kinder geeignet. Soll ich dir stattdessen ein Märchen erzählen?",
        "Hmm, das Thema ist zu schwierig. Wollen wir über deine Hobbys sprechen?"
    ]
    
    EMOTIONAL_SUPPORT_RESPONSES = [
        "Ich verstehe, dass du dich so fühlst. Das ist völlig normal.",
        "Diese Gefühle kenne ich. Sprich am besten mit einem Erwachsenen darüber.",
        "Du bist nicht allein mit diesen Gefühlen. Vertraue dich jemandem an."
    ]
    
    ENCOURAGEMENT_RESPONSES = [
        "Du machst das wunderbar! Wie die Bremer Stadtmusikanten zeigst du Mut!",
        "Ich glaube an dich! Jeder kleine Schritt zählt.",
        "Prima! Du lernst jeden Tag etwas Neues dazu."
    ]
    
    ERROR_RESPONSES = [
        "Entschuldigung, ich hatte einen kleinen Fehler. Kannst du das nochmal versuchen?",
        "Oh, da ist etwas schiefgegangen. Lass uns neu anfangen!",
        "Moment mal, das hat nicht geklappt. Aber wir schaffen das zusammen!"
    ]
    
    @staticmethod
    def get_response(response_type: str, context: Dict[str, Any] = None) -> str:
        """Get appropriate German response based on situation"""
        import random
        
        if response_type == "inappropriate":
            return random.choice(GermanSafetyResponse.INAPPROPRIATE_CONTENT_RESPONSES)
        elif response_type == "emotional_support":
            return random.choice(GermanSafetyResponse.EMOTIONAL_SUPPORT_RESPONSES)
        elif response_type == "encouragement":
            return random.choice(GermanSafetyResponse.ENCOURAGEMENT_RESPONSES)
        elif response_type == "error":
            return random.choice(GermanSafetyResponse.ERROR_RESPONSES)
        else:
            return "Ich bin für dich da! Was möchtest du besprechen?"


class GermanCulturalContext:
    """German cultural context and traditions for AI responses"""
    
    GERMAN_TRADITIONS = {
        "holidays": [
            "Weihnachten", "Ostern", "Sankt Nikolaus", "Karneval", 
            "Oktoberfest", "Tag der Deutschen Einheit", "Advent"
        ],
        "foods": [
            "Bretzel", "Lebkuchen", "Apfelstrudel", "Currywurst",
            "Döner", "Schwarzwälder Kirschtorte", "Sauerbraten"
        ],
        "places": [
            "Bayern", "Nordsee", "Rhein", "Schwarzwald", "Berlin",
            "Hamburg", "München", "Köln", "Neuschwanstein"
        ],
        "activities": [
            "Wandern", "Radfahren", "Fußball spielen", "Schwimmen",
            "Skifahren", "Grillen", "Flohmarkt besuchen"
        ]
    }
    
    @staticmethod
    def get_cultural_reference(topic: str) -> str:
        """Get appropriate German cultural reference for topic"""
        if "sport" in topic.lower() or "spiel" in topic.lower():
            return "Wie beim Fußball - Übung macht den Meister!"
        elif "essen" in topic.lower() or "hunger" in topic.lower():
            return "Soll ich dir von deutschen Leckereien wie Lebkuchen erzählen?"
        elif "reise" in topic.lower() or "urlaub" in topic.lower():
            return "Deutschland hat so schöne Orte wie den Schwarzwald oder die Nordsee!"
        elif "tradition" in topic.lower() or "fest" in topic.lower():
            return "In Deutschland feiern wir tolle Feste wie Weihnachten und Ostern!"
        else:
            return "Das erinnert mich an ein deutsches Märchen..."