"""Level 2: chatbot can advise but cannot read recruitment datasets."""


def llm_chatbot(user_input: str) -> str:
    text = user_input.casefold()
    if "jobid" in text or "userid" in text or "cham diem" in text:
        return "Toi khong co tool truy cap JobID/UserID nen khong the xac nhan ket qua."
    return "Hay trinh bay kinh nghiem, ky nang lien quan va thanh tuu cu the trong CV."


if __name__ == "__main__":
    print(llm_chatbot("Danh gia UserID 976112 cho JobID 0"))
