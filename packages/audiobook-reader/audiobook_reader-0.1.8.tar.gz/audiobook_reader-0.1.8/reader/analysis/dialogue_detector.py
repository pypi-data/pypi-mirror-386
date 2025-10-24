"""Dialogue detection and context analysis for Phase 3."""
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TextSegment:
    """Represents a segment of text with context information."""
    text: str
    is_dialogue: bool
    speaker: Optional[str] = None
    emotion_context: str = "neutral"
    narrative_type: str = "description"  # description, action, internal_thought


class DialogueDetector:
    """Detects dialogue and analyzes text context using pattern matching."""
    
    # Enhanced dialogue patterns
    DIALOGUE_PATTERNS = [
        # Standard quotes
        r'"([^"]*)"',
        r"'([^']*)'",
        # Curly quotes
        r'"([^"]*)"',
        r"'([^']*)'",
        # Em dash dialogue (common in some books)
        r'—([^—\n]*?)(?=—|\n|$)',
        # Dialogue with attribution
        r'(?:said|asked|replied|whispered|shouted|exclaimed)[^.]*?["\']([^"\']*)["\']',
    ]
    
    # Context keywords for narrative classification
    CONTEXT_KEYWORDS = {
        'action': ['ran', 'walked', 'moved', 'grabbed', 'took', 'opened', 'closed', 'turned'],
        'internal_thought': ['thought', 'wondered', 'realized', 'remembered', 'considered', 'felt'],
        'description': ['was', 'were', 'had', 'looked', 'appeared', 'seemed', 'beautiful', 'dark'],
        'emotion': ['angry', 'happy', 'sad', 'excited', 'nervous', 'calm', 'frustrated', 'joyful']
    }
    
    # Speaker attribution patterns
    SPEAKER_PATTERNS = [
        r'(\w+)\s+(?:said|asked|replied|whispered|shouted|exclaimed)',
        r'(?:said|asked|replied|whispered|shouted|exclaimed)\s+(\w+)',
        r'"[^"]*",?\s*(\w+)\s+(?:said|asked|replied)',
        r'(\w+):\s*"',  # Name: "dialogue"
    ]
    
    def __init__(self):
        """Initialize the dialogue detector."""
        self.compiled_dialogue_patterns = [re.compile(pattern, re.IGNORECASE) 
                                         for pattern in self.DIALOGUE_PATTERNS]
        self.compiled_speaker_patterns = [re.compile(pattern, re.IGNORECASE) 
                                        for pattern in self.SPEAKER_PATTERNS]
    
    def analyze_text(self, text: str) -> List[TextSegment]:
        """
        Analyze text and segment into dialogue and narrative parts.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of TextSegment objects with context information
        """
        segments = []
        
        # Split text into sentences/paragraphs for analysis
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            # Check if paragraph contains dialogue
            dialogue_matches = self._find_dialogue(paragraph)
            
            if dialogue_matches:
                # Process paragraph with dialogue
                segments.extend(self._process_dialogue_paragraph(paragraph, dialogue_matches))
            else:
                # Pure narrative paragraph
                segment = TextSegment(
                    text=paragraph.strip(),
                    is_dialogue=False,
                    narrative_type=self._classify_narrative(paragraph),
                    emotion_context=self._detect_emotion_context(paragraph)
                )
                segments.append(segment)
        
        return segments
    
    def _find_dialogue(self, text: str) -> List[Tuple[str, int, int]]:
        """Find all dialogue matches in text with their positions."""
        matches = []
        
        for pattern in self.compiled_dialogue_patterns:
            for match in pattern.finditer(text):
                matches.append((match.group(1), match.start(), match.end()))
        
        # Sort by position and remove overlaps
        matches.sort(key=lambda x: x[1])
        filtered_matches = []
        
        for match in matches:
            # Only add if it doesn't overlap with existing matches
            if not any(match[1] < existing[2] and match[2] > existing[1] 
                      for existing in filtered_matches):
                filtered_matches.append(match)
        
        return filtered_matches
    
    def _process_dialogue_paragraph(self, paragraph: str, dialogue_matches: List[Tuple[str, int, int]]) -> List[TextSegment]:
        """Process a paragraph that contains dialogue."""
        segments = []
        last_end = 0
        
        for dialogue_text, start, end in dialogue_matches:
            # Add narrative text before dialogue
            if start > last_end:
                narrative_text = paragraph[last_end:start].strip()
                if narrative_text:
                    segments.append(TextSegment(
                        text=narrative_text,
                        is_dialogue=False,
                        narrative_type=self._classify_narrative(narrative_text),
                        emotion_context=self._detect_emotion_context(narrative_text)
                    ))
            
            # Add dialogue segment
            speaker = self._extract_speaker(paragraph, start, end)
            segments.append(TextSegment(
                text=dialogue_text.strip(),
                is_dialogue=True,
                speaker=speaker,
                emotion_context=self._detect_emotion_context(dialogue_text)
            ))
            
            last_end = end
        
        # Add remaining narrative text
        if last_end < len(paragraph):
            remaining_text = paragraph[last_end:].strip()
            if remaining_text:
                segments.append(TextSegment(
                    text=remaining_text,
                    is_dialogue=False,
                    narrative_type=self._classify_narrative(remaining_text),
                    emotion_context=self._detect_emotion_context(remaining_text)
                ))
        
        return segments
    
    def _extract_speaker(self, paragraph: str, dialogue_start: int, dialogue_end: int) -> Optional[str]:
        """Extract speaker name from dialogue attribution."""
        # Look for speaker patterns around the dialogue
        context_before = paragraph[max(0, dialogue_start - 100):dialogue_start]
        context_after = paragraph[dialogue_end:min(len(paragraph), dialogue_end + 100)]
        
        for pattern in self.compiled_speaker_patterns:
            # Check before dialogue
            match = pattern.search(context_before)
            if match:
                return match.group(1).capitalize()
            
            # Check after dialogue
            match = pattern.search(context_after)
            if match:
                return match.group(1).capitalize()
        
        return None
    
    def _classify_narrative(self, text: str) -> str:
        """Classify narrative text type based on keywords."""
        text_lower = text.lower()
        
        # Count keyword matches for each category
        category_scores = {}
        for category, keywords in self.CONTEXT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return "description"
        
        # Return category with highest score
        return max(category_scores, key=category_scores.get)
    
    def _detect_emotion_context(self, text: str) -> str:
        """Detect emotional context from text."""
        text_lower = text.lower()
        
        # Emotion indicators
        emotion_patterns = {
            'anger': ['angry', 'furious', 'rage', 'mad', 'annoyed', 'irritated'],
            'joy': ['happy', 'joyful', 'excited', 'delighted', 'cheerful', 'glad'],
            'sadness': ['sad', 'sorrowful', 'depressed', 'melancholy', 'grief', 'mourning'],
            'fear': ['afraid', 'scared', 'terrified', 'anxious', 'worried', 'nervous'],
            'surprise': ['surprised', 'shocked', 'astonished', 'amazed', 'stunned'],
            'disgust': ['disgusted', 'revolted', 'repulsed', 'sick', 'nauseated']
        }
        
        # Punctuation indicators
        if '!' in text:
            if any(word in text_lower for word in ['no', 'stop', 'dont', "don't"]):
                return 'anger'
            else:
                return 'excitement'
        elif '?' in text:
            return 'curiosity'
        elif '...' in text:
            return 'hesitation'
        
        # Check emotion keywords
        for emotion, keywords in emotion_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        
        return 'neutral'
    
    def get_dialogue_ratio(self, segments: List[TextSegment]) -> float:
        """Calculate the ratio of dialogue to total text."""
        total_chars = sum(len(segment.text) for segment in segments)
        dialogue_chars = sum(len(segment.text) for segment in segments if segment.is_dialogue)
        
        return dialogue_chars / total_chars if total_chars > 0 else 0.0
    
    def get_speaker_list(self, segments: List[TextSegment]) -> List[str]:
        """Get list of unique speakers found in the text."""
        speakers = set()
        for segment in segments:
            if segment.is_dialogue and segment.speaker:
                speakers.add(segment.speaker)
        return sorted(list(speakers))
    
    def get_statistics(self, segments: List[TextSegment]) -> Dict[str, Any]:
        """Get detailed statistics about the analyzed text."""
        total_segments = len(segments)
        dialogue_segments = sum(1 for s in segments if s.is_dialogue)
        narrative_segments = total_segments - dialogue_segments
        
        # Narrative type breakdown
        narrative_types = {}
        for segment in segments:
            if not segment.is_dialogue:
                narrative_types[segment.narrative_type] = narrative_types.get(segment.narrative_type, 0) + 1
        
        # Emotion context breakdown
        emotions = {}
        for segment in segments:
            emotions[segment.emotion_context] = emotions.get(segment.emotion_context, 0) + 1
        
        return {
            'total_segments': total_segments,
            'dialogue_segments': dialogue_segments,
            'narrative_segments': narrative_segments,
            'dialogue_ratio': self.get_dialogue_ratio(segments),
            'unique_speakers': len(self.get_speaker_list(segments)),
            'speakers': self.get_speaker_list(segments),
            'narrative_types': narrative_types,
            'emotion_contexts': emotions
        }