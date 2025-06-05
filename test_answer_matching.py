#!/usr/bin/env python3
"""
Test script to verify improved answer matching for Jeopardy games.
"""

import re
import sys
import os

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestAnswerMatcher:
    """Test version of the answer matching logic."""
    
    def normalize_answer(self, answer: str) -> str:
        """
        Normalize an answer for comparison.
        Removes common prefixes, punctuation, parentheses content, and converts to lowercase.
        """
        # Remove "What is", "Who is", etc.
        answer = re.sub(r'^(what|who|where|when|why|how)\s+(is|are|was|were)\s+', '', answer.lower())
        
        # Remove content in parentheses (optional parts)
        answer = re.sub(r'\([^)]*\)', '', answer)
        
        # Remove articles at the beginning
        answer = re.sub(r'^(a|an|the)\s+', '', answer)
        
        # Remove common geographical descriptors and prefixes
        answer = re.sub(r'\b(peninsula|island|city|state|country|province|territory)\b', '', answer)
        
        # Normalize hyphens, dashes, and spaces
        answer = re.sub(r'[-–—]', ' ', answer)
        
        # Remove punctuation but preserve spaces
        answer = re.sub(r'[^\w\s]', '', answer)
        
        # Normalize multiple spaces to single space
        answer = re.sub(r'\s+', ' ', answer).strip()
        
        return answer
    
    def check_answer(self, user_answer: str, correct_answer: str) -> bool:
        """
        Check if the user's answer matches the correct answer.
        Uses flexible matching to account for variations, geographical descriptions,
        parenthetical content, and hyphenation differences.
        """
        user_normalized = self.normalize_answer(user_answer)
        correct_normalized = self.normalize_answer(correct_answer)
        
        print(f"  User normalized: '{user_normalized}'")
        print(f"  Correct normalized: '{correct_normalized}'")
        
        # Exact match after normalization
        if user_normalized == correct_normalized:
            return True
        
        # Split into words for more flexible matching
        correct_words = correct_normalized.split()
        user_words = user_normalized.split()
        
        # Special case: if user gives a single word that's contained in the correct answer
        # This handles cases like "wellington" for "wellington new zealand"
        if len(user_words) == 1 and len(correct_words) > 1:
            user_word = user_words[0]
            if len(user_word) >= 4:  # Must be a significant word
                for correct_word in correct_words:
                    if len(correct_word) >= 4 and (user_word == correct_word or 
                                                  user_word in correct_word or 
                                                  correct_word in user_word):
                        print(f"  Single word match: '{user_word}' found in correct answer")
                        return True
        
        # Special case: if correct answer has a single key word that user provides
        # This handles cases like "lincoln" for "abraham lincoln"
        if len(correct_words) > 1 and len(user_words) >= 1:
            # Find the most significant word in the correct answer (usually the last name or main term)
            significant_correct_words = [word for word in correct_words if len(word) >= 4]
            user_significant_words = [word for word in user_words if len(word) >= 3]
            
            # If user provides any significant word that matches
            for user_word in user_significant_words:
                for correct_word in significant_correct_words:
                    if user_word == correct_word or user_word in correct_word or correct_word in user_word:
                        # Additional check: make sure it's not a common word
                        common_words = ['with', 'from', 'that', 'this', 'they', 'have', 'been', 'were', 
                                      'answer', 'question', 'word', 'name', 'place', 'thing', 'person']
                        if correct_word not in common_words:
                            print(f"  Key word match: '{user_word}' matches '{correct_word}'")
                            return True
        
        # Handle single word answers with substring matching
        if len(correct_words) == 1 and len(user_words) == 1:
            correct_word = correct_words[0]
            user_word = user_words[0]
            # Check if they contain each other (handles partial matches)
            if correct_word in user_word or user_word in correct_word:
                return True
        
        # For multi-word answers, use flexible word matching
        if len(correct_words) > 1 and len(user_words) > 1:
            # Count how many significant words match
            matches = 0
            common_words = ['answer', 'question', 'word', 'name', 'place', 'thing', 'person']
            
            for correct_word in correct_words:
                # Skip very short words and common words
                if len(correct_word) < 3 or correct_word in common_words:
                    continue
                    
                # Check if this word appears in user answer (exact or partial)
                word_found = False
                for user_word in user_words:
                    if len(user_word) < 3:
                        continue
                    # Exact match or one contains the other
                    if correct_word == user_word or correct_word in user_word or user_word in correct_word:
                        word_found = True
                        break
                
                if word_found:
                    matches += 1
            
            # Need at least 60% of significant words to match, and at least one significant word
            significant_words = sum(1 for word in correct_words if len(word) >= 3 and word not in common_words)
            if significant_words > 0 and matches > 0:
                match_ratio = matches / significant_words
                print(f"  Match ratio: {match_ratio:.2f} (need 0.6, significant words: {significant_words})")
                return match_ratio >= 0.6
        
        # Fallback: check if user answer contains most of the correct answer
        # This handles cases where word order might be different
        if len(correct_normalized) > 0 and len(user_normalized) > 0:
            # Special case: if correct answer is much shorter due to normalization,
            # check if the correct answer is fully contained in user answer
            if len(correct_normalized) < len(user_normalized) * 0.5:
                # Check if correct answer is a substring of user answer
                if correct_normalized in user_normalized:
                    print(f"  Substring match: '{correct_normalized}' found in '{user_normalized}'")
                    return True
            
            # More sophisticated similarity check - both directions
            correct_in_user = sum(1 for char in correct_normalized if char in user_normalized)
            user_in_correct = sum(1 for char in user_normalized if char in correct_normalized)
            
            # Calculate bidirectional similarity
            forward_sim = correct_in_user / len(correct_normalized)
            backward_sim = user_in_correct / len(user_normalized)
            
            # Only match if both directions show high similarity and answers are reasonably similar in length
            length_ratio = min(len(user_normalized), len(correct_normalized)) / max(len(user_normalized), len(correct_normalized))
            
            print(f"  Character similarity: forward={forward_sim:.2f}, backward={backward_sim:.2f}, length_ratio={length_ratio:.2f}")
            print(f"  Required: forward>=0.9, backward>=0.9, length_ratio>=0.7")
            
            return forward_sim >= 0.9 and backward_sim >= 0.9 and length_ratio >= 0.7
        
        return False

def test_examples():
    """Test the examples provided by the user."""
    matcher = TestAnswerMatcher()
    
    test_cases = [
        # (user_answer, correct_answer, should_match)
        ("Lin Manuel Miranda", "Lin-Manuel Miranda", True),
        ("wellington", "Wellington, New Zealand", True),
        ("baja california", "the Baja Peninsula", True),
        ("what is lincoln", "Abraham Lincoln", True),
        ("who is shakespeare", "William Shakespeare (playwright)", True),
        ("paris", "Paris, France", True),
        ("new york", "New York City", True),
        ("mount everest", "Mount Everest (highest peak)", True),
        ("wrong answer", "Correct Answer", False),
        ("completely different", "Something Else", False),
    ]
    
    print("Testing improved answer matching:")
    print("=" * 50)
    
    passed = 0
    total = len(test_cases)
    
    for user_answer, correct_answer, expected in test_cases:
        print(f"\nTest: '{user_answer}' vs '{correct_answer}'")
        print(f"Expected: {'MATCH' if expected else 'NO MATCH'}")
        
        result = matcher.check_answer(user_answer, correct_answer)
        actual = "MATCH" if result else "NO MATCH"
        status = "✓ PASS" if result == expected else "✗ FAIL"
        
        print(f"Actual: {actual}")
        print(f"Status: {status}")
        
        if result == expected:
            passed += 1
    
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Answer matching is working correctly.")
    else:
        print(f"{total - passed} tests failed. Review the logic.")

if __name__ == "__main__":
    test_examples()