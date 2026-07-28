"""Level 1: fixed if/else rules for recruitment advice."""


def rule_based_bot(user_input: str) -> str:
    text = user_input.casefold()
    if "cv" in text:
        return "Hay viet ro ky nang, kinh nghiem va thanh tuu lien quan."
    if "phong van" in text:
        return "Hay tim hieu cong ty va chuan bi vi du kinh nghiem cu the."
    return "Toi chi xu ly duoc cac tu khoa CV va phong van."


if __name__ == "__main__":
    print(rule_based_bot("Toi can viet CV"))
