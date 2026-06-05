flights = [
    {
        "flight": "AI202",
        "destination": "Delhi",
        "gate": "A12",
        "departure": "10:30 AM",
        "status": "On Time"
    }
]

def get_answer(question):

    question = question.lower()

    for flight in flights:

        if flight["flight"].lower() in question:

            if "gate" in question:
                return f"Flight {flight['flight']} departs from Gate {flight['gate']}."

            elif "departure" in question or "time" in question:
                return f"Flight {flight['flight']} departs at {flight['departure']}."

            elif "status" in question or "delay" in question:
                return f"Flight {flight['flight']} status is {flight['status']}."

    return "Sorry, I couldn't find that information."