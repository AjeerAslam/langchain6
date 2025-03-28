import google.generativeai as genai

# Set your API key
genai.configure(api_key="AIzaSyDmogzh4LYZ5nrOjsyHZ_3BCe9p_8lA2d0")

# List available models
models = genai.list_models()

# Print model names
for model in models:
    print(model.name)
    
