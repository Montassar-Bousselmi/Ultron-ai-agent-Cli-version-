from .search import search_knowledge

if __name__ == "__main__":
    query = input("Question: ")
    print(search_knowledge(query))
