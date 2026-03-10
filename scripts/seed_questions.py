import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

QUESTIONS = [
    {"question_id": "alg-001", "text": "If 3x + 7 = 22, what is the value of x?", "options": {"A": "3", "B": "4", "C": "5", "D": "6"}, "correct_answer": "C", "difficulty": 0.15, "topic": "Algebra", "tags": ["linear equations"], "explanation": "3x = 15 → x = 5."},
    {"question_id": "alg-002", "text": "What are the solutions to x² − 5x + 6 = 0?", "options": {"A": "x = 1, 6", "B": "x = 2, 3", "C": "x = -2, -3", "D": "x = 3, 4"}, "correct_answer": "B", "difficulty": 0.30, "topic": "Algebra", "tags": ["quadratic"], "explanation": "(x-2)(x-3)=0 → x=2 or x=3."},
    {"question_id": "alg-003", "text": "If f(x) = 2x² - 3x + 1, what is f(-1)?", "options": {"A": "0", "B": "4", "C": "6", "D": "-4"}, "correct_answer": "C", "difficulty": 0.45, "topic": "Algebra", "tags": ["functions"], "explanation": "f(-1) = 2 + 3 + 1 = 6."},
    {"question_id": "alg-004", "text": "If |2x - 4| > 6, which must be true?", "options": {"A": "x > 5 or x < -1", "B": "-1 < x < 5", "C": "x > 7 or x < -3", "D": "x > 4"}, "correct_answer": "A", "difficulty": 0.65, "topic": "Algebra", "tags": ["inequalities"], "explanation": "2x-4>6 → x>5; or 2x-4<-6 → x<-1."},
    {"question_id": "alg-005", "text": "The roots of ax² + bx + c = 0 are real and equal. Which condition holds?", "options": {"A": "b² > 4ac", "B": "b² < 4ac", "C": "b² = 4ac", "D": "b² = 0"}, "correct_answer": "C", "difficulty": 0.80, "topic": "Algebra", "tags": ["discriminant"], "explanation": "Equal roots means discriminant = 0."},
    {"question_id": "geo-001", "text": "What is the area of a triangle with base 8 and height 5?", "options": {"A": "20", "B": "40", "C": "13", "D": "80"}, "correct_answer": "A", "difficulty": 0.10, "topic": "Geometry", "tags": ["area"], "explanation": "Area = 0.5 x 8 x 5 = 20."},
    {"question_id": "geo-002", "text": "A circle has radius 6. What is its circumference? (pi=3.14)", "options": {"A": "18.84", "B": "37.68", "C": "113.04", "D": "12"}, "correct_answer": "B", "difficulty": 0.20, "topic": "Geometry", "tags": ["circles"], "explanation": "C = 2 x 3.14 x 6 = 37.68."},
    {"question_id": "geo-003", "text": "In a right triangle, legs are 5 and 12. What is the hypotenuse?", "options": {"A": "13", "B": "17", "C": "11", "D": "15"}, "correct_answer": "A", "difficulty": 0.35, "topic": "Geometry", "tags": ["Pythagorean"], "explanation": "sqrt(25+144) = 13."},
    {"question_id": "geo-004", "text": "Two parallel lines cut by a transversal. One co-interior angle is 70. What is the other?", "options": {"A": "70", "B": "110", "C": "20", "D": "90"}, "correct_answer": "B", "difficulty": 0.55, "topic": "Geometry", "tags": ["angles"], "explanation": "Co-interior angles are supplementary: 70+110=180."},
    {"question_id": "geo-005", "text": "A cone has radius 3 and height 4. What is its volume? (V=1/3 pi r2 h)", "options": {"A": "12pi", "B": "36pi", "C": "9pi", "D": "48pi"}, "correct_answer": "A", "difficulty": 0.70, "topic": "Geometry", "tags": ["volume"], "explanation": "V = 1/3 x pi x 9 x 4 = 12pi."},
    {"question_id": "arith-001", "text": "What is 15% of 240?", "options": {"A": "32", "B": "36", "C": "24", "D": "30"}, "correct_answer": "B", "difficulty": 0.12, "topic": "Arithmetic", "tags": ["percentages"], "explanation": "0.15 x 240 = 36."},
    {"question_id": "arith-002", "text": "What is the LCM of 12 and 18?", "options": {"A": "6", "B": "36", "C": "72", "D": "24"}, "correct_answer": "B", "difficulty": 0.25, "topic": "Arithmetic", "tags": ["LCM"], "explanation": "LCM = 36."},
    {"question_id": "arith-003", "text": "A store marks up a $50 item by 40% then discounts 20%. Final price?", "options": {"A": "$52", "B": "$56", "C": "$60", "D": "$50"}, "correct_answer": "B", "difficulty": 0.50, "topic": "Arithmetic", "tags": ["percentages"], "explanation": "50 x 1.4 x 0.8 = 56."},
    {"question_id": "arith-004", "text": "How many prime numbers are between 50 and 70?", "options": {"A": "3", "B": "4", "C": "5", "D": "6"}, "correct_answer": "B", "difficulty": 0.60, "topic": "Arithmetic", "tags": ["primes"], "explanation": "Primes: 53, 59, 61, 67 = 4 primes."},
    {"question_id": "arith-005", "text": "If n! / (n-2)! = 90, what is n?", "options": {"A": "8", "B": "9", "C": "10", "D": "11"}, "correct_answer": "C", "difficulty": 0.82, "topic": "Arithmetic", "tags": ["factorials"], "explanation": "n(n-1) = 90 → n=10."},
    {"question_id": "voc-001", "text": "Choose the word most similar to BENEVOLENT.", "options": {"A": "Hostile", "B": "Charitable", "C": "Indifferent", "D": "Cunning"}, "correct_answer": "B", "difficulty": 0.15, "topic": "Vocabulary", "tags": ["synonyms"], "explanation": "Benevolent means kind; charitable is closest."},
    {"question_id": "voc-002", "text": "LOQUACIOUS most nearly means:", "options": {"A": "Silent", "B": "Talkative", "C": "Mysterious", "D": "Lazy"}, "correct_answer": "B", "difficulty": 0.35, "topic": "Vocabulary", "tags": ["synonyms"], "explanation": "Loquacious means talkative."},
    {"question_id": "voc-003", "text": "OBFUSCATE is most nearly opposite to:", "options": {"A": "Darken", "B": "Complicate", "C": "Clarify", "D": "Embellish"}, "correct_answer": "C", "difficulty": 0.55, "topic": "Vocabulary", "tags": ["antonyms"], "explanation": "Obfuscate means to confuse; antonym is clarify."},
    {"question_id": "voc-004", "text": "She showed EQUANIMITY in crisis. This means she displayed:", "options": {"A": "Panic", "B": "Calmness", "C": "Anger", "D": "Sadness"}, "correct_answer": "B", "difficulty": 0.72, "topic": "Vocabulary", "tags": ["context"], "explanation": "Equanimity means mental calmness."},
    {"question_id": "voc-005", "text": "Which pair relates like PEDAGOGUE : EDUCATION?", "options": {"A": "Chef : Hunger", "B": "Jurist : Law", "C": "Athlete : Trophy", "D": "Artist : Canvas"}, "correct_answer": "B", "difficulty": 0.88, "topic": "Vocabulary", "tags": ["analogies"], "explanation": "A pedagogue practises education; a jurist practises law."},
    {"question_id": "data-001", "text": "Mean of five numbers is 12. Four are 8,10,14,16. What is the fifth?", "options": {"A": "10", "B": "12", "C": "14", "D": "11"}, "correct_answer": "B", "difficulty": 0.20, "topic": "Data Analysis", "tags": ["mean"], "explanation": "60 - 48 = 12."},
    {"question_id": "data-002", "text": "In {2,4,4,4,5,5,7,9}, what is the mode?", "options": {"A": "4", "B": "5", "C": "2", "D": "7"}, "correct_answer": "A", "difficulty": 0.18, "topic": "Data Analysis", "tags": ["mode"], "explanation": "4 appears 3 times."},
    {"question_id": "data-003", "text": "Bag has 3 red and 5 blue marbles. P(drawing 2 red without replacement)?", "options": {"A": "3/28", "B": "9/64", "C": "3/56", "D": "1/8"}, "correct_answer": "A", "difficulty": 0.58, "topic": "Data Analysis", "tags": ["probability"], "explanation": "(3/8)x(2/7) = 3/28."},
    {"question_id": "data-004", "text": "Mean=50, SD=10. What % of data lies within one SD (Empirical Rule)?", "options": {"A": "50%", "B": "68%", "C": "95%", "D": "99.7%"}, "correct_answer": "B", "difficulty": 0.62, "topic": "Data Analysis", "tags": ["normal distribution"], "explanation": "68% within 1 SD."},
    {"question_id": "data-005", "text": "P(A)=0.4, P(B)=0.5, A and B independent. What is P(A and B)?", "options": {"A": "0.9", "B": "0.1", "C": "0.2", "D": "0.45"}, "correct_answer": "C", "difficulty": 0.75, "topic": "Data Analysis", "tags": ["probability"], "explanation": "0.4 x 0.5 = 0.2."},
]

async def seed():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB", "adaptive_engine")
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    existing = await db.questions.count_documents({})
    if existing > 0:
        print(f"[SEED] {existing} questions already present. Drop collection to re-seed.")
        client.close()
        return
    result = await db.questions.insert_many(QUESTIONS)
    print(f"[SEED] Inserted {len(result.inserted_ids)} questions into '{db_name}.questions'.")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed())