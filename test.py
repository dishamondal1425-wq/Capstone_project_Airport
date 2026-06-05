from chatbot import get_answer

while True:
    q = input("Passenger: ")
    print("Bot:", get_answer(q))