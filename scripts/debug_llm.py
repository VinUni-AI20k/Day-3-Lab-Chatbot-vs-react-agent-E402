import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from providers import get_llm_provider

provider = get_llm_provider()
print(f"Provider: {provider.__class__.__name__}")
print(f"Model: {provider.model_name}")
print(provider.generate("Say hello"))
